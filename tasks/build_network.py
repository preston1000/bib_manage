"""
这个是创建网络节点的任务
"""
import neo4j
from neo4j import GraphDatabase

# from utils.db_operation import create_or_match_persons
from utils.tmp_db import create_or_match_nodes, query_or_create_relation
from utils.util_text_operation import string_util, process_person_names
from utils.d_extraction import do_extract
from utils.util_operation import ini_neo4j, wrap_info_to_model, reverse_map_key_value, judge_type


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
                                       rel_type="PUBLISH_IN", filters={"node_type": "ARTICLE"},
                                       info_field='journal', use_source=1, do_split=False):
    """
    实现了从某一类节点的指定字段中提取信息，新建其他节点并建立指定的连接，这个可以处理info_field中包含多个节点信息的情况，现在只支持人的
    多个信息处理
    :param database_info: neo4j 连接信息
    :param source_node_type: 边起点类型
    :param target_node_type: 边终点类型
    :param rel_type: 边类型
    :param filters:dict，分析时，对接点进行过滤的条件，key为字段名，value为选出的可行值
    :param info_field: 待分析的字段名
    :param use_source: boolean，当为1时，使用起点节点进行数据分析，当为0时，使用终点节点进行数据分析
    :param do_split
    :return:json格式，其中
             code:-1：输入filters无效，-2:没查询到Publication节点,-3:Publication节点中没有指定信息，-4：创建/查询新节点失败，
                  -5：未识别的新节点类型，-6：部分边创建失败，1：创建成功
             msg:
    """
    result = {"code": 0, "msg": ""}
    # 解析filters的有效性，并生成查询条件语句
    if filters is not None:
        if isinstance(filters, dict):
            tmp_filter_str = ""
            for (key, value) in filters.items():
                tmp_filter_str += "node." + key + "='" + value + "' and "
            tmp_filter_str = tmp_filter_str[:-5]
        else:
            result["code"] = -1
            result["msg"] = "filter不是dict，无法使用"
            return result
        # 生成完整查询语句
        if use_source:
            cypher = "match (node:{NODE}) where {FILTER} return node".format(NODE=source_node_type, FILTER=tmp_filter_str)
        else:
            cypher = "match (node:{NODE}) where {FILTER} return node".format(NODE=target_node_type, FILTER=tmp_filter_str)
    else:
        # 生成完整查询语句
        if use_source:
            cypher = "match (node:{NODE}) return node".format(NODE=source_node_type)
        else:
            cypher = "match (node:{NODE}) return node".format(NODE=target_node_type,)
    # 连接数据库，
    driver = GraphDatabase.driver(database_info["uri"], auth=neo4j.basic_auth(database_info["username"], database_info["pwd"]))
    # 查询在指定条件下的指定类型节点
    data_pair = []  # 查询之后的输出 source: source_node_type的uuid， target：venue的name, parameter:其他属性，如作者排序等
    if use_source:
        new_type = target_node_type
    else:
        new_type = source_node_type
    with driver.session() as session:
        nodes = session.run(cypher)
        counter = 0
        counter_all = 0
        if use_source:
            for record in nodes:  # 把各节点的info_field字段提取出来，组成dict，key是节点的uuid，value是info_field字段值
                print("提取{NODE}与{NODE2}之间关系{REL}过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type,
                                                                  REL=rel_type) + str(record["node"]['id']))
                counter_all += 1
                if not string_util(record["node"][info_field]):
                    print("{ID} has empty {FIELD} field".format(ID=record["node"]['id'], FIELD=info_field))
                else:
                    if do_split:  # 需要将字段进行分割，然后生成多个节点
                        if new_type.upper() == "PERSON":
                                names = process_person_names([record["node"][info_field]])  # 这里拆分成了多个，返回值：dict, original authors: list of dict of authors
                                names = names[record["node"][info_field]]  # list of dict = {name, index}
                                for name in names:
                                    tmp = {"source": record["node"]['uuid'], "target": name["name"], "parameter": {"index": name["index"]}}
                                    data_pair.append(tmp)
                        else:
                            tmp = {"source": record["node"]['uuid'], "target": record["node"][info_field], "parameter": None}
                            data_pair.append(tmp)
                            print("暂不支持针对【" + new_type + "】的拆分")
                    else:
                        tmp = {"source": record["node"]['uuid'], "target": record["node"][info_field], "parameter": None}
                        data_pair.append(tmp)
                    counter += 1
        else:
            for record in nodes:  # 把各节点的info_field字段提取出来，组成dict，key是节点的uuid，value是info_field字段值
                print("提取{NODE}与{NODE2}之间关系{REL}过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type,
                                                                  REL=rel_type) + str(record["node"]['id']))
                counter_all += 1
                if not string_util(record["node"][info_field]):
                    print("{ID} has empty {FIELD} field".format(ID=record["node"]['id'], FIELD=info_field))
                else:
                    if do_split:  # 需要将字段进行分割，然后生成多个节点
                        if new_type.upper() == "PERSON":
                            names = process_person_names([record["node"][info_field]])  # 这里拆分成了多个，返回值：dict, original authors: list of dict of authors
                            names = names[record["node"][info_field]]  # list of dict = {name, index}
                            for name in names:
                                tmp = {"target": record["node"]['uuid'], "source": name["name"], "parameter": {"index": name["index"]}}
                                data_pair.append(tmp)
                        else:
                            tmp = {"target": record["node"]['uuid'], "source": record["node"][info_field]}
                            data_pair.append(tmp)
                            print("暂不支持针对【" + new_type + "】的拆分")
                    else:
                        tmp = {"target": record["node"]['uuid'], "source": record["node"][info_field]}
                        data_pair.append(tmp)
                    counter += 1
    if counter_all == 0:
        result["code"] = -2
        result["msg"] = "提取{NODE}与{NODE2}之间关系{REL}过程：未查询到{NODE_Q}节点中满足条件{FILTER}的节点".format(
            NODE=source_node_type, FILTER=str(filters), NODE2=target_node_type, REL=rel_type, NODE_Q=new_type)
        print(result["msg"])
        return result
    if counter == 0:
        result["code"] = -3
        result["msg"] = "提取{NODE}与{NODE2}之间关系{REL}过程：在满足条件{FILTER}的{NODE_Q}节点的字段{FIELD}中没有有效信息".format(
            NODE=source_node_type, FILTER=str(filters), NODE2=target_node_type, REL=rel_type, FIELD=info_field,
            NODE_Q=new_type)
        print(result["msg"])
        return result
    # 先将要生成的节点数据筛选出来
    data_switched = []
    if use_source:
        for tmp in data_pair:
            data_switched.append(tmp["target"])
    else:
        for tmp in data_pair:
            data_switched.append(tmp["source"])
    data_switched = list(set(data_switched))
    # 将要建立节点的信息进行封装，models的类
    info = {"name": data_switched, "type": new_type}
    nodes = wrap_info_to_model(info, filters)  # node是封装后的节点类
    # 查询/创建节点
    create_result = create_or_match_nodes(nodes, database_info)
    if create_result["code"] < 1:
        result["code"] = -4
        result["msg"] = create_result["msg"] + "\t 停止创建关系"
        return result
    # 解析出新生成节点的uuid和关键字的对应关系，key是关键字，value是uuid
    nodes = create_result["data"]
    mapping = {}
    for datum in nodes:
        if new_type == "Publication":  # Publication
            mapping[datum.id] = datum.uuid
        elif new_type == "Venue":  # Venue
            mapping[datum.venue_name] = datum.uuid
        elif new_type == "Person":  # Person
            mapping[datum.full_name] = datum.uuid
        else:
            result["code"] = -5
            result["msg"] = "未识别的节点类型，停止创建边"
            return result
    # 更新data_pair,将其中关键字部分改成uuid
    if use_source:
        for pair in data_pair:
            tmp_id = mapping[pair["target"]]
            pair["target"] = tmp_id
    else:
        for pair in data_pair:
            tmp_id = mapping[pair["source"]]
            pair["source"] = tmp_id
    # 查询/建立边
    counter = 0
    counter_all = 0
    with driver.session() as session:
        for pair in data_pair:
            counter_all += 1

            tmp = query_or_create_relation(session, source_node_type, pair["source"], target_node_type, pair["target"], rel_type,
                                           to_create=True, parameters=pair["parameter"])
            if tmp["code"] > 0:
                counter += 1
    if counter < counter_all:
        result["code"] = -6
        result["msg"] = "部分边创建失败"
        return result
    else:
        result["code"] = 1
        result["msg"] = "全部边创建成功"
        return result


if __name__ == "__main__":

    file = "/Volumes/Transcend/web/utils/reference.bib"
    neo4j_config_file = "/Volumes/Transcend/web/web_pages/webs/neo4j.conf"
    database_info = ini_neo4j(neo4j_config_file)  # 配置数据库
    # 从文件中生成Publication节点
    # generate_pub_node_from_file(file, database_info)
    # # 从Publication节点中分析期刊信息，创建Venue节点并创建Publish_in边
    # build_relation_from_node_attribute(database_info)
    # 从Publication节点中分析人信息，创建Person节点并创建Author边
    build_relation_from_node_attribute(database_info, source_node_type="Person", target_node_type="Publication",
                                       rel_type="AUTHOR", filters=None,
                                       info_field='author', use_source=False, do_split=True)
