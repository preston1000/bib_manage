"""
这个是重构db_operation的文件
"""
import time
import uuid

from neo4j import GraphDatabase
import neo4j

from utils.d_extraction import parse_bib

from utils.util_operation import ini_neo4j


def create_or_match_nodes(bib_data, database_info):
    """
    根据指定的文献信息，建立节点，若节点已存在，则不操作, 要返回新生成或查询到的节点的uuid，且要有对应关系（直接填到节点信息里）
    :param bib_data: 是Publication/Venue/Person类的list
    :param database_info: 数据库信息dict，包括URI，username，pwd，
    :return:
    """
    # 输入数据检查
    result = {"code": 0, "msg": "", "data": ""}
    if bib_data is None or not isinstance(bib_data, list):
        result["code"] = -1
        result["msg"] = "the given data is not of type list"
        return result
    if database_info is None:
        result["code"] = -2
        result["msg"] = "the database is not configured!"
        return result
    # 启动数据库
    driver = GraphDatabase.driver(database_info["uri"], auth=neo4j.basic_auth(database_info["username"], database_info["pwd"]))
    # 在数据库中查询数据
    bib_data_new = []
    with driver.session() as session:
        for entry in bib_data:
            tmp = query_or_create_node(session, entry, to_create=True, match_field=None)  # 查询或创建节点
            if tmp == -1:
                print("the bib " + entry.tostring() + " is not valid and can not be written into DB")
            else:
                entry.uuid = tmp
                bib_data_new.append(entry)
    # 查询结果分析
    if not bib_data_new:
        result["code"] = 0
        result["msg"] = "未查询到或新建任何节点"
        return result
    elif len(bib_data_new) < len(bib_data):
        result["code"] = 2
        result["msg"] = "Not all entries are written into DB"
        result["data"] = bib_data_new
        return result
    else:
        result["code"] = 1
        result["msg"] = "all entries have been written into DB"
        result["data"] = bib_data_new
        return result


def revise_node(tx, node, field_value_revise):
    """
    先查询节点是否存在，若存在，修改内容，否则，创建节点。-1表示出错 todo 还没改
    :param tx:
    :param node: 现有节点
    :param field_value_revise: 要修改的字段，dict
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


if __name__ == "__main__":
    # 从文件中解析文献，
    # flag, msg, info = parse_bib("bibtex.bib")
    flag, msg, info = parse_bib("/Users/X/Downloads/reference.bib")
    # 并创建节点
    database_info = ini_neo4j("/Volumes/Transcend/web/web_pages/webs/neo4j.conf")
    create_or_match_nodes(info)
    # # 从网络中解析文献节点，并提取journal信息，创建venue节点、[wenxian]->[publication]
    # build_network_of_venues(node_type="ARTICLE", publication_field="journal")
    # build_network_of_venues(node_type="inproceedings".upper(), publication_field="book_title")
    # # 从文献中解析author字段，创建Person节点、person->publication
    # build_network_of_persons()


def query_or_create_node(tx, node, to_create=True, match_field=None):
    """
    先查询节点是否存在，若存在，直接返回节点id，否则，创建节点并返回id。-1表示出错
    :param tx: neo4j连接
    :param node:节点信息，是models.py中定义的类
    :param to_create:当节点不在数据库中时是否创建新节点
    :param match_field:
    :return: 若查到数据，返回uuid，否则，若to_create为真，返回新建节点uuid，否则，返回0；出错返回-1
    """
    # 取回查询语句
    if node is None:
        return -1
    if match_field is None:
        cypher = node.get_match_cypher()
    else:
        cypher = node.get_match_cypher(match_field)
    # 查询数据库
    node_id = tx.run(cypher)
    # 分析结果
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
        return -1
    return 0


def query_or_create_relation(tx, source_type, source_id, target_type, target_id, relation_type, to_create=True, parameters=None):
    """
    先根据起终点的uuid查询关系是否存在，若存在，直接返回关系id，否则，创建关系并返回id。todo 设计边的属性，现在只有uuid和added_date
    :param relation_type:
    :param target_id:
    :param target_type:
    :param source_id:
    :param source_type:
    :param tx:
    :param to_create:
    :param parameters: dict，边属性
    :return: -1:参数不完整,1:已存在，-2：不存在，且不创建,-3:指定边属性无效，-4：创建失败，2：生成成功
    """
    result = {"code": -1, "msg": "", "data": ""}
    # 检查输入数据
    if source_type is None or source_id is None or target_id is None or target_type is None or relation_type is None:
        result["msg"] = "输入参数不完整"
        return result
    if tx is None:
        result["msg"] = "DB is not connected"
        return result
    # 生成查询语句
    cypher = "MATCH (s:{source}) -[r:{rel}]-> (t:{target}) where s.uuid='{IDs}' and t.uuid='{IDt}'  " \
             "return r.uuid" .format(source=source_type, target=target_type, IDs=source_id,
                                      IDt=target_id, rel=relation_type.upper())
    edges = tx.run(cypher)
    edges = edges.data()
    if len(edges) > 0:
        result["code"] = 1
        result["data"] = edges[0]["r.uuid"]
        result["msg"] = "{IDs}和{IDt}的{REL}关系已经存在{UUID}".format(IDs=source_id, IDt=target_id, REL=relation_type,
                                                               UUID=edges[0]["r.uuid"])
        print(result["msg"])
        return result
    if to_create:
        # 解析属性
        tmp_uuid = uuid.uuid1()
        added_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        cypher_cond = "{uuid:'" + tmp_uuid.hex + "', added_date:'" + added_date + "', "
        if parameters is not None and not isinstance(parameters, dict):
            result["code"] = -3
            result["msg"] = "指定边属性不是dict，取消生成节点"
            print(result["msg"])
            return result
        elif parameters is not None and isinstance(parameters, dict):
            # 生成查询语句
            for (key, value) in parameters.items():
                cypher_cond += "" + key + ":'" + str(value) + "', "
        cypher_cond = cypher_cond[:-2] + "}"
        cypher = "MATCH (s:{source}), (t:{target}) where s.uuid='{IDs}' and t.uuid='{IDt}' CREATE (s) -[r:{REL}{COND}]->(t) " \
                 "return r.uuid" .format(source=source_type, target=target_type, IDs=source_id,
                                          IDt=target_id, REL=relation_type.upper(), COND=cypher_cond)
        # 执行查询+生成过程
        edges = tx.run(cypher)
        edges = edges.data()
        if len(edges) > 0:
            result["code"] = 2
            result["data"] = edges[0]["r.uuid"]
            result["msg"] = "{IDs}和{IDt}的{REL}关系已创建{UUID}".format(IDs=source_id, IDt=target_id, REL=relation_type,
                                                                  UUID=edges[0]["r.uuid"])
            print(result["msg"])
            return result
        else:
            result["code"] = -4
            result["msg"] = "{IDs}和{IDt}的{REL}关系创建关系失败，数据库操作失败".format(IDs=source_id, IDt=target_id, REL=relation_type)
            return result
    else:
        result["code"] = -2
        result["msg"] = "数据库无记录，已选择不创建新节点"
        return result


