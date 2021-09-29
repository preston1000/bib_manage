

"""
数据库操作
"""
import time
import uuid

from utils.bib_util.utils import split_pages, split_name
from utils.db_util.utils import generate_cypher_for_multi_field_condition, process_neo4j_result
from utils.nlp.text_utils import null_string, null_int
from utils.initialization import ini_result, RESULT_CODE, RESULT_MSG, RESULT_DATA, NODE_TYPES, EDGE_TYPES


def query_one_pub_by_uuid(driver, pub_id):
    """
    利用Publication的uuid来查询其详情，checked，todo 当前有多个匹配的时候，只选取第一个
    :param driver:
    :param pub_id:str, pub uuid
    :return:
    """
    result = ini_result()
    if driver is None or pub_id is None or not isinstance(pub_id, str):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "invalid arguments"
        return result

    # 查询是否存在数据
    cypher = "match (m:Publication {uuid:'" + pub_id + "'}) <-[r:Write]- (n:Person) return m, n"

    with driver.session() as session:
        records = session.run(cypher)
        records = records.data()

    if records is None or len(records) == 0:
        result[RESULT_MSG] = "no matched data"
        result[RESULT_CODE] = 902
        return result

    # 处理特殊数据
    pages = records[0]["m"]["pages"]
    page1, page2 = split_pages(pages)

    # 处理author
    authors = [item["n"]["name"] for item in records]
    authors = [split_name(name, authors) for name in authors]

    pub = {"paperTypeEdit": records[0]["m"]["node_type"],
           "title": null_string(records[0]["m"]["title"]),
           "booktitle": null_string(records[0]["m"]["book_title"]),
           "author": authors,
           "editor": null_string(records[0]["m"]["editor"]),
           "keywords": null_string(records[0]["m"]["keywords"]),
           "edition": null_string(records[0]["m"]["edition"]),
           "year": null_string(records[0]["m"]["year"]),
           "month": null_string(records[0]["m"]["month"]),
           "journal": null_string(records[0]["m"]["journal"]),
           "volume": null_string(records[0]["m"]["volume"]),
           "type": null_string(records[0]["m"]["type"]),
           "chapter": null_string(records[0]["m"]["chapter"]),
           "number": null_string(records[0]["m"]["number"]),
           "pages1": null_string(page1),
           "pages2": null_string(page2),
           "publisher": null_string(records[0]["m"]["publisher"]),
           "organization": null_string(records[0]["m"]["organization"]),
           "institution": null_string(records[0]["m"]["institution"]),
           "school": null_string(records[0]["m"]["school"]),
           "address": null_string(records[0]["m"]["address"]),
           "series": null_string(records[0]["m"]["series"]),
           "howpublished": null_string(records[0]["m"]["how_published"]),
           "indexing": 0,
           "note": null_string(records[0]["m"]["note"])}

    result[RESULT_MSG] = "success"
    result[RESULT_CODE] = 903
    result[RESULT_DATA] = pub

    return result


def query_bib_node_by_multiple_field(driver, node_type, node_info, page=None, limit=None):
    """
    利用Publication/venue/person的多个字段来进行查询，并对处理结果进行解析。checked
    :param limit:
    :param page:
    :param node_type:
    :param driver:
    :param node_info:pub uuid
    :return:
    """
    # 根据提供的文献信息，查询数据库，并整理结果

    result = ini_result()

    if driver is None or node_info is None or not isinstance(node_info, dict) or node_type not in ["PUBLICATION", "PERSON", "VENUE"]:
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "invalid arguments"
        return result

    identifier = "m"
    tmp = query_by_multiple_field(driver, node_info, node_type, page, limit, identifier)

    if tmp[RESULT_CODE] != 904:
        result[RESULT_CODE] = tmp[RESULT_CODE]
        result[RESULT_MSG] = tmp[RESULT_MSG]
        return result

    records = tmp[RESULT_DATA]

    result[RESULT_CODE] = 905
    result[RESULT_MSG] = "success"

    if node_type in ["VENUE", "PERSON"]:
        result[RESULT_DATA] = records
        return result

    pubs = []
    for record in records:
        page1, page2 = split_pages(record["pages"])# 处理页码

        pub = {"node_type": record["node_type"],
               "book_title": null_string(record["book_title"]),
               "how_published": null_string(record["how_published"]),
               "title": null_string(record["title"]),
               "author": null_string(record["author"]),
               "editor": null_string(record["editor"]),
               "keywords": null_string(record["keywords"]),
               "edition": null_string(record["edition"]),
               "year": null_int(record["year"]),
               "month": null_string(record["month"]),
               "journal": null_string(record["journal"]),
               "volume": null_string(record["volume"]),
               "type": null_string(record["type"]),
               "chapter": null_string(record["chapter"]),
               "number": null_string(record["number"]),
               "pages1": null_string(page1),
               "pages2": null_string(page2),
               "publisher": null_string(record["publisher"]),
               "organization": null_string(record["organization"]),
               "institution": null_string(record["institution"]),
               "school": null_string(record["school"]),
               "address": null_string(record["address"]),
               "series": null_string(record["series"]),
               "indexing": 0,
               "id": null_string(record["id"]),
               "uuid": null_string(record["uuid"]),
               "note": null_string(record["note"])}
        pubs.append(pub)
    result[RESULT_DATA] = pubs
    return result


