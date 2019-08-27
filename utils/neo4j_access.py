from neo4j.v1 import GraphDatabase
import neo4j.v1
import uuid
import os
import time

from utils.models import Publication, Venue, Person
from utils.text_utils import string_util, process_person_names, process_special_character
from utils.operate_utils import is_valid_key, key_2_upper
from utils.data_extraction import parse_bib
from configparser import ConfigParser


cf = ConfigParser()
# cf.read("./neo4j.conf", encoding="utf-8")
cf.read("E:\\projects\\web_pages\\webs/neo4j.conf", encoding="utf-8")

uri = cf.get("neo4j", "uri")
username = cf.get("neo4j", "username")
pwd = cf.get("neo4j", "pwd")


def create_or_match_publications(data_source='bibtex.bib', mode=1, is_list=False):
    """
    从“文件/给定信息”中提取文献信息，建立节点
    :param data_source: 若mode=1，则文件名；若mode=2，则为pub信息list of dict or dict
    :param mode: 1：从文件中读取；2：给定pub的dict信息
    :param is_list: true：有多个文献的list；false：只有一个文献，是dict
    :return: -1:读取/解析文献信息错误；1：处理成功；-2：提取文献信息失败；-3：写入数据库失败（可能全失败或部分失败）
    """
    if mode == 1:
        bib_data = parse_bib(data_source)
        bib_data = bib_data.entries
    else:
        if is_list:
            bib_data = data_source
        else:
            bib_data = [data_source]
    if bib_data is None or bib_data == []:
        print('No valid bibliography in the database')
        return -1
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        flag = 1
        for entry in bib_data:
            node = extract_publication(entry)  # 提取文献信息，构造节点
            if node is None or isinstance(node, int):
                flag = -2
            else:
                tmp = query_or_create_node(session, node)  # 创建/更新节点（更新未实现）
                if tmp is None:
                    flag = -3
    return flag


def create_or_match_venues(data_source, mode=1):
    """
    从“文件或数据结构”中创建/匹配venue节点
    :param data_source: file name or dict/list of dict or venues
    :param mode: 1:file;2:dict or list of dict
    :return: code:-3:位置的mode值；-2:文件不存在；-1:参数类型错误；1：处理成功；-4：提取venue信息封装节点失败；
                -5：写入数据库失败（可能全失败或部分失败）
                data：venue_name和uuid的对应关系,dict
                names: 原始name和处理后name的映射
    """
    # 检查数据有效性
    result = {"code": 0, "data": "", "msg": ""}
    if mode == 1:
        if not os.path.exists(data_source):
            result["code"] = -2
            result["msg"] = "文件不存在"
            return result
    #     todo 读取file
    elif mode == 2:
        if isinstance(data_source, dict):
            data_source = [data_source]
        elif isinstance(data_source, list):
            data_source = data_source
        else:
            result["code"] = -1
            result["msg"] = "参数类型错误"
            return result
    else:
        result["code"] = -3
        result["msg"] = "mode值错误"
        return result
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        flag = 1
        mappings = {}  # name 和uuid的mapping
        name_mappings = {}  # 原始和处理后name的mapping
        for data in data_source:
            node = extract_venue(data)  # 提取venue信息，构造节点
            if data["venue_name"] not in name_mappings.keys():
                name_mappings[data["venue_name"]] = node.venue_name
            if node is None:
                flag = min(-4, flag)
                result["msg"] += "，提取venue信息错误"
            else:
                if node.venue_name not in mappings.keys():
                    tmp = query_or_create_node(session, node)  # 创建/更新节点（更新未实现）
                    if tmp is None:
                        flag = min(-5, flag)
                        result["msg"] += "，写入数据库错误"
                    else:
                        mappings[node.venue_name] = tmp
        result["data"] = mappings
        result["names"] = name_mappings
        result["code"] = flag
        if flag == 1:
            result["msg"] = "创建venue节点成功"
    return result


