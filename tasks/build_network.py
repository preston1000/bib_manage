"""
这个是创建网络节点的任务
"""
import os

from utils.tmp_db import revise_node_by_fields
from utils.db_util.operations import create_or_match_nodes, query_by_multiple_field, query_or_create_relation
from utils.nlp.text_utils import string_util, process_person_names, process_pages
from utils.bib_util.extraction import extract_bib_info_from_file, extract_publication_from_bib_info, \
    extract_venue_from_bib_info, extract_person_from_bib_info, extract_rel_publish_in_from_pub_info,\
    extract_rel_author_by_from_pub_info
from utils.util_operation import wrap_info_to_model
from utils.db_util.utils import process_neo4j_result
from utils.initialization import NODE_TYPES, FIELD_NAMES_PUB, EDGE_TYPES, FIELD_NAMES_PUB
from utils.initialization import ini_result, RESULT_CODE, RESULT_MSG, RESULT_DATA


def build(driver, file_name, sheet_name=None, column_name=None):
    """
    从文件中提取文献信息，并生成Publication、Venue、Person和他们之间的Published_in、Authored_by关系。 ---checked
    :param driver:
    :param file_name:
    :param sheet_name:
    :param column_name:
    :return:
    """
    result = ini_result()
    if file_name is None or not os.path.exists(file_name):
        result["code"] = -504
        result["msg"] = "file does not exist"
        return result
    if driver is None:
        result[RESULT_CODE] = -500
        result[RESULT_MSG] = "the database is not configured!"
        return result

    # 从文件中提取info
    publication_info = extract_bib_info_from_file(file_name, sheet_name, column_name)  # dict

    pubs, venues, persons = [], [], []
    fail_pub, fail_venue, fail_person = [], [], []

    for entry in publication_info:
        # 解析文献
        tmp_result_pub = extract_publication_from_bib_info(entry)
        if tmp_result_pub[RESULT_CODE] == 1001:
            pubs.append(tmp_result_pub[RESULT_DATA])
        else:
            fail_pub.append(entry)
        # 解析venue
        tmp_result_venue = extract_venue_from_bib_info(entry)
        if tmp_result_venue[RESULT_CODE] == 1005:
            venues.append(tmp_result_venue[RESULT_DATA])
        else:
            fail_venue.append(entry)
        # 解析person
        tmp_result_person = extract_person_from_bib_info(entry)
        if tmp_result_person[RESULT_CODE] == 1006:
            persons.append(tmp_result_person[RESULT_DATA])
        else:
            fail_person.append(entry)

    pubs = None if pubs == [] else pubs
    venues = None if venues == [] else venues
    persons = None if persons == [] else persons
    # 利用提取的Publication、Venue、Person写入数据库
    db_pub_result = create_or_match_nodes(driver, pubs, return_type="class", to_create=True)
    if db_pub_result[RESULT_CODE] != 1303:
        result[RESULT_CODE] = -1205
        result[RESULT_MSG] = "Publication节点生成失败"
    db_ven_result = create_or_match_nodes(driver, venues, return_type="class", to_create=True)
    if db_ven_result[RESULT_CODE] != 1303:
        result[RESULT_CODE] = -1205
        result[RESULT_MSG] += "。Venue节点生成失败"
    db_ppl_result = create_or_match_nodes(driver, persons, return_type="class", to_create=True)
    if db_ppl_result[RESULT_CODE] != 1303:
        result[RESULT_CODE] = -1205
        result[RESULT_MSG] += "。Person节点生成失败"

    if result[RESULT_CODE] == -1205:
        return result

    # 生成边 published in
    publish_in_info_result = extract_rel_publish_in_from_pub_info(db_pub_result[RESULT_DATA])  # 获取published_in信息

    failed_pair = []
    if publish_in_info_result[RESULT_CODE] in [1009, 1010]:  # 若提取成功，则创建边
        pairs = publish_in_info_result[RESULT_DATA]["success"]
        for entry in pairs:
            venue_info = [entry]
            venue_result = create_or_match_nodes(driver, venue_info, "VENUE")
            if venue_result[RESULT_CODE] != 904:
                failed_pair.append(entry)
                continue
            tmp_result = query_or_create_relation(driver, "PUBLICATION", entry["pub"].uuid, "VENUE", venue_result[RESULT_DATA][0].uuid, "PUBLISHED_IN")
            if tmp_result[RESULT_CODE] not in [1304, 1306]:
                failed_pair.append(entry)

    # 生成边 AUTHORED_BY
    author_by_info_result = extract_rel_author_by_from_pub_info(db_pub_result[RESULT_DATA])  # 获取authored_by信息
    if author_by_info_result[RESULT_CODE] in [1009, 1010]:  # 若提取成功，则创建边
        pairs = author_by_info_result[RESULT_DATA]["success"]
        for entry in pairs:
            person_info = [entry]
            person_result = create_or_match_nodes(driver, person_info, "PERSON")
            if person_result[RESULT_CODE] != 904:
                failed_pair.append(entry)
                continue
            tmp_result = query_or_create_relation(driver, "PUBLICATION", entry["pub"].uuid, "PERSON",
                                                  person_result[RESULT_DATA][0].uuid, "AUTHORED_BY")
            if tmp_result[RESULT_CODE] not in [1304, 1306]:
                failed_pair.append(entry)
    #
    failed_pair = None if failed_pair == [] else failed_pair

    if failed_pair is not None:
        result[RESULT_CODE] = 1400
        result[RESULT_MSG] = "success"
    else:
        result[RESULT_CODE] = -1400
        result[RESULT_MSG] = "partially or fully failed"

    return result