def query_by_multiple_field(driver, node_info, node_type, page=None, limit=None, identifier="m"):
    """
    通用方法：给予节点的一个或多个字段来搜索节点信息。checked
    :param identifier:
    :param limit:
    :param page:
    :param driver: 数据库信息
    :param node_info: dict
    :param node_type:数据库节点类型名
    :return:返回的是dict，其中code：-1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
    """
    # 输入数据检测
    result = ini_result()
    # 输入数据检查
    if driver is None or node_info is None or not isinstance(node_info, dict) or \
            (page is not None and not isinstance(page, int)) or (limit is not None and not isinstance(limit, int)):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "invalid arguments"
        return result

    # 查询条件
    cond = generate_cypher_for_multi_field_condition(node_info, node_type, identifier)
    if cond is None:
        result[RESULT_CODE] = -904
        result[RESULT_MSG] = "No cypher has been generated"
        return result

    if page is not None and limit is not None:
        paging = " skip " + str((page-1)*limit) + " limit " + str(limit)

    cypher = "match ({IF}:{NODE_TYPE}) ".format(IF=identifier, NODE_TYPE=node_type) + cond + " return " + identifier + " " + paging
    # 查询数据库

    try:
        with driver.session() as session:
            records = session.run(cypher)
            records = records.data()
    except:
        result[RESULT_CODE] = -910
        result[RESULT_MSG] = "数据库连接失败"
        return result

    records = process_neo4j_result(records, identifier, flag=1)  # 用match时
    result[RESULT_MSG] = "success"
    result[RESULT_CODE] = 904
    result[RESULT_DATA] = records
    if records is None:
        result["count"] = 0
    else:
        result["count"] = len(records)
    return result


def query_by_multiple_field_count(driver, node_info, node_type, identifier="m"):
    """
    通用方法：根据给定的节点信息，查询有多少条数据满足条件。checked
    :param identifier:
    :param driver:
    :param node_info: dict
    :param node_type:数据库节点类型名
    :return:返回的是dict，其中code：-1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
    """

    result = ini_result()
    result["count"] = -1

    # 输入数据检测
    if driver is None or node_info is None or not isinstance(node_info, dict) or node_type is None or node_type not in ["PUBLICATION", "PERSON", "VENUE"]:
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "invalid arguments"
        return result
    # 查询条件
    cond = generate_cypher_for_multi_field_condition(node_info, node_type, identifier)  # 指定的查询条件
    if cond is None:
        result[RESULT_CODE] = -904
        result[RESULT_MSG] = "No cypher has been generated"
        return result

    cypher = "match ({IF}:{NODE_TYPE}) ".format(IF=identifier, NODE_TYPE=node_type) + cond + " return count({IF})".format(IF=identifier)

    # 查询数据库

    try:
        with driver.session() as session:
            records = session.run(cypher)
            records = records.data()
    except:
        result[RESULT_CODE] = -910
        result[RESULT_MSG] = "数据库连接失败"
        return result

    result[RESULT_MSG] = "success"
    result[RESULT_CODE] = 906

    if records is None or len(records) == 0:
        result["count"] = 0
    elif len(records) > 1:
        result["count"] = len(records)
    else:
        result["count"] = records[0]["count(m)"]
    return result


