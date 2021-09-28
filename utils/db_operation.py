from neo4j import GraphDatabase
import neo4j
import uuid
import os
import time

from utils.bib_util.utils import extract_publication, extract_venue, extract_person
from utils.nlp.text_utils import string_util
from utils.file_util.utils import parse_bib_file


def ini_result():
    result = {"code": -1, "msg": "", "data": None}
    return result


def create_or_match_publications(driver, data_source, mode=1):
    """
    从“文件/给定信息”中提取文献信息，建立节点
    :param driver:
    :param data_source: 若mode=1，则文件名；若mode=2，则为pub信息list of dict
    :param mode: 1：从文件中读取；2：给定pub的dict信息
    :return:
    """
    result = ini_result()
    if driver is None:
        result["code"] = -500
        result["msg"] = "driver is not given"
        return result

    if mode == 1:
        if not os.path.exists(data_source):
            result["code"] = -504
            result["msg"] = "file does not exist"
            return result
        parse_flag, msg, bib_data = parse_bib_file(data_source)
        bib_data = bib_data.entries
    elif mode == 2:
        if not isinstance(data_source, list):
            result["code"] = -502
            result["msg"] = "data_source should be list when mode is 2"
            return result
    else:
        result["code"] = -501
        result["msg"] = "unknown mode value"
        return result

    if bib_data is None or len(bib_data) == 0:
        result["code"] = -503
        result["msg"] = "No valid bibliography in the database"
        return result

    unparsed_entry = []
    unrecorded_entry = []
    with driver.session() as session:
        for entry in bib_data:
            node = extract_publication(entry)  # 提取文献信息，构造节点
            if node is None or isinstance(node, int):
                unparsed_entry.append(entry)
                continue
            tmp = query_or_create_node(session, node)  # 创建/更新节点（更新未实现）
            if tmp is None:
                unrecorded_entry.append(entry)
    if len(unparsed_entry) == 0 and len(unrecorded_entry) == 0:
        result["code"] = 500
        result["msg"] = "all have been written into database"
    elif len(unparsed_entry) == 0 and len(unrecorded_entry) > 0:
        result["code"] = 501
        result["msg"] = "some entries that are parsed are failed to be written into database"
        result["data"] = {"db_fail": unrecorded_entry}
    elif len(unparsed_entry) > 0 and len(unrecorded_entry) == 0:
        result["code"] = 502
        result["msg"] = "some entries are failed to be parsed"
        result["data"] = {"parse_fail": unparsed_entry}
    else:
        result["code"] = 503
        result["msg"] = "some entries are failed to be parsed and some others that are parsed are failed to be written into database"
        result["data"] = {"parse_fail": unparsed_entry, "db_fail": unrecorded_entry}
    return result


def create_or_match_venues(driver, data_source, mode=1):
    """
    从“文件或数据结构”中创建/匹配venue节点
    :param driver:
    :param data_source: file name or dict/list of dict or venues
    :param mode: 1: file;2: list of dict
    :return: code见汇总
                data：venue_name和uuid的对应关系,dict
                names: 原始name和处理后name的映射
    """
    # 检查数据有效性
    result = ini_result()
    if driver is None:
        result["code"] = -500
        result["msg"] = "driver is not given"
        return result

    if mode == 1:  # todo 读取file还未实现，file格式？
        if not os.path.exists(data_source):
            result["code"] = -504
            result["msg"] = "file does not exist"
            return result
    elif mode == 2:
        if not isinstance(data_source, list):
            result["code"] = -502
            result["msg"] = "data_source should be list when mode is 2"
            return result
    else:
        result["code"] = -501
        result["msg"] = "unknown mode value"
        return result

    mappings = {}  # "name: uuid" 的mapping
    name_mappings = {}  # "原始:处理后" name的mapping
    entry_failed = []
    entry_failed_to_disk = []
    with driver.session() as session:
        for data in data_source:
            node = extract_venue(data)  # 提取venue信息，构造节点

            if node is None:
                entry_failed.append(data)
                continue

            venue_name_ori = data["venue_name"]
            venue_name_processed = node.venue_name
            if venue_name_ori not in name_mappings.keys():
                name_mappings[venue_name_ori] = venue_name_processed

            if venue_name_processed not in mappings.keys():
                tmp_uuid = query_or_create_node(session, node)  # 创建/更新节点（更新未实现）
                if tmp_uuid is None:
                    entry_failed_to_disk.append(data)
                else:
                    mappings[venue_name_processed] = tmp_uuid
    if len(entry_failed) == 0 and len(entry_failed_to_disk) == 0:
        result["code"] = 510
        result["msg"] = "success"
        result["data"] = {"name_uuid_mapping": mappings, "name_old_new_mapping": name_mappings}  # todo 原来分别是data和names字段
    elif len(entry_failed) > 0 and len(entry_failed_to_disk) == 0:
        result["code"] = 511
        result["msg"] = "some entries are failed to be transformed into venues"
        result["data"] = {"parse_fail": entry_failed}
    elif len(entry_failed) == 0 and len(entry_failed_to_disk) > 0:
        result["code"] = 512
        result["msg"] = "some entries that are parsed are failed to be written into database"
        result["data"] = {"db_fail": entry_failed_to_disk}
    else:
        result["code"] = 513
        result["msg"] = "some entries that are parsed are failed to be written into database and some other entries are failed to be transformed into venues"
        result["data"] = {"db_fail": entry_failed_to_disk, "parse_fail": entry_failed}

    return result


