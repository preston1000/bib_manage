"""
这个是创建网络节点的任务
"""
import neo4j
from neo4j import GraphDatabase

# from utils.db_operation import create_or_match_persons
from utils.tmp_db import create_or_match_nodes
from utils.util_text_operation import string_util, process_person_names
from utils.d_extraction import do_extract
from utils.util_operation import ini_neo4j, wrap_info_to_model


def generate_pub_node_from_file(file, database_info):
    """
    从文件中提取bib信息，然后写入neo4j
    :param file: bib文件或Excel文件
    :param neo4j_config_file: 配置文件
    :return:
    """
    # 提取bib信息
    flag, msg, info = do_extract(file)
    # 创建数据库节点
    create_or_match_nodes(info, database_info)  # 写入节点


def build_relation_from_node_attribute(database_info, source_node_type="Publication", target_node_type="Venue",
                                       rel_type="PUBLISH_IN", use_source=1, filters={"node_type": "ARTICLE"},
                                       info_field='journal'):
    """
    实现了从某一类节点的指定字段中提取信息，新建其他节点并建立指定的连接
    :param database_info: neo4j 连接信息
    :param source_node_type: 边起点类型
    :param target_node_type: 边终点类型
    :param rel_type: 边类型
    :param use_source: boolean，当为1时，使用起点节点进行数据分析，当为0时，使用终点节点进行数据分析
    :param filters:dict，分析时，对接点进行过滤的条件，key为字段名，value为选出的可行值
    :param info_field: 待分析的字段名
    :return:code:-6:创建节点时，node_name name和uuid关系提取失败；-7:现在只能处理article和conference；-8：未查询到有效的venue name;
                  -9：原始数据、处理后name、uuid对应失败,-10创建关系失败;1:成功
             data:
             msg:
    """
    result = {"code": 0, "msg": "", "data": ""}
    # 查询指定venue_type字段的source_node_type
    if filters is not None:
        if isinstance(filters, dict):
            tmp_filter_str = ""
            for (key, value) in filters.items():
                tmp_filter_str += "node." + key.upper() + "='" + value + "' and "
            tmp_filter_str = tmp_filter_str[:-5]
        else:
            result.msg = "filter不是dict，无法使用"
            return result
    if use_source:
        cypher = "match (node:{NODE}) where {FILTER} return node".format(NODE=source_node_type, FILTER=tmp_filter_str)
    else:
        cypher = "match (node:{NODE}) where {FILTER} return node".format(NODE=target_node_type, FILTER=tmp_filter_str)
    driver = GraphDatabase.driver(database_info["uri"], auth=neo4j.basic_auth(database_info["username"], database_info["pwd"]))
    with driver.session() as session:
        nodes = session.run(cypher)
        data = {}  # key: source_node_type的uuid， value：venue的name
        counter = 0
        counter_all = 0
        for record in nodes:  # 把各节点的info_field字段提取出来，组成dict，key是节点的uuid，value是info_field字段值
            print("提取{NODE}与{NODE2}之间关系{REL}过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type,
                                                              REL=rel_type) + str(record["node"]['id']))
            counter_all += 1
            if not string_util(record["node"][info_field]):
                print("{ID} has empty {FIELD} field".format(ID=record["node"]['id'], FIELD=info_field))
            else:
                data[record["node"]['uuid']] = record["node"][info_field]
                counter += 1
        if counter_all == 0:
            print("提取{NODE}与{NODE2}之间关系{REL}过程：未查询到{NODE}节点中满足条件{FILTER}的节点".format(
                NODE=source_node_type, FILTER=str(filters), NODE2=target_node_type, REL=rel_type))
            result["code"] = -8
            result["msg"] = "提取{NODE}与{NODE2}之间关系{REL}过程：未查询到{NODE}节点中满足条件{FILTER}的节点".format(
                NODE=source_node_type, FILTER=str(filters), NODE2=target_node_type, REL=rel_type)
            return result
        # 创建新节点
        # if not (node_type == "ARTICLE" or node_type == "CONFERENCE" or node_type == "INPROCEEDINGS"):
        #     print("现在不能处理【" + node_type + "】类型的venue")
        #     result["code"] = -7
        #     result["msg"] = "现在不能处理【" + node_type + "】类型的venue"
        #     return result
        new_node_info = []
        node_names = list(set(data.values()))
        if use_source:
            new_type = target_node_type
        else:
            new_type = source_node_type
        info = {"name": node_names, "type": new_type}
        nodes = wrap_info_to_model(info, filters)
        create_result = create_or_match_nodes(nodes, database_info)  # 这里要封装好的节点
        if create_result is not None:
            result["code"] = -1
            result["msg"] = create_result + "\t 停止创建关系"
            return result
        # 提取Venue和Publication关系
        rel_mapping_name_uuid = create_result["data"]  # 这是venue name 和uuid之间的mapping关系
        name_mappings = create_result["node_names"]
        # if rel_mapping_name_uuid is None or not isinstance(rel_mapping_name_uuid, dict) or \
        #         not isinstance(name_mappings, dict):
        #     result["code"] = -6
        #     result["msg"] = create_result["msg"] + "\n 停止创建关系"
        #     return result
        # for source_id, target_name in data.items():
        #     processed_name = name_mappings.get(target_name, None)
        #     if processed_name is None:
        #         result["code"] = min(-9, result["code"])
        #         result["msg"] += ",提取处理后venue name失败：" + target_name
        #         print("提取处理后venue name失败：" + target_name)
        #         continue
        #     venue_id = rel_mapping_name_uuid.get(processed_name, None)
        #     if venue_id is None:
        #         result["code"] = min(-9, result["code"])
        #         result["msg"] += ",提取venue的uuid失败： " + processed_name
        #         print("提取venue的uuid失败： " + processed_name)
        #         continue
        #     match_cypher = "MATCH  (pub:" + source_node_type + " {uuid:'" + source_id + "'}) -[:" + rel_type + \
        #                    "]-> (ven:" + target_node_type + " {uuid:'" + venue_id + "'})  return pub, ven"
        #     query_result = session.run(match_cypher)
        #     query_result = query_result.data()
        #     if len(query_result) > 0:
        #         print("关系已存在(" + rel_type + "):" + source_id + "->" + venue_id)
        #         continue
        #     create_cypher = "MATCH  (pub:" + source_node_type + " {uuid:'" + source_id + "'}) , (ven:" + \
        #                     target_node_type + " {uuid:'" + venue_id + "'})  CREATE (pub) -[:" + rel_type + \
        #                     "]-> (ven) return pub, ven"
        #     query_result = session.run(create_cypher)
        #     query_result = query_result.data()
        #     if len(query_result) > 0:
        #         print("，创建关系成功(" + rel_type + "):" + source_id + "->" + venue_id)
        #     else:
        #         result["code"] = min(-10, result["code"])
        #         result["msg"] += "，创建关系失败(" + rel_type + "):" + source_id + "->" + venue_id
        #         print("，创建关系失败(" + rel_type + "):" + source_id + "->" + venue_id)
        # if result["code"] == 0:
        #     result["msg"] = "成功"
        #     result["code"] = 1
    return result