def query_person_pub_venue_by_person_name(driver, person_list, skip=None, limit=None):
    """
    利用person name来获取Publication、venue等数据，用来展示关系图。checked
    :param limit:
    :param skip:
    :param person_list: list of person name
    :param driver:
    :return:
    """
    result = ini_result()
    if driver is None or person_list is None or not isinstance(person_list, list):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "invalid arguments"
        return result

    # 查询是否存在数据
    cypher_total = "match (n:Person)-[r:Write]->(m:Publication)  where n.name in " + str(person_list) + \
                   " return count(m)"
    with driver.session() as session:
        records = session.run(cypher_total)
        total = records.value()[0]

    if total == 0:  # no data found
        result[RESULT_CODE] = 901
        result[RESULT_MSG] = "no matched data"
        return result

    # get details of matched Publication and Person
    cypher = "match (m:Person)-[r:Write]->(n:Publication)  where m.name in " + str(person_list) + \
             " return n, m order by n.year"

    if skip is not None:
        cypher += " skip " + str(skip) + " limit " + str(limit)

    nodes = []
    node_ids = []
    relations = []
    with driver.session() as session:
        records = session.run(cypher)
        for record in records:
            print("查询person-->publication结果成功")
            # 组装结果
            if record["m"]["uuid"] not in node_ids:
                node = {"id": record["m"]["uuid"],
                        "label": record["m"]["name"],
                        "type": "person"}
                nodes.append(node)
                node_ids.append(record["m"]["uuid"])
            if record["n"]["uuid"] not in node_ids:
                node = {"id": record["n"]["uuid"],
                        "label": record["n"]["title"],
                        "type": "publication"}
                nodes.append(node)
                node_ids.append(record["n"]["uuid"])
            relation = {"from": record["m"]["uuid"],
                        "to": record["n"]["uuid"]}
            relations.append(relation)

    if not nodes:
        result[RESULT_CODE] = -902
        result[RESULT_MSG] = "failed to get matched data (Publication<-Write<-Person)"
        return result

    # get details of matched Publication and Venue
    cypher = "match (m:Publication)-[r:PUBLISH_IN]->(n:Venue)  where m.uuid in " + str(node_ids) + \
             " return n, m"

    with driver.session() as session:
        records = session.run(cypher)
        for record in records:
            print("查询publication-->venue结果成功")
            # 组装结果
            if record["m"]["uuid"] not in node_ids:
                node = {"id": record["m"]["uuid"],
                        "label": record["m"]["title"],
                        "type": "publication"}
                nodes.append(node)
                node_ids.append(record["m"]["uuid"])
            if record["n"]["uuid"] not in node_ids:
                node = {"id": record["n"]["uuid"],
                        "label": record["n"]["venue_name"],
                        "type": "venue"}
                nodes.append(node)
                node_ids.append(record["n"]["uuid"])
            relation = {"from": record["m"]["uuid"],
                        "to": record["n"]["uuid"]}
            relations.append(relation)

    result[RESULT_CODE] = 900
    result[RESULT_MSG] = "success"
    result[RESULT_DATA] = {"relation": relations, "nodes": nodes}

    return result


if __name__ == "__main__":
    # msg = sample_data("0", "10")
    # msg = query_vis_data()
    from neo4j import GraphDatabase
    import neo4j
    driver0 = GraphDatabase.driver('bolt://localhost:7687', auth=neo4j.basic_auth('neo4j', '123456'))
    msg0 = query_one_pub_by_uuid(driver0, "c0aaecba7da111e881f3a45e60c2e1a5")
    print(msg0)


