from configparser import ConfigParser
from neo4j.v1 import GraphDatabase
import neo4j.v1
import json

from utils.util_text_operation import null_string, split_name, null_int

cf = ConfigParser()
cf.read("./neo4j.conf", encoding="utf-8")

uri = cf.get("neo4j", "uri")
username = cf.get("neo4j", "username")
pwd = cf.get("neo4j", "pwd")


def sample_data(skip=None, limit=None):
    """
    mode=1 : 用来查询"人--文献"的关系，用以生成表格
    mode=2 : 用来查询"人--文献--venue"的关系，用以生成图形
    :param skip:
    :param limit:
    :param mode:
    :return:
    """
    # 读取配置文件
    person_list = []
    members = cf.get("cpwlGroup", "members")
    members_cn = cf.get("cpwlGroup", "members_cn")

    person_list.extend(members.split(" and "))
    person_list.extend(members_cn.split(" and "))
    person_list = [item.upper() for item in person_list]

    # 初始化Neo4j数据库连接,及查询结果
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))

    # 查询是否存在数据
    cypher_total = "match (n:Person)-[r:Write]->(m:Publication)  where n.name in " + str(person_list) + \
                   " return count(m)"
    with driver.session() as session:
        records = session.run(cypher_total)
        total = records.value()[0]
    if total == 0:
        msg = {"code": -1,
               "msg": "no records",
               "count": 0,
               "data": ""}
    else:
        cypher = "match (n:Person)-[r:Write]->(m:Publication)  where n.name in " + str(person_list) + \
                 " return n, m, r order by m.year"
        if skip is not None:
            cypher += " skip " + str(skip) + " limit " + str(limit)
        with driver.session() as session:
            records = session.run(cypher)
            pubs = []
            count = 1
            for record in records:
                print("查询结果成功")
                # 组装结果
                venue = ""
                node_type = record["m"]["node_type"]
                if node_type == "ARTICLE":
                    venue = record["m"]["journal"]
                elif node_type == "INBOOK":
                    venue = record["m"]["chapter"]
                elif node_type == "INPROCEEDINGS" or node_type == "CONFERENCE" or node_type == "INCOLLECTION":
                    venue = record["m"]["book_title"]
                elif node_type == "PHDTHESIS":
                    venue = record["m"]["school"]
                elif node_type == "MASTERSTHESIS":
                    venue = record["m"]["school"]
                elif node_type == "TECHREPORT":
                    venue = record["m"]["institution"]
                pub = {"ID": count,
                       "TITLE": record["m"]["title"],
                       "AUTHORS": record["m"]["author"],
                       "VENUE": venue,
                       "YEAR": record["m"]["year"],
                       "VENUE_TYPE": node_type,
                       "uuid": record["m"]["uuid"]}
                count += 1
                pubs.append(pub)
            if count > 1:
                msg = {"code": 0,
                       "msg": "successfully queried publications",
                       "count": total,
                       "data": pubs}
            else:
                msg = {"code": -1,
                       "msg": "no records",
                       "count": 0,
                       "data": ""}
    return json.dumps(msg)


def query_one_pub_by_uuid(pub_id):
    """
    :param pub_id:pub uuid
    :return:
    """

    # 初始化Neo4j数据库连接,及查询结果
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))

    # 查询是否存在数据
    cypher = "match (m:Publication {uuid:'" + pub_id + "'}) <-[r:Write]- (n:Person) return m, n"

    msg = {"code": -1,
           "msg": "",
           "data": None}

    with driver.session() as session:
        records = session.run(cypher)
        records = records.data()
    if records is None or len(records) == 0:
        msg["msg"] = "no records"
        msg["code"] = 0
        return msg
    elif len(records) > 1:
        msg["msg"] = "more than one record. suppose that the publication has more than one author but not have " \
                     "duplicated records for the same publication"
        msg["code"] = 1
    else:
        msg["msg"] = "found one record"
        msg["code"] = 1

    pages = records[0]["m"]["pages"]
    page1 = None
    page2 = None

    # 处理页码
    if pages is not None and pages != "null" and pages != "":
        pages = str.split(pages, "-")
        tmp = [page.strip() for page in pages if page.strip() != ""]
        if len(tmp) == 2:
            page1 = tmp[0]
            page2 = tmp[1]
    # 处理author
    authors = [item["n"]["name"] for item in records]
    tmp = [split_name(name, authors) for name in authors]
    authors = tmp

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
    msg["data"] = pub

    return msg


