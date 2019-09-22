"""
这个是根据数据库中节点，进行推断并建立节点或关系的操作
"""

from utils.tmp_db import create_or_match_nodes
from utils.util_text_operation import string_util, process_person_names


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