def create_or_match_persons(data_source, mode=1):
    """
    从“文件或数据结构”中创建/匹配person节点
    :param data_source: file name or dict/list of dict or venues
    :param mode: 1:file;2:dict or list of dict
    :return: code:-3:位置的mode值；-2:文件不存在；-1:参数类型错误；1：处理成功；-4：提取venue信息封装节点失败；
                -5：写入数据库失败（可能全失败或部分失败）
                data：venue_name和uuid的对应关系,dict
                names: 原始name和处理后name的映射
    """
    # 检查数据有效性
    result = {"code": 0, "data": "", "msg": ""}
    if mode == 1:
        if not os.path.exists(data_source):
            result["code"] = -2
            result["msg"] = "文件不存在"
            return result
    #     TODO 读取file
    elif mode == 2:
        if isinstance(data_source, dict):
            data_source = [data_source]
        elif isinstance(data_source, list):
            data_source = data_source
        else:
            result["code"] = -1
            result["msg"] = "参数类型错误"
            return result
    else:
        result["code"] = -3
        result["msg"] = "mode值错误"
        return result
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        flag = 1
        mappings = {}  # name 和uuid的mapping
        name_mappings = {}  # 原始和处理后name的mapping
        for data in data_source:
            node = extract_person(data)  # 提取person信息，构造节点
            if data["full_name"] not in name_mappings.keys():
                name_mappings[data["full_name"]] = node.full_name
            if node is None:
                flag = min(-4, flag)
                result["msg"] += "，提取person信息错误"
            else:
                if node.full_name not in mappings.keys():
                    node.name_ch = node.full_name
                    node.full_name = ""
                    tmp = query_or_create_node(session, node, to_create=False, match_field="name_ch")  # 查询是否有name_ch的节点
                    if tmp is None:
                        node.full_name = node.name_ch
                        node.name_ch = ""
                        tmp = query_or_create_node(session, node, to_create=True, match_field="full_name")  # 查询是否有full_name的节点
                        if tmp is None:
                            flag = min(-5, flag)
                            result["msg"] += "，写入数据库错误"
                        else:
                            mappings[node.full_name] = tmp
                    else:
                        mappings[node.full_name] = tmp

        result["data"] = mappings
        result["names"] = name_mappings
        result["code"] = flag
        if flag == 1:
            result["msg"] = "创建full_name节点成功"
    return result