def create_or_match_persons(driver, data_source, mode=1):
    """
    从“文件或数据结构”中创建/匹配person节点
    :param driver:
    :param data_source: file name or dict/list of dict or venues
    :param mode: 1:file;2:dict or list of dict
    :return: code:-3:位置的mode值；-2:文件不存在；-1:参数类型错误；1：处理成功；-4：提取venue信息封装节点失败；
                -5：写入数据库失败（可能全失败或部分失败）
                data：venue_name和uuid的对应关系,dict
                names: 原始name和处理后name的映射
    """
    result = ini_result()
    if driver is None:
        result["code"] = -500
        result["msg"] = "driver is not given"
        return result

    if mode == 1:  # todo 读取file还未实现，file格式？
        if not os.path.exists(data_source):
            result["code"] = -504
            result["msg"] = "file does not exist"
            return result
    elif mode == 2:
        if not isinstance(data_source, list):
            result["code"] = -502
            result["msg"] = "data_source should be list when mode is 2"
            return result
    else:
        result["code"] = -501
        result["msg"] = "unknown mode value"
        return result

    mappings = {}  # "name: uuid" 的mapping
    name_mappings = {}  # "原始:处理后" name的mapping
    entry_failed = []
    entry_failed_to_disk = []
    with driver.session() as session:

        for data in data_source:
            node = extract_person(data)  # 提取person信息，构造节点

            if node is None:
                entry_failed.append(data)
                continue

            person_name_ori = data["full_name"]
            person_name_processed = node.full_name

            if person_name_ori not in name_mappings.keys():
                name_mappings[person_name_ori] = person_name_processed

            if person_name_processed not in mappings.keys():
                tmp_uuid = query_or_create_node(session, node, to_create=False, match_field="full_name")  # 查询是否有full_name的节点 todo 或者name_ch，待修改query_or_create_node with multiple match field

                if tmp_uuid is None:
                    entry_failed_to_disk.append(data)
                else:
                    mappings[person_name_processed] = tmp_uuid
                    #
    if len(entry_failed) == 0 and len(entry_failed_to_disk) == 0:
        result["code"] = 510
        result["msg"] = "success"
        result["data"] = {"name_uuid_mapping": mappings,
                          "name_old_new_mapping": name_mappings}  # todo 原来分别是data和names字段
    elif len(entry_failed) > 0 and len(entry_failed_to_disk) == 0:
        result["code"] = 511
        result["msg"] = "some entries are failed to be transformed into venues"
        result["data"] = {"parse_fail": entry_failed}
    elif len(entry_failed) == 0 and len(entry_failed_to_disk) > 0:
        result["code"] = 512
        result["msg"] = "some entries that are parsed are failed to be written into database"
        result["data"] = {"db_fail": entry_failed_to_disk}
    else:
        result["code"] = 513
        result[
            "msg"] = "some entries that are parsed are failed to be written into database and some other entries are failed to be transformed into venues"
        result["data"] = {"db_fail": entry_failed_to_disk, "parse_fail": entry_failed}

    return result