def create_or_match_nodes(driver, node_list, return_type="class", to_create=True):
    """
    根据指定的数据信息，建立节点，若节点已存在，则不操作, 要返回新生成或查询到的节点的，且要有对应关系（直接填到节点信息里）.checked
    :param node_list: 是Publication/Venue/Person类的list
    :param driver: 数据库信息
    :param return_type:class/dict
    :param to_create: 查询后若没有记录，是否新建
    :return:list of Publication/Venue/Person
    """
    # 输入数据检查
    result = ini_result()

    if node_list is None or not isinstance(node_list, list) or len(node_list) == 0:
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "the given data is not of type list"
        return result

    if driver is None:
        result[RESULT_CODE] = -500
        result[RESULT_MSG] = "the database is not configured!"
        return result

    if return_type != 'class' and return_type != "dict":
        result[RESULT_CODE] = -1300
        result[RESULT_MSG] = "返回值类型指定错误!"
        return result

    # 在数据库中查询数据
    counter_processed = 0
    has_failed = False
    bib_data_new = []
    try:
        with driver.session() as session:
            for entry in node_list:
                query_result = query_or_create_node(session, entry, to_create=to_create, match_field=None)  # 查询或创建节点,返回是list of dict
                if query_result[RESULT_CODE] not in [1301, 1302]:
                    print(query_result[RESULT_MSG])
                    has_failed = True
                else:
                    counter_processed += 1
                    result_content = query_result[RESULT_DATA][0]  # todo 有多个的时候怎么办
                    if return_type == 'class':  # todo 这里要
                        entry.uuid = result_content["uuid"]
                        bib_data_new.append(entry)
                    elif return_type == 'dict':
                        bib_data_new.append(result_content)
    except:
        result[RESULT_CODE] = -910
        result[RESULT_MSG] = "数据库连接失败"
        return result
    # 查询结果分析
    if has_failed:
        result[RESULT_CODE] = -1304
        result[RESULT_MSG] = "查询/新建节点出现错误"
    else:
        result[RESULT_CODE] = 1303
        result[RESULT_MSG] = "成功"
        result[RESULT_DATA] = bib_data_new
    return result


def query_or_create_node(tx, node, to_create=True, match_field=None):
    """
    先查询节点是否存在，若存在，直接返回节点所有字段，否则，创建节点并返回所有数据。checked
    :param tx: neo4j连接
    :param node:节点信息，是models.py中定义的类
    :param to_create:当节点不在数据库中时是否创建新节点
    :param match_field: 用来匹配数据库中记录的条件，dict
    :return: 若查到数据，返回uuid，否则，若to_create为真，返回新建节点uuid，否则，返回0；出错返回-1
    """
    # 取回查询语句
    result = ini_result()
    if tx is None or node is None:
        result["code"] = -901
        result["msg"] = "未提供数据查询/新建节点或未提供数据库信息"
        return result

    if match_field is None:  # 利用默认的mandatory field来进行搜索
        cypher = node.get_match_cypher()
    else:
        if not isinstance(match_field, dict):
            result["code"] = -901
            result["msg"] = "提供查询的条件格式错误"
            return result
        else:
            cypher = node.get_match_cypher(match_field)  # todo 暂未实现
    # 查询数据库
    try:
        nodes = tx.run(cypher)
    except:
        result["code"] = -910
        result["msg"] = "数据库连接错误"
        return result

    nodes = nodes.data()
    # 分析结果
    if nodes is not None and len(nodes) > 0:
        tmp = process_neo4j_result(nodes, "node", 1)
        if tmp is not None:
            result["data"] = tmp
            result["code"] = 1301
            result["msg"] = "查询成功，有" + str(len(tmp["data"])) + "个匹配节点："
        else:
            result["code"] = -1301
            result["msg"] = "异常！"
        return result

    if not to_create:
        result["code"] = 1300
        result["msg"] = "查询成功，无记录，且不创建新节点"
        return result

    node.uuid = uuid.uuid1()
    node.added_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    create_cypher = node.get_create_cypher()
    try:
        nodes = tx.run(create_cypher)
    except:
        result["code"] = -910
        result["msg"] = "查询无记录，创建过程中数据库连接失败！"
        return result

    if nodes is None:
        result["code"] = -1303
        result["msg"] = "创建失败！"
        return result

    if len(nodes) > 1:
        result["code"] = -1302
        result["msg"] = "异常！"
        return result

    tmp = process_neo4j_result(nodes, "node", 2)
    if tmp is not None:
        result["data"] = tmp
        result["code"] = 152
        result["msg"] = "查询无记录，创建成功！"
    else:
        result["code"] = -1301
        result["msg"] = "异常！"

    return result