def build_network_of_venues(source_node_type="Publication", node_type="ARTICLE", publication_field='journal',
                            target_node_type="Venue", rel_type="PUBLISH_IN"):
    """
    从publication中查询article 和conference字段，创建节点，再提取关系
    :param rel_type:
    :param target_node_type:
    :param source_node_type:
    :param node_type:
    :param publication_field:
    :return:code:-6:创建节点时，venue name和uuid关系提取失败；-7:现在只能处理article和conference；-8：未查询到有效的venue name;
                  -9：原始数据、处理后name、uuid对应失败,-10创建关系失败;1:成功
             data:
             msg:
    """
    result = {"code": 0, "msg": "", "data": ""}
    # 查询指定venue_type字段的source_node_type
    cypher = "match (node:{NODE}) where node.node_type='{TYPE}' return node".format(NODE=source_node_type,
                                                                                    TYPE=node_type)
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        nodes = session.run(cypher)
        data = {}  # key: source_node_type的uuid， value：venue的name
        for record in nodes:
            print("提取{NODE}与{NODE2}之间关系过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type)
                  + str(record["node"]['title']))
            if not string_util(record["node"][publication_field]):
                print("{ID} has empty {FIELD} field".format(ID=record["node"]['title'], FIELD=publication_field))
            else:
                data[record["node"]['uuid']] = record["node"][publication_field]
        if data == {}:
            print("提取{NODE}与{NODE2}之间关系过程：未查询到{NODE}.{TYPE}中的节点".format(NODE=source_node_type,
                                                                        TYPE=node_type, NODE2=target_node_type))
            result["code"] = -8
            result["msg"] = "提取{NODE}与{NODE2}之间关系过程：未查询到{NODE}.{TYPE}中的节点".format(NODE=source_node_type,
                                                                                  TYPE=node_type,
                                                                                  NODE2=target_node_type)
            return result
    # 创建Venue节点
    if not (node_type == "ARTICLE" or node_type == "CONFERENCE" or node_type == "INPROCEEDINGS"):
        print("现在不能处理【" + node_type + "】类型的venue")
        result["code"] = -7
        result["msg"] = "现在不能处理【" + node_type + "】类型的venue"
        return result
    venue_info = []
    venue_names = list(set(data.values()))
    for venue in venue_names:
        info = {"venue_name": venue, "venue_type": node_type}
        venue_info.append(info)
    create_result = create_or_match_venues(venue_info, mode=2)
    if create_result["code"] < 0:
        result["code"] = create_result["code"]
        result["msg"] = create_result["msg"] + "\n 停止创建关系"
        return result
    # 提取Venue和Publication关系
    rel_mapping_name_uuid = create_result["data"]  # 这是venue name 和uuid之间的mapping关系
    name_mappings = create_result["names"]
    if rel_mapping_name_uuid is None or not isinstance(rel_mapping_name_uuid, dict) or \
            not isinstance(name_mappings, dict):
        result["code"] = -6
        result["msg"] = create_result["msg"] + "\n 停止创建关系"
        return result
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        for source_id, target_name in data.items():
            processed_name = name_mappings.get(target_name, None)
            if processed_name is None:
                result["code"] = min(-9, result["code"])
                result["msg"] += ",提取处理后venue name失败：" + target_name
                print("提取处理后venue name失败：" + target_name)
                continue
            venue_id = rel_mapping_name_uuid.get(processed_name, None)
            if venue_id is None:
                result["code"] = min(-9, result["code"])
                result["msg"] += ",提取venue的uuid失败： " + processed_name
                print("提取venue的uuid失败： " + processed_name)
                continue
            match_cypher = "MATCH  (pub:" + source_node_type + " {uuid:'" + source_id + "'}) -[:" + rel_type + \
                           "]-> (ven:" + target_node_type + " {uuid:'" + venue_id + "'})  return pub, ven"
            query_result = session.run(match_cypher)
            query_result = query_result.data()
            if len(query_result) > 0:
                print("关系已存在(" + rel_type + "):" + source_id + "->" + venue_id)
                continue
            create_cypher = "MATCH  (pub:" + source_node_type + " {uuid:'" + source_id + "'}) , (ven:" + \
                            target_node_type + " {uuid:'" + venue_id + "'})  CREATE (pub) -[:" + rel_type + \
                            "]-> (ven) return pub, ven"
            query_result = session.run(create_cypher)
            query_result = query_result.data()
            if len(query_result) > 0:
                print("，创建关系成功(" + rel_type + "):" + source_id + "->" + venue_id)
            else:
                result["code"] = min(-10, result["code"])
                result["msg"] += "，创建关系失败(" + rel_type + "):" + source_id + "->" + venue_id
                print("，创建关系失败(" + rel_type + "):" + source_id + "->" + venue_id)
        if result["code"] == 0:
            result["msg"] = "成功"
            result["code"] = 1
    return result