def generate_pub_node_from_file(driver, file_name, sheet_name, column_name):
    """
    从文件中提取bib信息，然后写入neo4j.checked
    :param column_name:
    :param sheet_name:
    :param file_name: bib文件或Excel文件
    :param driver: 数据库接口
    :return:
    """
    # 提取bib信息
    result = ini_result()
    extract_result = extract_bib_info_from_file(file_name, sheet_name, column_name)  # 结果是models类

    if extract_result[RESULT_CODE] == 1003:
        extracted_data = extract_result[RESULT_DATA]  # list of pubs
        db_result = create_or_match_nodes(extracted_data, driver)  # 写入节点
        if db_result[RESULT_CODE] != 1303:
            result[RESULT_CODE] = -1201
            result[RESULT_MSG] = extract_result[RESULT_MSG]
        else:
            result[RESULT_CODE] = 1200
            result[RESULT_MSG] = "success"
    else:
        print("不写入数据库：" + extract_result[RESULT_MSG])
        result[RESULT_CODE] = -1200
        result[RESULT_MSG] = extract_result[RESULT_MSG]

    return result


def build_relation_from_node_attribute(driver, source_node_type="PUBLICATION", target_node_type="VENUE",
                                       rel_type="PUBLISHED_IN", filters={"node_type": "ARTICLE"},
                                       info_field='JOURNAL', use_source=1, do_split=False):
    """
    实现了从某一类节点的指定字段中提取信息，新建其他节点并建立指定的连接，这个可以处理info_field中包含多个节点信息的情况，现在只支持人的
    多个信息处理
    :param driver: neo4j 连接信息
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
    result = ini_result()

    if driver is None:
        result[RESULT_CODE] = -500
        result[RESULT_MSG] = "driver is not given"
        return result

    if source_node_type not in NODE_TYPES or target_node_type not in NODE_TYPES:
        result[RESULT_CODE] = -1202
        result[RESULT_MSG] = "node type is not valid"
        return result

    if rel_type not in EDGE_TYPES:
        result[RESULT_CODE] = -1203
        result[RESULT_MSG] = "edge type is not valid"
        return result

    if info_field not in FIELD_NAMES_PUB:
        result[RESULT_CODE] = -1204
        result[RESULT_MSG] = "field is not valid"
        return result

    if (filters is not None and not isinstance(filters, dict)) or \
            (filters is not None and len(set(filters.keys()) & set(FIELD_NAMES_PUB)) == 0) or \
            use_source is None or do_split is None:
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "invalid arguments"
        return result

    identifier = 'node'
    # 解析filters的有效性，并生成查询条件语句
    if filters is not None:
        tmp_filter_str = ""
        for (key, value) in filters.items():
            tmp_filter_str += identifier + "." + key + "='" + value + "' and "
        tmp_filter_str = tmp_filter_str[:-5]
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
        result[RESULT_CODE] = -910
        result[RESULT_MSG] = "数据库连接失败"
        return result

    counter_has_content = 0
    counter_all = 0
    # counter_processed = 0  todo 这里没有检查有数据的记录是否成功处理，后面要加
    if use_source:
        for record in nodes:  # 把各节点的info_field字段提取出来，组成dict，key是节点的uuid，value是info_field字段值
            record_id = record[identifier][FIELD_NAMES_PUB[31]]  # uuid
            print("提取{NODE}与{NODE2}之间关系{REL}过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type,
                                                              REL=rel_type) + str(record_id))
            counter_all += 1
            record_field = record[identifier][info_field]
            if not string_util(record_field):
                print("{ID} has empty {FIELD} field".format(ID=record_id, FIELD=info_field))
            else:
                if do_split:  # 需要将字段进行分割，然后生成多个节点
                    if new_type.upper() == NODE_TYPES[2]:  # person # todo 这是是什么情况？？
                        names = process_person_names([record_field])  # 这里拆分成了多个，返回值：dict, original authors: list of dict of authors
                        names = names[record_field]  # list of dict = {name, index}
                        for name in names:
                            tmp = {"source": record_id, "target": name["name"], "parameter": {"index": name["index"]}}
                            data_pair.append(tmp)
                    else:
                        tmp = {"source": record_id, "target": record_field, "parameter": None}
                        data_pair.append(tmp)
                        result[RESULT_MSG] += "暂不支持针对【" + new_type + "】的拆分"
                        print("暂不支持针对【" + new_type + "】的拆分")
                else:
                    tmp = {"source": record_id, "target": record_field, "parameter": None}
                    data_pair.append(tmp)
                counter_has_content += 1
    else:
        for record in nodes:  # 把各节点的info_field字段提取出来，组成dict，key是节点的uuid，value是info_field字段值
            record_id = record[identifier][FIELD_NAMES_PUB[31]]  # uuid
            print("提取{NODE}与{NODE2}之间关系{REL}过程：查询到节点：".format(NODE=source_node_type, NODE2=target_node_type,
                                                              REL=rel_type) + str(record_id))
            counter_all += 1
            record_field = record[identifier][info_field]
            if not string_util(record_field):
                print("{ID} has empty {FIELD} field".format(ID=record_id, FIELD=info_field))
            else:
                if do_split:  # 需要将字段进行分割，然后生成多个节点
                    if new_type.upper() == NODE_TYPES[2]:  # person
                        names = process_person_names([record_field])  # 这里拆分成了多个，返回值：dict, original authors: list of dict of authors
                        names = names[record_field]  # list of dict = {name, index}
                        for name in names:
                            tmp = {"target": record_id, "source": name["name"], "parameter": {"index": name["index"]}}
                            data_pair.append(tmp)
                    else:
                        tmp = {"target": record_id, "source": record_field}
                        data_pair.append(tmp)
                        result[RESULT_MSG] += "暂不支持针对【" + new_type + "】的拆分"
                        print("暂不支持针对【" + new_type + "】的拆分")
                else:
                    tmp = {"target": record_id, "source": record_field}
                    data_pair.append(tmp)
                counter_has_content += 1
    if counter_all == 0:
        result[RESULT_CODE] = 125
        result[RESULT_MSG] += "\n 提取{NODE}与{NODE2}之间关系{REL}过程：未查询到{NODE_Q}节点中满足条件{FILTER}的节点".format(
            NODE=source_node_type, FILTER=str(filters), NODE2=target_node_type, REL=rel_type, NODE_Q=new_type)
        print(result[RESULT_MSG])
        return result
    if counter_has_content == 0:
        result[RESULT_CODE] = 126
        result[RESULT_MSG] += "\n 提取{NODE}与{NODE2}之间关系{REL}过程：在满足条件{FILTER}的{NODE_Q}节点的字段{FIELD}中没有有效信息".format(
            NODE=source_node_type, FILTER=str(filters), NODE2=target_node_type, REL=rel_type, FIELD=info_field,
            NODE_Q=new_type)
        print(result[RESULT_MSG])
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
    if create_result[RESULT_CODE] < 0:
        result[RESULT_CODE] = -128
        result[RESULT_MSG] = create_result[RESULT_MSG] + "\t 查询/新建节点信息失败，停止创建关系"
        return result
    # 解析出新生成节点的uuid和关键字的对应关系，key是关键字，value是uuid
    nodes = create_result[RESULT_DATA]
    mapping = {}
    for datum in nodes:
        if new_type == NODE_TYPES[0]:  # Publication
            mapping[datum.id] = datum.uuid
        elif new_type == NODE_TYPES[1]:  # Venue
            mapping[datum.venue_name] = datum.uuid
        elif new_type == NODE_TYPES[2]:  # Person
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
            if tmp[RESULT_CODE] == 170 or tmp[RESULT_CODE] == 171:
                counter_has_content += 1
    if counter_has_content < counter_all:
        result[RESULT_CODE] = -131
        result[RESULT_MSG] = "部分边创建失败"
        return result
    else:
        result[RESULT_CODE] = 127
        result[RESULT_MSG] = "全部边创建成功"
        return result


def revise_node_info(database_info, node_type, node_field):
    """
    实现的是对某一类型所有节点的某一属性的修改，如对pub节点的pages属性的统一处理等
    :param database_info: dict，数据库信息
    :param node_type: 节点名，str
    :param node_field: 属性名，str
    :return:
    """
    result = {RESULT_CODE: 0, RESULT_MSG: "", RESULT_DATA: ""}
    # 连接数据库，
    if database_info is None or not isinstance(database_info, dict):
        result[RESULT_CODE] = -280
        result[RESULT_MSG] = "数据库信息缺失"
        return result
    uri = database_info.get("uri", None)
    user_name = database_info.get("username", None)
    pwd = database_info.get("pwd", None)
    if uri is None or user_name is None or pwd is None:
        result[RESULT_CODE] = -281
        result[RESULT_MSG] = "数据库信息不完整"
        return result
    driver = GraphDatabase.driver(uri, auth=neo4j.basic_auth(user_name, pwd))
    # 节点类型
    try:
        node_type_index = NODE_TYPES.index(node_type)
    except:
        result[RESULT_CODE] = -282
        result[RESULT_MSG] = "节点类型不符合要求"
        return result
    if node_type_index == 0:  # pub
        try:
            field_index = FIELD_NAMES_PUB.index(node_field)
        except:
            result[RESULT_CODE] = -284
            result[RESULT_MSG] = "未知的节点属性"
            return result
        if field_index == 10:  # pages
            process_result = process_pub_pages(driver)
            result[RESULT_MSG] = process_result.get(RESULT_MSG, "")
            result[RESULT_CODE] = process_result.get(RESULT_CODE, -286)
        else:
            result[RESULT_CODE] = -285
            result[RESULT_MSG] = "不能处理的节点属性"
    else:
        result[RESULT_CODE] = -283
        result[RESULT_MSG] = "不能处理的节点类型"
    return result


def process_pub_pages(driver):
    """
    对所有PUBLICATION节点的pages属性进行整理
    :return:
    """
    filter_field = "uuid"
    target_field = "pages"
    result = {RESULT_CODE: 0, RESULT_MSG: "", RESULT_DATA: ""}
    cypher = "match (n:{PUB}) return n".format(PUB=NODE_TYPES[0])
    with driver.session() as session:
        query_result = session.run(cypher)
        query_result = query_result.data()
    query_result = process_neo4j_result(query_result, "n", 1)
    if query_result[RESULT_MSG] < 0:
        result[RESULT_MSG] = "Publication的pages属性提取失败"
        result[RESULT_CODE] = -290
        return result
    processed_data = {}
    counter_all = len(query_result)
    if counter_all == 0:
        result[RESULT_CODE] = -291
        result[RESULT_MSG] = "没有PUBLICATION节点"
        return result
    counter_failed = 0
    for pub_item in query_result[RESULT_DATA]:
        pub_uuid = pub_item.get(filter_field, None)
        if pub_uuid is None:
            print(str(pub_item) + "->存在数据" + filter_field + "为空")
            continue
        pub_pages = pub_item.get(target_field, None)
        if pub_pages is None:
            print(str(pub_item) + "->缺少" + target_field + "字段")
            continue
        pub_pages = process_pages(pub_pages)
        if pub_pages is None:
            print(str(pub_item) + "->处理" + target_field + "字段失败")
            counter_failed += 1
            continue
        processed_data[pub_uuid] = pub_pages

    if counter_failed > 0:
        result[RESULT_CODE] = -292
        result[RESULT_MSG] = "存在pages字段处理失败的情况，取消处理"
        return result
    if processed_data == {}:
        result[RESULT_CODE] = 290
        result[RESULT_MSG] = "存在pages字段处理失败的情况，取消处理"
        return result
    # 修改字段
    counter_success = 0
    with driver.session() as session:
        for (key, value) in processed_data.items():
            field_match = {filter_field: key}
            field_value_revise = {target_field: value}
            revise_result = revise_node_by_fields(session, NODE_TYPES[0], field_match, field_value_revise)
            if revise_result[RESULT_CODE] != 200:
                print(str(key) + "," + str(value) + "->" + revise_result[RESULT_MSG])
                continue
            counter_success += 1
    if counter_success < len(processed_data.keys()):
        result[RESULT_CODE] = 291
        result[RESULT_MSG] = "部分处理成功，不成功部分请见日志"
    else:
        result['code'] = 292
        result[RESULT_MSG] = '全部处理成功'
    return result


if __name__ == "__main__":
    from configparser import ConfigParser
    import neo4j
    from neo4j import GraphDatabase

    file = "/Volumes/Transcend/web/utils/reference.bib"
    neo4j_config_file = "/Volumes/Transcend/web/web_pages/webs/neo4j.conf"

    cf = ConfigParser()
    cf.read(neo4j_config_file, encoding="utf-8")

    uri = cf.get("neo4j", "uri")
    neo4j_username = cf.get("neo4j", "username")
    neo4j_pwd = cf.get("neo4j", "pwd")

    driver0 = GraphDatabase.driver(uri, auth=neo4j.basic_auth(neo4j_username, neo4j_pwd))

    # 从文件中生成Publication节点
    result0 = generate_pub_node_from_file(driver0, file)
    print(str(result0))
    # # 从Publication节点中分析期刊信息，创建Venue节点并创建Publish_in边
    result0 = build_relation_from_node_attribute(driver0)
    print(str(result0))
    # 从Publication节点中分析人信息，创建Person节点并创建Author边
    result0 = build_relation_from_node_attribute(driver0, source_node_type="PERSON", target_node_type="PUBLICATION",
                                                rel_type="AUTHORED_BY", filters=None,
                                                info_field='author', use_source=False, do_split=True)
    print(str(result0))
