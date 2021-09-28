

"""
数据库操作
"""
from utils.bib_util.utils import split_pages, split_name
from utils.db_util.utils import generate_cypher_for_multi_field_condition, process_neo4j_result
from utils.nlp.text_utils import null_string, null_int


def ini_result():
    result = {"data": None, "code": 0, "msg": ""}
    return result


def query_one_pub_by_uuid(driver, pub_id):
    """
    利用Publication的uuid来查询其详情，todo 当前有多个匹配的时候，只选取第一个
    :param driver:
    :param pub_id:str, pub uuid
    :return:
    """
    result = ini_result()
    if driver is None or pub_id is None or not isinstance(pub_id, str):
        result["code"] = -901
        result["msg"] = "invalid arguments"
        return result

    # 查询是否存在数据
    cypher = "match (m:Publication {uuid:'" + pub_id + "'}) <-[r:Write]- (n:Person) return m, n"

    with driver.session() as session:
        records = session.run(cypher)
        records = records.data()

    if records is None or len(records) == 0:
        result["msg"] = "no matched data"
        result["code"] = 902
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

    result["msg"] = "success"
    result["code"] = 903
    result["data"] = pub

    return result


def query_bib_node_by_multiple_field(driver, node_type, node_info, page=None, limit=None):
    """
    利用Publication/venue/person的多个字段来进行查询，并对处理结果进行解析
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
        result["code"] = -901
        result["msg"] = "invalid arguments"
        return result

    identifier = "m"
    tmp = query_by_multiple_field(driver, node_info, node_type, page, limit, identifier)

    if tmp["code"] != 904:
        result["code"] = tmp["code"]
        result["msg"] = tmp["msg"]
        return result

    records = tmp["data"]

    result["code"] = 905
    result["msg"] = "success"

    if node_type in ["VENUE", "PERSON"]:
        result["data"] = records
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
    result["data"] = pubs
    return result


def query_by_multiple_field(driver, node_info, node_type, page=None, limit=None, identifier="m"):
    """
    通用方法：给予节点的一个或多个字段来搜索节点信息
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
        result["code"] = -901
        result["msg"] = "invalid arguments"
        return result

    # 查询条件
    cond = generate_cypher_for_multi_field_condition(node_info, node_type, identifier)
    if cond is None:
        result["code"] = -904
        result["msg"] = "No cypher has been generated"
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
        result["code"] = -910
        result["msg"] = "数据库连接失败"
        return result

    records = process_neo4j_result(records, identifier, flag=1)  # 用match时
    result["msg"] = "success"
    result["code"] = 904
    result["data"] = records
    if records is None:
        result["count"] = 0
    else:
        result["count"] = len(records)
    return result


def query_by_multiple_field_count(driver, node_info, node_type, identifier="m"):
    """
    通用方法：根据给定的节点信息，查询有多少条数据满足条件
    :param identifier:
    :param driver:
    :param node_info: dict
    :param node_type:数据库节点类型名
    :param parameter: 参数？未想好有什么用处
    :return:返回的是dict，其中code：-1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
    """

    result = ini_result()
    result["count"] = -1

    # 输入数据检测
    if driver is None or node_info is None or not isinstance(node_info, dict) or node_type is None or node_type not in ["PUBLICATION", "PERSON", "VENUE"]:
        result["code"] = -901
        result["msg"] = "invalid arguments"
        return result
    # 查询条件
    cond = generate_cypher_for_multi_field_condition(node_info, node_type, identifier)  # 指定的查询条件
    if cond is None:
        result["code"] = -904
        result["msg"] = "No cypher has been generated"
        return result

    cypher = "match ({IF}:{NODE_TYPE}) ".format(IF=identifier, NODE_TYPE=node_type) + cond + " return count({IF})".format(IF=identifier)

    # 查询数据库

    try:
        with driver.session() as session:
            records = session.run(cypher)
            records = records.data()
    except:
        result["code"] = -910
        result["msg"] = "数据库连接失败"
        return result

    result["msg"] = "success"
    result["code"] = 906

    if records is None or len(records) == 0:
        result["count"] = 0
    elif len(records) > 1:
        result["count"] = len(records)
    else:
        result["count"] = records[0]["count(m)"]
    return result


def query_person_pub_venue_by_person_name(driver, person_list, skip=None, limit=None):
    """
    利用person name来获取Publication、venue等数据，用来展示关系图
    :param limit:
    :param skip:
    :param person_list: list of person name
    :param driver:
    :return:
    """
    result = ini_result()
    if driver is None or person_list is None or not isinstance(person_list, list):
        result["code"] = -901
        result["msg"] = "invalid arguments"
        return result

    # 查询是否存在数据
    cypher_total = "match (n:Person)-[r:Write]->(m:Publication)  where n.name in " + str(person_list) + \
                   " return count(m)"
    with driver.session() as session:
        records = session.run(cypher_total)
        total = records.value()[0]

    if total == 0:  # no data found
        result["code"] = 901
        result["msg"] = "no matched data"
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
        result["code"] = -902
        result["msg"] = "failed to get matched data (Publication<-Write<-Person)"
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

    result["code"] = 900
    result["msg"] = "success"
    result["data"] = {"relation": relations, "nodes": nodes}

    return result


if __name__ == "__main__":
    # msg = sample_data("0", "10")
    # msg = query_vis_data()
    from neo4j import GraphDatabase
    import neo4j
    driver0 = GraphDatabase.driver('bolt://localhost:7687', auth=neo4j.basic_auth('neo4j', '123456'))
    msg0 = query_one_pub_by_uuid(driver0, "c0aaecba7da111e881f3a45e60c2e1a5")
    print(msg0)