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
from utils.constants import GlobalVariables

field_names = GlobalVariables.const_field_name
node_types = GlobalVariables.const_node_type
edge_types = GlobalVariables.const_edge_tpe


def generate_pub_node_from_file(file, database_info):
    """
    从文件中提取bib信息，然后写入neo4j
    :param file: bib文件或Excel文件
    :param neo4j_config_file: 配置文件
    :return:
    """
    # 提取bib信息
    extract_result = do_extract(file)
    if extract_result["code"] == 110:
        print(extract_result["msg"])
    elif extract_result["code"] == 111:
        create_or_match_nodes(extract_result["data"], database_info)  # 写入节点
    elif extract_result["code"] == 112:
        print(extract_result["msg"])
    else:
        print(extract_result["msg"])
    return extract_result


def build_relation_from_node_attribute(database_info, source_node_type="PUBLICATION", target_node_type="VENUE",
                                       rel_type="PUBLISHED_IN", filters={"node_type": "ARTICLE"},
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
    result = {"code": 0, "msg": "", "data": ""}
    identifier = 'node'
    try:
        node_types.index(source_node_type)
        node_types.index(target_node_type)
    except:
        result["code"] = -129
        result["msg"] = "起终点类型不符合要求"
        return result
    try:
        edge_types.index(rel_type)
    except:
        result["code"] = -130
        result["msg"] = "边类型不符合要求"
        return result

    # 解析filters的有效性，并生成查询条件语句
    if filters is not None:
        if isinstance(filters, dict):
            tmp_filter_str = ""
            for (key, value) in filters.items():
                tmp_filter_str += identifier + "." + key + "='" + value + "' and "
            tmp_filter_str = tmp_filter_str[:-5]
        else:
            result["code"] = -125
            result["msg"] = "filter不是dict，无法使用"
            return result
        # 生成完整查询语句
        if use_source:
            cypher = "match ({IF}:{NODE}) where {FILTER} return {IF}".format(IF=identifier, NODE=source_node_type, FILTER=tmp_filter_str)
        else:
            cypher = "match ({IF}:{NODE}) where {FILTER} return {IF}".format(IF=identifier, NODE=target_node_type, FILTER=tmp_filter_str)
    else:
        # 生成完整查询语句
        if use_source:
            cypher = "match ({IF}:{NODE}) return {IF}".format(IF=identifier, NODE=source_node_type)
        else:
            cypher = "match ({IF}:{NODE}) return {IF}".format(IF=identifier, NODE=target_node_type)
    # 连接数据库，
    uri = database_info.get("uri", None)
    user_name = database_info.get("username", None)
    pwd = database_info.get("pwd", None)
    if uri is None or user_name is None or pwd is None:
        result["code"] = -126
        result["msg"] = "数据库信息不完整"
        return result
    driver = GraphDatabase.driver(uri, auth=neo4j.basic_auth(user_name, pwd))
    # 查询在指定条件下的指定类型节点
    data_pair = []  # 查询之后的输出 source: source_node_type的uuid， target：venue的name, parameter:其他属性，如作者排序等
    if use_source:
        new_type = target_node_type
    else:
        new_type = source_node_type
    try:
        with driver.session() as session:
            nodes = session.run(cypher)
    except:
        result["code"] = -127
        result["msg"] = "数据库连接失败"
        return result
    counter_has_content = 0
    counter_all = 0
    # counter_processed = 0  todo 这里没有检查有数据的记录是否成功处理，后面要加
    if use_source:
        for record in nodes:  # 把各节点的info_field字段提取出来，组成dict，key是节点的uuid，value是info_field字段值
            record_id = record[identifier][field_names[31]]  # uuid  todo 检查是id还是uuid
            print("提取{NODE}与{NODE2}之间关系{REL}过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type,
                                                              REL=rel_type) + str(record_id))
            counter_all += 1
            record_field = record[identifier][info_field]
            if not string_util(record_field):
                print("{ID} has empty {FIELD} field".format(ID=record_id, FIELD=info_field))
            else:
                if do_split:  # 需要将字段进行分割，然后生成多个节点
                    if new_type.upper() == node_types[2]:  # person # todo 这是是什么情况？？
                        names = process_person_names([record_field])  # 这里拆分成了多个，返回值：dict, original authors: list of dict of authors
                        names = names[record_field]  # list of dict = {name, index}
                        for name in names:
                            tmp = {"source": record_id, "target": name["name"], "parameter": {"index": name["index"]}}
                            data_pair.append(tmp)
                    else:
                        tmp = {"source": record_id, "target": record_field, "parameter": None}
                        data_pair.append(tmp)
                        result["msg"] += "暂不支持针对【" + new_type + "】的拆分"
                        print("暂不支持针对【" + new_type + "】的拆分")
                else:
                    tmp = {"source": record_id, "target": record_field, "parameter": None}
                    data_pair.append(tmp)
                counter_has_content += 1
    else:
        for record in nodes:  # 把各节点的info_field字段提取出来，组成dict，key是节点的uuid，value是info_field字段值
            record_id = record[identifier][field_names[31]]  # id
            print("提取{NODE}与{NODE2}之间关系{REL}过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type,
                                                              REL=rel_type) + str(record_id))
            counter_all += 1
            record_field = record[identifier][info_field]
            if not string_util(record_field):
                print("{ID} has empty {FIELD} field".format(ID=record_id, FIELD=info_field))
            else:
                if do_split:  # 需要将字段进行分割，然后生成多个节点
                    if new_type.upper() == node_types[2]:  # person
                        names = process_person_names([record_field])  # 这里拆分成了多个，返回值：dict, original authors: list of dict of authors
                        names = names[record_field]  # list of dict = {name, index}
                        for name in names:
                            tmp = {"target": record_id, "source": name["name"], "parameter": {"index": name["index"]}}
                            data_pair.append(tmp)
                    else:
                        tmp = {"target": record_id, "source": record_field}
                        data_pair.append(tmp)
                        result["msg"] += "暂不支持针对【" + new_type + "】的拆分"
                        print("暂不支持针对【" + new_type + "】的拆分")
                else:
                    tmp = {"target": record_id, "source": record_field}
                    data_pair.append(tmp)
                counter_has_content += 1
    if counter_all == 0:
        result["code"] = 125
        result["msg"] += "\n 提取{NODE}与{NODE2}之间关系{REL}过程：未查询到{NODE_Q}节点中满足条件{FILTER}的节点".format(
            NODE=source_node_type, FILTER=str(filters), NODE2=target_node_type, REL=rel_type, NODE_Q=new_type)
        print(result["msg"])
        return result
    if counter_has_content == 0:
        result["code"] = 126
        result["msg"] += "\n 提取{NODE}与{NODE2}之间关系{REL}过程：在满足条件{FILTER}的{NODE_Q}节点的字段{FIELD}中没有有效信息".format(
            NODE=source_node_type, FILTER=str(filters), NODE2=target_node_type, REL=rel_type, FIELD=info_field,
            NODE_Q=new_type)
        print(result["msg"])
        return result
    # 先将要生成的节点数据筛选出来 todo 没有检查是否所有记录都成功处理
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
    create_result = create_or_match_nodes(nodes, database_info, to_create=True, return_type="class")
    if create_result["code"] < 0:
        result["code"] = -128
        result["msg"] = create_result["msg"] + "\t 查询/新建节点信息失败，停止创建关系"
        return result
    # 解析出新生成节点的uuid和关键字的对应关系，key是关键字，value是uuid
    nodes = create_result["data"]
    mapping = {}
    for datum in nodes:
        if new_type == node_types[0]:  # Publication
            mapping[datum.id] = datum.uuid
        elif new_type == node_types[1]:  # Venue
            mapping[datum.venue_name] = datum.uuid
        elif new_type == node_types[2]:  # Person
            mapping[datum.full_name] = datum.uuid
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
    counter_has_content = 0
    counter_all = len(data_pair)
    with driver.session() as session:
        for pair in data_pair:
            tmp = query_or_create_relation(session, source_node_type, pair["source"], target_node_type, pair["target"], rel_type,
                                           to_create=True, parameters=pair["parameter"])
            if tmp["code"] == 170 or tmp["code"] == 171:
                counter_has_content += 1
    if counter_has_content < counter_all:
        result["code"] = -131
        result["msg"] = "部分边创建失败"
        return result
    else:
        result["code"] = 127
        result["msg"] = "全部边创建成功"
        return result


if __name__ == "__main__":

    file = "/Volumes/Transcend/web/utils/reference.bib"
    neo4j_config_file = "/Volumes/Transcend/web/web_pages/webs/neo4j.conf"
    database_info = ini_neo4j(neo4j_config_file)  # 配置数据库
    # 从文件中生成Publication节点
    result = generate_pub_node_from_file(file, database_info)
    print(str(result))
    # # 从Publication节点中分析期刊信息，创建Venue节点并创建Publish_in边
    result = build_relation_from_node_attribute(database_info)
    print(str(result))
    # 从Publication节点中分析人信息，创建Person节点并创建Author边
    result = build_relation_from_node_attribute(database_info, source_node_type="PERSON", target_node_type="PUBLICATION",
                                       rel_type="AUTHORED_BY", filters=None,
                                       info_field='author', use_source=False, do_split=True)
    print(str(result))