def build_network_of_persons(source_node_type="Publication", publication_field='author', target_node_type="Person",
                             rel_type="WRITE"):
    # 查询所有articles of publication
    result = {"code": 0, "msg": "", "data": ""}
    cypher = "match (node:{NODE}) return node".format(NODE=source_node_type)
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        nodes = session.run(cypher)
        data = {}
        for record in nodes:
            print("提取{NODE}与{NODE2}之间关系过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type)
                  + str(record["node"]['uuid']))
            if not string_util(record["node"][publication_field]):
                print("{ID} has empty {FIELD} field".format(ID=record["node"]['uuid'], FIELD=publication_field))
            else:
                data[record["node"]['uuid']] = record["node"][publication_field]  # value是bib的name，要拆分处理成list of string
        if data is {}:
            print("提取{NODE}与{NODE2}之间关系过程：未查询到{NODE}.{TYPE}中的节点".format(NODE=source_node_type,
                                                                        TYPE=publication_field, NODE2=target_node_type))
            return
    # 处理多个作者的情况
    person_names = []
    for key, names in data.items():
        names = process_person_names([names])  # 这里拆分成了多个，返回值：dict, original authors: list of dict of authors
        for _, separate_names in names.items():
            for separate_name in separate_names:
                person_names.append(separate_name["name"])
        data[key] = names
    # 创建Person节点
    person_info = []  # 组装数据，for 生成person节点
    person_names = list(set(person_names))  # 去重
    for person in person_names:
        info = {"full_name": person}
        person_info.append(info)
    create_result = create_or_match_persons(person_info, mode=2)
    if create_result["code"] < 0:
        result["code"] = create_result["code"]
        result["msg"] = create_result["msg"] + "\n 停止创建关系"
        return result
    # 提取person和Publication关系
    rel_mapping_name_uuid = create_result["data"]  # 这是处理后person name 和uuid之间的mapping关系
    name_mappings = create_result["names"]  # 这是原始和处理后name的mapping
    if rel_mapping_name_uuid is None or not isinstance(rel_mapping_name_uuid, dict):
        result["code"] = -6
        result["msg"] = create_result["msg"] + "\n 停止创建关系"
        return result
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        for source_id, target_names in data.items():  # target_names is a list
            for _, value in target_names.items():
                target_names = value
                break
            for target_name in target_names:
                target_name = target_name["name"]
                processed_name = name_mappings.get(target_name, None)
                if processed_name is None:
                    result["code"] = min(-9, result["code"])
                    result["msg"] += ",提取处理后person name失败：" + target_name
                    print("提取处理后person name失败：" + target_name)
                    continue
                target_id = rel_mapping_name_uuid.get(processed_name, None)
                if target_id is None:
                    result["code"] = min(-9, result["code"])
                    result["msg"] += ",提取person的uuid失败： " + processed_name
                    print("提取person的uuid失败： " + processed_name)
                    continue
                match_cypher = "MATCH  (m:" + source_node_type + " {uuid:'" + source_id + "'}) -[:" + rel_type + \
                               "]-> (n:" + target_node_type + " {uuid:'" + target_id + "'})  return m, n"
                query_result = session.run(match_cypher)
                query_result = query_result.data()
                if len(query_result) > 0:
                    print("关系已存在(PUBLISH_IN):" + source_id + "->" + target_id)
                    continue
                create_cypher = "MATCH  (m:" + source_node_type + " {uuid:'" + source_id + "'}) , (n:" + target_node_type +\
                                " {uuid:'" + target_id + "'}) " " CREATE (n) -[:" + rel_type + "]-> (m) return m, n"
                query_result = session.run(create_cypher)
                query_result = query_result.data()
                if len(query_result) > 0:
                    print("，创建关系成功(" + target_node_type + "):" + source_id + "->" + target_id)
                else:
                    result["code"] = min(-10, result["code"])
                    result["msg"] += "，创建关系失败(" + target_node_type + "):" + source_id + "->" + target_id
                    print("，创建关系失败(" + target_node_type + "):" + source_id + "->" + target_id)
        if result["code"] == 0:
            result["msg"] = "成功"
            result["code"] = 1
    return result


def revise_publications(data):
    """
    从文件中提取文献信息，并建立节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid bibliography in the database')
        return -1
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        node = extract_publication(data)  # 提取文献信息，构造节点
        if node is None or isinstance(node, int):
            return -2
        else:
            tmp = revise_node(session, node, data)  # 创建/更新节点
            if tmp is None:
                return -3
            return 1


def revise_persons(data):
    """
    提取人信息，并修改节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid person info is given')
        return -1
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        node = extract_person(data)  # 提取文献信息，构造节点
        if node is None or isinstance(node, int):
            return -2
        else:
            tmp = revise_node(session, node, data)  # 更新节点
            if tmp is None:
                return -3
            return 1