def query_pub_by_multiple_field(pub_info, parameters=None):
    """
    :param pub_info:pub uuid
    :param parameters: 分页参数
    :return:-1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录，result={"data":, "code":}
    """
    # 根据提供的文献信息，查询数据库，并整理结果
    result = {"code": -1, "data": {}, "msg":""}
    tmp = query_by_multiple_field(pub_info, "PUBLICATION", parameters)
    result["code"] = tmp.get("code", -1)
    result["data"] = tmp.get("data", None)
    result["msg"] = tmp.get("msg", "")
    if result["code"] < 1:  # 没有搜索到数据或没有传入数据
        return json.dumps(result)
    pubs = []
    for record in result["data"]:
        pages = record["m"]["pages"]
        page1 = None
        page2 = None
        # 处理页码
        if pages is not None and pages != "null" and pages != "":
            pages = str.split(pages, "-")
            tmp = [page.strip() for page in pages if page.strip() != ""]
            if len(tmp) == 2:
                page1 = tmp[0]
                page2 = tmp[1]

        pub = {"paperTypeEdit": record["m"]["node_type"],
               "title": null_string(record["m"]["title"]),
               "booktitle": null_string(record["m"]["book_title"]),
               "author": null_string(record["m"]["author"]),
               "editor": null_string(record["m"]["editor"]),
               "keywords": null_string(record["m"]["keywords"]),
               "edition": null_string(record["m"]["edition"]),
               "year": null_int(record["m"]["year"]),
               "month": null_string(record["m"]["month"]),
               "journal": null_string(record["m"]["journal"]),
               "volume": null_string(record["m"]["volume"]),
               "type": null_string(record["m"]["type"]),
               "chapter": null_string(record["m"]["chapter"]),
               "number": null_string(record["m"]["number"]),
               "pages1": null_string(page1),
               "pages2": null_string(page2),
               "publisher": null_string(record["m"]["publisher"]),
               "organization": null_string(record["m"]["organization"]),
               "institution": null_string(record["m"]["institution"]),
               "school": null_string(record["m"]["school"]),
               "address": null_string(record["m"]["address"]),
               "series": null_string(record["m"]["series"]),
               "howpublished": null_string(record["m"]["how_published"]),
               "indexing": 0,
               "id": null_string(record["m"]["id"]),
               "uuid": null_string(record["m"]["uuid"]),
               "note": null_string(record["m"]["note"])}
        pubs.append(pub)
    result["data"] = pubs
    return json.dumps(result)


def query_person_or_venue_by_multiple_field(person_info, node_type):
    """
    :param person_info:dict of person info
    :return:-1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
    """
    # 根据提供的文献信息，查询数据库，并整理结果
    result = {"code": -1, "data": {}}
    tmp = query_by_multiple_field(person_info, node_type)
    result["code"] = tmp.get("code", -1)
    result["data"] = tmp.get("data", None)
    if result["code"] < 1:  # 没有搜索到数据或没有传入数据
        return json.dumps(result)
    nodes = []
    for record in result["data"]:
        record = record["m"]
        # nodes.append(record)
        node = {}
        for field, value in record.items():
            node[field] = value
        nodes.append(node)
    result["data"] = nodes
    return json.dumps(result)


def query_by_multiple_field(node_info, node_type, parameter=None):
    """
    通用方法：给予节点的一个或多个字段来搜索节点信息
    :param node_info: dict
    :param node_type:数据库节点类型名
    :param parameter: 分页参数
    :return:返回的是dict，其中code：-1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
    """
    # 输入数据检测
    msg = {"code": -1, "msg": "", "count": 0, "data": ""}
    if node_info is None or not isinstance(node_info, dict):
        msg["msg"] = "search conditions are not given"
        return msg
    # 查询条件
    cond = generate_cypher_for_multi_field_condition(node_info, node_type, 'm')
    paging = ""
    if not (parameter is None or not isinstance(parameter, dict)):
        page = parameter.get("page", None)
        limit = parameter.get("limit", None)
        if page is None or limit is None or not isinstance(page, int) or not isinstance(limit, int):
            print("分页参数不正确")
        else:
            paging = " skip " + str((page-1)*limit) + " limit " + str(limit)
    cypher = "match (m:{}) ".format(node_type) + cond + " return m " + paging

    # 查询数据库
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))  # 初始化Neo4j数据库连接,及查询结果
    with driver.session() as session:
        records = session.run(cypher)
        records = records.data()
    if records is None or len(records) == 0:
        msg["msg"] = "no records"
        msg["code"] = 0
    elif len(records) > 1:
        msg["msg"] = "more than one record. suppose that the publication has more than one author but not have " \
                     "duplicated records for the same publication"
        msg["code"] = 2
        msg["count"] = len(records)
        msg["data"] = records
    else:
        msg["msg"] = "found one record"
        msg["code"] = 1
        msg["count"] = len(records)
        msg["data"] = records
    return msg