# def build_network_of_persons(source_node_type="Publication", publication_field='author', target_node_type="Person",
#                              rel_type="WRITE"):
#     # 查询所有articles of publication
#     result = {"code": 0, "msg": "", "data": ""}
#     cypher = "match (node:{NODE}) return node".format(NODE=source_node_type)
#     driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
#     with driver.session() as session:
#         nodes = session.run(cypher)
#         data = {}
#         for record in nodes:
#             print("提取{NODE}与{NODE2}之间关系过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type)
#                   + str(record["node"]['uuid']))
#             if not string_util(record["node"][publication_field]):
#                 print("{ID} has empty {FIELD} field".format(ID=record["node"]['uuid'], FIELD=publication_field))
#             else:
#                 data[record["node"]['uuid']] = record["node"][publication_field]  # value是bib的name，要拆分处理成list of string
#         if data is {}:
#             print("提取{NODE}与{NODE2}之间关系过程：未查询到{NODE}.{TYPE}中的节点".format(NODE=source_node_type,
#                                                                         TYPE=publication_field, NODE2=target_node_type))
#             return
#     # 处理多个作者的情况
#     person_names = []
#     for key, names in data.items():
#         names = process_person_names([names])  # 这里拆分成了多个，返回值：dict, original authors: list of dict of authors
#         for _, separate_names in names.items():
#             for separate_name in separate_names:
#                 person_names.append(separate_name["name"])
#         data[key] = names
#     # 创建Person节点
#     person_info = []  # 组装数据，for 生成person节点
#     person_names = list(set(person_names))  # 去重
#     for person in person_names:
#         info = {"full_name": person}
#         person_info.append(info)
#     create_result = create_or_match_persons(person_info, mode=2)
#     if create_result["code"] < 0:
#         result["code"] = create_result["code"]
#         result["msg"] = create_result["msg"] + "\n 停止创建关系"
#         return result
#     # 提取person和Publication关系
#     rel_mapping_name_uuid = create_result["data"]  # 这是处理后person name 和uuid之间的mapping关系
#     name_mappings = create_result["names"]  # 这是原始和处理后name的mapping
#     if rel_mapping_name_uuid is None or not isinstance(rel_mapping_name_uuid, dict):
#         result["code"] = -6
#         result["msg"] = create_result["msg"] + "\n 停止创建关系"
#         return result
#     driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
#     with driver.session() as session:
#         for source_id, target_names in data.items():  # target_names is a list
#             for _, value in target_names.items():
#                 target_names = value
#                 break
#             for target_name in target_names:
#                 target_name = target_name["name"]
#                 processed_name = name_mappings.get(target_name, None)
#                 if processed_name is None:
#                     result["code"] = min(-9, result["code"])
#                     result["msg"] += ",提取处理后person name失败：" + target_name
#                     print("提取处理后person name失败：" + target_name)
#                     continue
#                 target_id = rel_mapping_name_uuid.get(processed_name, None)
#                 if target_id is None:
#                     result["code"] = min(-9, result["code"])
#                     result["msg"] += ",提取person的uuid失败： " + processed_name
#                     print("提取person的uuid失败： " + processed_name)
#                     continue
#                 match_cypher = "MATCH  (m:" + source_node_type + " {uuid:'" + source_id + "'}) -[:" + rel_type + \
#                                "]-> (n:" + target_node_type + " {uuid:'" + target_id + "'})  return m, n"
#                 query_result = session.run(match_cypher)
#                 query_result = query_result.data()
#                 if len(query_result) > 0:
#                     print("关系已存在(PUBLISH_IN):" + source_id + "->" + target_id)
#                     continue
#                 create_cypher = "MATCH  (m:" + source_node_type + " {uuid:'" + source_id + "'}) , (n:" + target_node_type +\
#                                 " {uuid:'" + target_id + "'}) " " CREATE (n) -[:" + rel_type + "]-> (m) return m, n"
#                 query_result = session.run(create_cypher)
#                 query_result = query_result.data()
#                 if len(query_result) > 0:
#                     print("，创建关系成功(" + target_node_type + "):" + source_id + "->" + target_id)
#                 else:
#                     result["code"] = min(-10, result["code"])
#                     result["msg"] += "，创建关系失败(" + target_node_type + "):" + source_id + "->" + target_id
#                     print("，创建关系失败(" + target_node_type + "):" + source_id + "->" + target_id)
#         if result["code"] == 0:
#             result["msg"] = "成功"
#             result["code"] = 1
#     return result
#

if __name__ == "__main__":

    file = "/Volumes/Transcend/web/utils/reference.bib"
    neo4j_config_file = "/Volumes/Transcend/web/web_pages/webs/neo4j.conf"
    database_info = ini_neo4j(neo4j_config_file)  # 配置数据库
    # 从文件中生成Publication节点
    # generate_pub_node_from_file(file, database_info)
    # 从Publication节点中分析期刊信息，创建Venue节点并创建Publish_in边
    build_relation_from_node_attribute(database_info)