def revise_venues(data):
    """
    提取人信息，并修改节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid venue info is given')
        return -1
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        node = extract_venue(data)  # 提取文献信息，构造节点
        if node is None or isinstance(node, int):
            return -2
        else:
            tmp = revise_node(session, node, data)  # 更新节点
            if tmp is None:
                return -3
            return 1


def revise_node(tx, node, field_value_revise):
    """
    先查询节点是否存在，若存在，修改内容，否则，创建节点。-1表示出错
    :param tx:
    :param node:
    :param field_value_revise:
    :return:
    """
    if node is None:
        return None
    cypher = node.get_match_cypher()
    nodes = tx.run(cypher)
    nodes = nodes.data()
    if len(nodes) == 0:
        return None
    nodes = nodes[0]
    print("查询到了节点：" + str(nodes["node"]['uuid']) + "开始修改：")
    field_value_match = {"uuid": nodes["node"]['uuid']}
    cypher = node.get_revise_cypher(field_value_revise, field_value_match)
    node_revised = tx.run(cypher)
    node_revised = node_revised.data()
    node_revised = node_revised[0].get("node", None)
    if node_revised is None:
        return None
    node_revised = node_revised.get("uuid", None)
    if node_revised is None:
        return None
    return 1


def extract_publication(entry):
    entry_parsed_keys = key_2_upper(entry)
    entry_type = entry.get(entry_parsed_keys["ENTRYTYPE"], None).upper()

    if entry_type is None:
        print("unrecognized entry (type):" + str(entry))
        return None
    elif entry_type == "ARTICLE":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        journal = is_valid_key(entry_parsed_keys, "journal".upper())
        journal = "" if journal is None else entry.get(journal, None)
        journal = process_special_character(journal)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        pages = is_valid_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if author is None or title is None or journal is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, title=title, journal=journal, year=year,
                           volume=volume, number=number, pages=pages, month=month, note=note)
    elif entry_type == "BOOK":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = is_valid_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = is_valid_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        edition = is_valid_key(entry_parsed_keys, "edition".upper())
        edition = "" if edition is None else entry.get(edition, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if (author is None and editor is None) or title is None or publisher is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, publisher=publisher,
                           year=year,
                           volume=volume, number=number, series=series, address=address, month=month,
                           edition=edition, note=note)
    elif entry_type == "INBOOK":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = is_valid_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        chapter = is_valid_key(entry_parsed_keys, "chapter".upper())
        chapter = "" if chapter is None else entry.get(chapter, None)
        pages = is_valid_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = is_valid_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        book_type = is_valid_key(entry_parsed_keys, "type".upper())
        book_type = "" if book_type is None else entry.get(book_type, None)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        edition = is_valid_key(entry_parsed_keys, "edition".upper())
        edition = "" if edition is None else entry.get(edition, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if (author is None and editor is None) or title is None or (chapter is None and pages is None) or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, journal=None, year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=edition, book_title=None, organization=None,
                           chapter=chapter, school=None, type=book_type, how_published=None, keywords=None, institution=None)
    elif entry_type == "INPROCEEDINGS" or entry_type == "CONFERENCE":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = is_valid_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        book_title = is_valid_key(entry_parsed_keys, "booktitle".upper())
        book_title = "" if book_title is None else entry.get(book_title, None)
        book_title = process_special_character(book_title)
        publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = is_valid_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        pages = is_valid_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        organization = is_valid_key(entry_parsed_keys, "organization".upper())
        organization = "" if organization is None else entry.get(organization, None)
        organization = process_special_character(organization)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if author is None or title is None or book_title is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, journal=None, year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=None, book_title=book_title, organization=organization,
                           chapter=None, school=None, type=None, how_published=None, keywords=None, institution=None)
    elif entry_type == "INCOLLECTION":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = is_valid_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        book_title = is_valid_key(entry_parsed_keys, "booktitle".upper())
        book_title = "" if book_title is None else entry.get(book_title, None)
        book_title = process_special_character(book_title)
        publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = is_valid_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        pages = is_valid_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        edition = is_valid_key(entry_parsed_keys, "edition".upper())
        edition = "" if edition is None else entry.get(edition, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        book_type = is_valid_key(entry_parsed_keys, "type".upper())
        book_type = "" if book_type is None else entry.get(book_type, None)
        chapter = is_valid_key(entry_parsed_keys, "chapter".upper())
        chapter = "" if chapter is None else entry.get(chapter, None)
        chapter = process_special_character(chapter)
        if author is None or title is None or book_title is None or year is None or publisher is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="INCOLLECTION", author=author, editor=editor, title=title, journal=None,
                           year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=edition, book_title=book_title, organization=None,
                           chapter=chapter, school=None, type=book_type, how_published=None, keywords=None, institution=None)
    elif entry_type == "MISC":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        how_published = is_valid_key(entry_parsed_keys, "howpublished".upper())
        how_published = "" if how_published is None else entry.get(how_published, None)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        node = Publication(uuid="", node_type="MISC", author=author, editor=None, title=title, journal=None, year=year,
                           volume=None, number=None, series=None, address=None, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=None, type=None, how_published=how_published, keywords=None, institution=None)
    elif entry_type == "PHDTHESIS":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        school = is_valid_key(entry_parsed_keys, "school".upper())
        school = "" if school is None else entry.get(school, None)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        keywords = is_valid_key(entry_parsed_keys, "keywords".upper())
        keywords = "" if keywords is None else entry.get(keywords, None)
        keywords = process_special_character(keywords)
        if author is None or title is None or school is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="PHDTHESIS", author=author, editor=None, title=title, journal=None, year=year,
                           volume=None, number=None, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=school, type=None, how_published=None, keywords=keywords, institution=None)
    elif entry_type == "MASTERSTHESIS":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        school = is_valid_key(entry_parsed_keys, "school".upper())
        school = "" if school is None else entry.get(school, None)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        type = is_valid_key(entry_parsed_keys, "type".upper())
        type = "" if type is None else entry.get(type, None)
        type = process_special_character(type)
        if author is None or title is None or school is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="MASTERSTHESIS", author=author, editor=None, title=title, journal=None,
                           year=year,
                           volume=None, number=None, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=school, type=type, how_published=None, keywords=None, institution=None)
    elif entry_type == "TECHREPORT":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        institution = is_valid_key(entry_parsed_keys, "institution".upper())
        institution = "" if institution is None else entry.get(institution, None)
        institution = process_special_character(institution)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        report_type = is_valid_key(entry_parsed_keys, "type".upper())
        report_type = "" if report_type is None else entry.get(report_type, None)
        if author is None or title is None or institution is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="TECHREPORT", author=author, editor=None, title=title, journal=None, year=year,
                           volume=None, number=number, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=None, type=report_type, how_published=None, keywords=None,
                           institution=institution)
    else:
        print("unsupported entry (type):" + str(entry))
        return None
    return node


def extract_venue(entry):
    """
    从节点信息中，提取出venue节点
    :param entry:
    :return:
    """
    entry_parsed_keys = key_2_upper(entry)
    # venue name
    venue_name = is_valid_key(entry_parsed_keys, "venue_name".upper())
    venue_name = "" if venue_name is None else entry.get(venue_name, None)
    venue_name = process_special_character(venue_name)  # 包括了转大写、去除空格、转换特殊字符等操作
    # abbr
    abbr = is_valid_key(entry_parsed_keys, "abbr".upper())
    abbr = "" if abbr is None else entry.get(abbr, None)
    abbr = process_special_character(abbr)  # 包括了转大写、去除空格、转换特殊字符等操作
    # venue type
    venue_type = is_valid_key(entry_parsed_keys, "venue_type".upper())
    venue_type = "" if venue_type is None else entry.get(venue_type, None)
    venue_type = process_special_character(venue_type)
    # publisher
    publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
    publisher = "" if publisher is None else entry.get(publisher, None)
    publisher = process_special_character(publisher)
    # address
    address = is_valid_key(entry_parsed_keys, "address".upper())
    address = "" if address is None else entry.get(address, None)
    address = process_special_character(address)
    # sci_index
    sci_index = is_valid_key(entry_parsed_keys, "sci_index".upper())
    sci_index = "" if sci_index is None else entry.get(sci_index, None)
    # ei_index
    ei_index = is_valid_key(entry_parsed_keys, "ei_index".upper())
    ei_index = "" if ei_index is None else entry.get(ei_index, None)
    # ssci_index
    ssci_index = is_valid_key(entry_parsed_keys, "ssci_index".upper())
    ssci_index = "" if ssci_index is None else entry.get(ssci_index, None)
    # start year
    start_year = is_valid_key(entry_parsed_keys, "start_year".upper())
    start_year = "" if start_year is None else entry.get(start_year, None)
    # year
    year = is_valid_key(entry_parsed_keys, "year".upper())
    year = "" if year is None else entry.get(year, None)
    # note
    note = is_valid_key(entry_parsed_keys, "note".upper())
    note = "" if note is None else entry.get(note, None)
    note = process_special_character(note)
    if venue_name is "" or venue_type is "":
        print("No valid node! venue name and venue type are mandatory fields: " + str(entry))
        return None
    node = Venue(uuid="", venue_name=venue_name, abbr=abbr, venue_type=venue_type, publisher=publisher, year=year,
                 address=address, sci_index=sci_index, ei_index=ei_index, ssci_index=ssci_index, note=note,
                 start_year=start_year)
    return node


def extract_person(entry):
    """
    从节点信息中，提取出person节点
    :param entry:
    :return:
    """
    entry_parsed_keys = key_2_upper(entry)
    # full name
    full_name = is_valid_key(entry_parsed_keys, "full_name".upper())
    full_name = "" if full_name is None else entry.get(full_name, None)
    full_name = process_special_character(full_name)  # 包括了转大写、去除空格、转换特殊字符等操作
    # last_name
    last_name = is_valid_key(entry_parsed_keys, "last_name".upper())
    last_name = "" if last_name is None else entry.get(last_name, None)
    last_name = process_special_character(last_name)  # 包括了转大写、去除空格、转换特殊字符等操作
    # middle_name
    middle_name = is_valid_key(entry_parsed_keys, "middle_name".upper())
    middle_name = "" if middle_name is None else entry.get(middle_name, None)
    middle_name = process_special_character(middle_name)
    # first_name
    first_name = is_valid_key(entry_parsed_keys, "first_name".upper())
    first_name = "" if first_name is None else entry.get(first_name, None)
    first_name = process_special_character(first_name)
    # name_ch
    name_ch = is_valid_key(entry_parsed_keys, "name_ch".upper())
    name_ch = "" if name_ch is None else entry.get(name_ch, None)
    name_ch = process_special_character(name_ch)
    # first_name_ch
    first_name_ch = is_valid_key(entry_parsed_keys, "first_name_ch".upper())
    first_name_ch = "" if first_name_ch is None else entry.get(first_name_ch, None)
    first_name_ch = process_special_character(first_name_ch)
    # last_name_ch
    last_name_ch = is_valid_key(entry_parsed_keys, "last_name_ch".upper())
    last_name_ch = "" if last_name_ch is None else entry.get(last_name_ch, None)
    last_name_ch = process_special_character(last_name_ch)
    # research_interest
    research_interest = is_valid_key(entry_parsed_keys, "research_interest".upper())
    research_interest = "" if research_interest is None else entry.get(research_interest, None)
    research_interest = process_special_character(research_interest)
    # institution
    institution = is_valid_key(entry_parsed_keys, "institution".upper())
    institution = "" if institution is None else entry.get(institution, None)
    institution = process_special_character(institution)
    # added_by
    added_by = is_valid_key(entry_parsed_keys, "added_by".upper())
    added_by = "" if added_by is None else entry.get(added_by, None)
    added_by = process_special_character(added_by)
    # added_date
    added_date = is_valid_key(entry_parsed_keys, "added_date".upper())
    added_date = "" if added_date is None else entry.get(added_date, None)
    # note
    note = is_valid_key(entry_parsed_keys, "note".upper())
    note = "" if note is None else entry.get(note, None)
    note = process_special_character(note)
    if full_name is "" and name_ch is "":
        print("No valid node! full name or name_ch is mandatory fields: " + str(entry))
        return None
    node = Person(uuid="", full_name=full_name, first_name=first_name, middle_name=middle_name, last_name=last_name, name_ch=name_ch,
                  first_name_ch=first_name_ch, last_name_ch=last_name_ch, institution=institution, research_interest=research_interest, note=note,
                  added_by=added_by, added_date=added_date)
    return node


def query_or_create_node(tx, node, to_create=True, match_field=None):
    """
    先查询节点是否存在，若存在，直接返回节点id，否则，创建节点并返回id。-1表示出错
    :param tx:
    :param node:
    :param to_create:
    :param match_field:
    :return:
    """
    if node is None:
        return None
    if match_field is None:
        cypher = node.get_match_cypher()
    else:
        cypher = node.get_match_cypher(match_field)
    node_id = tx.run(cypher)
    for record in node_id:
        print("查询到了节点：" + str(record["node"]['uuid']))
        return record["node"]['uuid']
    if to_create:
        node.uuid = uuid.uuid1()
        node.added_date = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        create_cypher = node.get_create_cypher()
        node_id = tx.run(create_cypher)
        for record in node_id:
            print("创建新节点：" + str(record["node"]['uuid']))
            return record["node"]['uuid']
        return None
    return None


def query_or_create_relation(tx, source_type, source_id, target_type, target_id, relation_type, to_create=True):
    """
    先查询关系是否存在，若存在，直接返回关系id，否则，创建关系并返回id。-1表示出错
    :param relation_type:
    :param target_id:
    :param target_type:
    :param source_id:
    :param source_type:
    :param tx:
    :param to_create:
    :return:
    """
    message = {"status": -1, "msg": ""}
    if source_type is None or source_id is None or target_id is None or target_type is None or relation_type is None:
        message["msg"] = "输入参数不完整"
        return None
    if tx is None:
        driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
        tx = driver.session()
    cypher = "MATCH (s:{source}) -[r:{rel}]-> (t:{target}) where s.uuid='{IDs}' and t.uuid='{IDt}'  " \
             "return s, r, t" .format(source=source_type, target=target_type, IDs=source_id,
                                      IDt=target_id, rel=relation_type.upper())
    result = tx.run(cypher)
    result = result.data()
    if len(result) > 0:
        print("查询到了关系：")
        message["status"] = 2
        message["msg"] = "关系已经存在"
        return message
    if to_create:
        cypher = "MATCH (s:{source}), (t:{target}) where s.uuid='{IDs}' and t.uuid='{IDt}' CREATE (s) -[r:{rel}]->(t) " \
             "return s, r, t" .format(source=source_type, target=target_type, IDs=source_id,
                                      IDt=target_id, rel=relation_type.upper())
        result = tx.run(cypher)
        result = result.data()
        if len(result) > 0:
            print("创建新关系：")
            message["status"] = 1
            message["msg"] = "关系已创建"
            return message
        message["status"] = -2
        message["msg"] = "创建关系失败，数据库操作失败"
        return message
    message["status"] = -3
    message["msg"] = "数据库无记录，已选择不创建新节点"
    return message


if __name__ == "__main__":
    # # 从文件中解析文献，并创建节点
    create_or_match_publications('E:/reference.bib')
    # # 从网络中解析文献节点，并提取journal信息，创建venue节点、[wenxian]->[publication]
    build_network_of_venues(node_type="ARTICLE", publication_field="journal")
    build_network_of_venues(node_type="inproceedings".upper(), publication_field="book_title")
    # 从文献中解析author字段，创建Person节点、person->publication
    build_network_of_persons()