def query_or_create_relation(driver, source_type, source_id, target_type, target_id, relation_type, to_create=True, parameters=None):
    """
    先根据起终点的uuid查询关系是否存在，若存在，直接返回关系id，否则，创建关系并返回id。todo 设计边的属性，现在只有uuid和added_date
    :param relation_type:
    :param target_id:
    :param target_type:
    :param source_id:
    :param source_type:
    :param driver:
    :param to_create:
    :param parameters: dict，边属性
    :return: -1:参数不完整,1:已存在，-2：不存在，且不创建,-3:指定边属性无效，-4：创建失败，2：生成成功
    """
    result = ini_result()
    # 检查输入数据
    if source_type is None or source_id is None or target_id is None or target_type is None or relation_type is None:
        result["code"] = -901
        result["msg"] = "输入参数不完整"
        return result
    if source_type not in NODE_TYPES or source_type not in NODE_TYPES or target_type not in NODE_TYPES or target_type not in NODE_TYPES:
        result[RESULT_CODE] = -1202
        result[RESULT_MSG] = "node type is not valid"
        return result

    if relation_type not in EDGE_TYPES:
        result[RESULT_CODE] = -1203
        result[RESULT_MSG] = "edge type is not valid"
        return result

    if parameters is not None and not isinstance(parameters, dict):
        result["code"] = -901
        result["msg"] = "指定边属性不是dict，取消生成节点"
        return result

    # 生成查询语句
    cypher = "MATCH (s:{source}) -[r:{rel}]-> (t:{target}) where s.uuid='{IDs}' and t.uuid='{IDt}'  " \
             "return r" .format(source=source_type, target=target_type, IDs=source_id,
                                      IDt=target_id, rel=relation_type.upper())
    try:
        with driver.session() as session:
            edges = session.run(cypher)
    except:
        result["code"] = -910
        result["msg"] = "数据库连接失败"
        return result

    edges = edges.data()
    if len(edges) > 0:
        tmp = process_neo4j_result(edges, "r", 1)
        if tmp is None:
            result["code"] = -1305
            result["msg"] = "边查询成功，但结果处理失败"
        else:
            result["code"] = 1304
            result["data"] = tmp
            result["msg"] = "{IDs}和{IDt}的{REL}关系已经存在".format(IDs=source_id, IDt=target_id, REL=relation_type)
        return result

    if to_create:
        # 解析属性
        tmp_uuid = uuid.uuid1()
        added_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        cypher_cond = "{uuid:'" + tmp_uuid.hex + "', added_date:'" + added_date + "', "
        if parameters is not None:  # 生成查询语句
            for (key, value) in parameters.items():
                cypher_cond += "" + key + ":'" + str(value) + "', "
        cypher_cond = cypher_cond[:-2] + "}"
        cypher = "MATCH (s:{source}), (t:{target}) where s.uuid='{IDs}' and t.uuid='{IDt}' CREATE (s) -[r:{REL}{COND}]->(t) " \
                 "return r" .format(source=source_type, target=target_type, IDs=source_id,
                                          IDt=target_id, REL=relation_type.upper(), COND=cypher_cond)
        # 执行查询+生成过程
        try:
            with driver.session() as session:
                edges = session.run(cypher)
        except:
            result["code"] = -910
            result["msg"] = "数据库连接失败"
            return result

        edges = edges.data()
        if len(edges) > 0:
            tmp = process_neo4j_result(edges, "r", 2)
            if tmp is None:
                result["code"] = -1305
                result["msg"] = "边新建成功，但结果处理失败"
            else:
                result["code"] = 1306
                result["data"] = tmp
                result["msg"] = "{IDs}和{IDt}的{REL}关系创建成功".format(IDs=source_id, IDt=target_id, REL=relation_type)

        else:
            result["code"] = -1306
            result["msg"] = "{IDs}和{IDt}的{REL}关系创建关系失败，数据库操作失败".format(IDs=source_id, IDt=target_id, REL=relation_type)

    else:
        result["code"] = 1305
        result["msg"] = "数据库无记录，已选择不创建新节点"
    return result