def build_network_of_venues(driver, source_node_type="Publication", node_type="ARTICLE", publication_field='journal',
                            target_node_type="Venue", rel_type="PUBLISH_IN"):
    """
    从publication中查询article 和conference字段，创建节点，再提取关系
    :param driver:
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
    result = ini_result()
    # 查询指定venue_type字段的source_node_type
    cypher = "match (node:{NODE}) where node.node_type='{TYPE}' return node".format(NODE=source_node_type,
                                                                                    TYPE=node_type)
    data = {}  # key: source_node_type的uuid， value：venue的name
    with driver.session() as session:
        nodes = session.run(cypher)

        for record in nodes:
            print("提取{NODE}与{NODE2}之间关系过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type)
                  + str(record["node"]['title']))
            if not string_util(record["node"][publication_field]):
                print("{ID} has empty {FIELD} field".format(ID=record["node"]['title'], FIELD=publication_field))
            else:
                data[record["node"]['uuid']] = record["node"][publication_field]
        if data == {}:
            result["code"] = -550
            result["msg"] = "提取{NODE}与{NODE2}之间关系过程：未查询到{NODE}.{TYPE}中的节点".format(NODE=source_node_type,
                                                                                  TYPE=node_type,
                                                                                  NODE2=target_node_type)
            print(result["msg"])
            return result
    # 创建Venue节点 todo 只能处理article，conference，inproceedings
    if not (node_type == "ARTICLE" or node_type == "CONFERENCE" or node_type == "INPROCEEDINGS"):
        print("现在不能处理【" + node_type + "】类型的venue")
        result["code"] = -551
        result["msg"] = "现在不能处理【" + node_type + "】类型的venue"
        return result
    venue_info = []
    venue_names = list(set(data.values()))
    for venue in venue_names:
        info = {"venue_name": venue, "venue_type": node_type}
        venue_info.append(info)
    create_result = create_or_match_venues(driver, venue_info, mode=2)
    if create_result["code"] != 510:
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


def revise_publications(driver, data):
    """
    从文件中提取文献信息，并建立节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid bibliography in the database')
        return -1

    with driver.session() as session:
        node = extract_publication(data)  # 提取文献信息，构造节点
        if node is None or isinstance(node, int):
            return -2
        else:
            tmp = revise_node(session, node, data)  # 创建/更新节点
            if tmp is None:
                return -3
            return 1


def revise_persons(driver, data):
    """
    提取人信息，并修改节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid person info is given')
        return -1

    with driver.session() as session:
        node = extract_person(data)  # 提取文献信息，构造节点
        if node is None or isinstance(node, int):
            return -2
        else:
            tmp = revise_node(session, node, data)  # 更新节点
            if tmp is None:
                return -3
            return 1


def revise_venues(driver, data):
    """
    提取人信息，并修改节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid venue info is given')
        return -1

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
        node.added_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        create_cypher = node.get_create_cypher()
        node_id = tx.run(create_cypher)
        for record in node_id:
            print("创建新节点：" + str(record["node"]['uuid']))
            return record["node"]['uuid']
        return None
    return None


def query_or_create_relation(driver, source_type, source_id, target_type, target_id, relation_type, to_create=True):
    """
    先查询关系是否存在，若存在，直接返回关系id，否则，创建关系并返回id。-1表示出错
    :param relation_type:
    :param target_id:
    :param target_type:
    :param source_id:
    :param source_type:
    :param driver:
    :param to_create:
    :return:
    """
    message = {"status": -1, "msg": ""}
    if source_type is None or source_id is None or target_id is None or target_type is None or relation_type is None:
        message["msg"] = "输入参数不完整"
        return None
    if driver is None:
        return None
    tx = driver.session()
    cypher = "MATCH (s:{source}) -[r:{rel}]-> (t:{target}) where s.uuid='{IDs}' and t.uuid='{IDt}'  " \
             "return s, r, t".format(source=source_type, target=target_type, IDs=source_id,
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
                 "return s, r, t".format(source=source_type, target=target_type, IDs=source_id,
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
    # create_or_match_publications('E:/reference.bib')
    driver0 = GraphDatabase.driver('bolt://localhost:7687', auth=neo4j.basic_auth('neo4j', '123456'))

    file_dir = os.path.join(Path(__file__).parent.parent, 'model_files/data/refProcessed.bib')
    result_tmp = create_or_match_publications(driver0, file_dir)
    # # 从网络中解析文献节点，并提取journal信息，创建venue节点、[wenxian]->[publication]
    build_network_of_venues(driver0, node_type="ARTICLE", publication_field="journal")
    build_network_of_venues(driver0, node_type="inproceedings".upper(), publication_field="book_title")
    # 从文献中解析author字段，创建Person节点、person->publication
    # build_network_of_persons()