def query_by_multiple_field_count(node_info, node_type, parameter=None):
    """
    通用方法：根据给定的节点信息，查询有多少条数据满足条件
    :param node_info: dict
    :param node_type:数据库节点类型名
    :param parameter: 参数？未想好有什么用处
    :return:返回的是dict，其中code：-1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
    """
    # 输入数据检测
    msg = {"code": -1,
           "msg": "",
           "count": 0}
    if node_info is None or not isinstance(node_info, dict):
        msg["msg"] = "search conditions are not given"
        return msg
    # 查询条件
    cond = generate_cypher_for_multi_field_condition(node_info, 'm')
    cypher = "match (m:{}) ".format(node_type) + cond + " return count(m)"

    # 查询数据库
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))  # 初始化Neo4j数据库连接,及查询结果
    with driver.session() as session:
        records = session.run(cypher)
        records = records.data()
    if records is None or len(records) == 0:
        msg["msg"] = "no records"
        msg["count"] = 0
        msg["code"] = 0
    elif len(records) > 1:
        msg["msg"] = "error!"
        msg["code"] = -1
        msg["count"] = len(records)
    else:
        msg["msg"] = "done!"
        msg["code"] = 1
        msg["count"] = records[0]["count(m)"]
    return msg


def generate_cypher_for_multi_field_condition(node_info, node_type, node_identifier):
    """
    根据节点的多个属性，设置查询条件
    :param node_info: dict，节点属性条件
    :param node_type: 节点类型，对不同的节点配置不同的可用参数以供查询
    :param node_identifier: str，查询语句中节点的标识符
    :return:
    """
    if node_type == 'VENUE':
        currently_supported_fields = ["venue_name"]
    elif node_type == 'PERSON':
        currently_supported_fields = []
    elif node_type == "PUBLICATION":
        currently_supported_fields = ["title", "node_type"]
    else:
        currently_supported_fields = []

    tmp = list(set(node_info.keys()).intersection(set(currently_supported_fields)))

    if tmp is None or len(tmp) == 0:
        cypher = ""
        print("no supported fields for search are given")
    else:
        cypher = "where "
        key_flag = 0
        for key, value in node_info.items():  # todo 对Publication：目前paperIndex和author还没加，venue：只有venue_name
            if key == "title":
                cypher += node_identifier + "." + key + " =~ '(?i).*" + value + ".*' and "
                key_flag += 1
            elif key == "node_type":
                cypher += node_identifier + "." + key + " = '" + value + "' and "
                key_flag += 1
            elif key == "startTime":
                cypher += node_identifier + ". year >= " + str(value) + " and "
                key_flag += 1
            elif key == "endTime":
                cypher += node_identifier + ". year <= " + str(value) + " and "
                key_flag += 1
            elif key == 'venue_name':
                cypher += node_identifier + "." + key + " =~ '(?i).*" + value + ".*' and "
                key_flag += 1
        if key_flag > 0:
            cypher = cypher[:-4]
        else:
            cypher = ""
            print("没有有效的key来查询{NODE}".format(NODE=node_type))
    return cypher


def query_vis_data():
    """
    用来展示关系图
    :param skip:
    :param limit:
    :return:
    """
    # 读取配置文件
    person_list = []
    members = cf.get("cpwlGroup", "members")
    members_cn = cf.get("cpwlGroup", "members_cn")

    person_list.extend(members.split(" and "))
    person_list.extend(members_cn.split(" and "))
    person_list = [item.upper() for item in person_list]

    # 初始化Neo4j数据库连接,及查询结果
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))

    # 查询是否存在数据
    cypher_total = "match (n:Person)-[r:Write]->(m:Publication)  where n.name in " + str(person_list) + \
                   " return count(m)"
    with driver.session() as session:
        records = session.run(cypher_total)
        total = records.value()[0]
    if total == 0:
        message = {"relation": "",
                   "nodes": "",
                   "status": 0}
    else:
        cypher = "match (m:Person)-[r:Write]->(n:Publication)  where m.name in " + str(person_list) + \
                 " return n, m"
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
        if nodes:
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

        if nodes:
            message = {"relation": relations,
                       "nodes": nodes,
                       "status": 1}
        else:
            message = {"relation": "",
                       "nodes": "",
                       "status": 0}
    return json.dumps(message)


if __name__ == "__main__":
    # msg = sample_data("0", "10")
    # msg = query_vis_data()
    msg = query_one_pub_by_uuid("c0aaecba7da111e881f3a45e60c2e1a5")
    print(msg)
