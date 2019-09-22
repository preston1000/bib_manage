"""
这个是根据数据库中节点，进行推断并建立节点或关系的操作
"""
import time
import uuid

import neo4j
from neo4j import GraphDatabase

from utils.tmp_db import create_or_match_nodes
from utils.util_text_operation import string_util, process_person_names


def build_network_of_venues(session, source_node_type="Publication", node_type="ARTICLE", publication_field='journal',
                            target_node_type="Venue", rel_type="PUBLISH_IN"):
    """
    从数据库的publication节点中查询，对entry_type属于article 和conference的节点，解析journal字段，创建venue节点，并建立PUBLISH_IN关系
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
    create_result = create_or_match_nodes(venue_info, mode=2)
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


def build_network_of_persons(session, source_node_type="Publication", publication_field='author', target_node_type="Person",
                             rel_type="WRITE"):
    # 查询所有articles of publication
    result = {"code": 0, "msg": "", "data": ""}
    cypher = "match (node:{NODE}) return node".format(NODE=source_node_type)

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
    create_result = create_or_match_nodes(person_info, mode=2)
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
        return "DB is not connected"
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
