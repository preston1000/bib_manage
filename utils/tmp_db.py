"""
这个是重构db_operation的文件 --- 是整理好的
"""

from utils.db_util.operations import create_or_match_nodes
from utils.file_util.utils import parse_bib_file
from utils.initialization import NODE_TYPES, FIELD_NAMES_PUB


def revise_node_by_class(tx, node, field_value_revise):
    """
    有封装好的models类，进行文献修改，先查询节点是否存在，若存在，修改内容，否则，返回错误代码
    :param tx:
    :param node: 现有节点
    :param field_value_revise: 要修改的字段，dict
    :return:
    """
    result = {"code": 0, "msg": "", "data": ""}
    if node is None:
        result["code"] = -190
        result["msg"] = "输入节点信息错误"
        return result
    cypher = node.get_match_cypher()
    if cypher is None:
        result["code"] = -191
        result["msg"] = "cypher for match获取失败"
        return result
    try:
        nodes = tx.run(cypher)
    except:
        result["code"] = -192
        result["msg"] = "数据库连接失败"
        return result
    nodes = nodes.data()
    if len(nodes) == 0:
        result["code"] = -193
        result["msg"] = "无匹配记录，无法修改"
        return result
    nodes = nodes[0]
    print("查询到了节点：" + str(nodes["node"]['uuid']) + "开始修改：")
    # 进行修改
    field_value_match = {"uuid": nodes["node"]['uuid']}
    cypher = node.get_revise_cypher(field_value_revise, field_value_match)
    try:
        node_revised = tx.run(cypher)
    except:
        result["code"] = -194
        result["msg"] = "数据库连接失败"
        return result
    node_revised = node_revised.data()
    node_revised = node_revised[0].get("node", None)
    if node_revised is None:
        result["code"] = -195
        result["msg"] = "修改失败"
        return result
    node_revised = node_revised.get("uuid", None)
    if node_revised is None:
        result["code"] = -194
        result["msg"] = "修改失败"
        return result
    result["code"] = 190
    result["msg"] = "修改成功"
    return result


def revise_node_by_fields(tx, node_type, field_match, field_value_revise):
    """
    根据指定的匹配字段，进行数据修改
    :param tx:
    :param node: 现有节点
    :param field_value_revise: 要修改的字段，dict
    :return:
    """
    result = {"code": 0, "msg": "", "data": ""}
    if field_match is None or not isinstance(field_match, dict) or field_match.keys() is None:
        result["code"] = -200
        result["msg"] = "输入匹配信息错误"
        return result

    if field_value_revise is None or not isinstance(field_value_revise, dict) or field_value_revise.keys() is None:
        result["code"] = -201
        result["msg"] = "输入更新信息错误"
        return result

    try:
        NODE_TYPES.index(node_type)
    except:
        result["code"] = -202
        result["msg"] = "节点类型指定错误"
        return result
    cypher = "MATCH (node:" + node_type + " {"
    for field, value in field_match.items():
        try:
            field_index = FIELD_NAMES_PUB.index(field)
        except:
            print(field + "<-不是可执行的字段名称")
            continue
        if field_index == 7:  # year
            cypher += field + ":" + str(value) + ","
        else:
            cypher += field + ":'" + str(value) + "',"
    cypher = cypher[:-1] + "}) set "
    for field, value in field_value_revise.items():
        if value is not None and value != '':
            if field == 'year':
                cypher += "node." + field + "=" + value + ","
            else:
                cypher += "node." + field + "='" + value + "',"
    cypher = cypher[:-1] + " return node"

    try:
        nodes = tx.run(cypher)
    except:
        result["code"] = -203
        result["msg"] = "数据库连接失败"
        return result
    nodes = nodes.data()
    if len(nodes) == 0:
        result["code"] = -204
        result["msg"] = "无匹配记录，无法修改"
        return result
    result["code"] = 200
    result["msg"] = "修改成功"
    return result


if __name__ == "__main__":
    from neo4j import GraphDatabase
    import neo4j
    from configparser import ConfigParser

    neo4j_config_file = "/Volumes/Transcend/web/web_pages/webs/neo4j.conf"

    cf = ConfigParser()
    cf.read(neo4j_config_file, encoding="utf-8")

    uri = cf.get("neo4j", "uri")
    neo4j_username = cf.get("neo4j", "username")
    neo4j_pwd = cf.get("neo4j", "pwd")

    driver = GraphDatabase.driver(uri, auth=neo4j.basic_auth(neo4j_username, neo4j_pwd))

    # 从文件中解析文献，
    # flag, msg, info = parse_bib("bibtex.bib")
    result0 = parse_bib_file("/Users/X/Downloads/reference.bib")
    if result0["code"] < 0:
        print(result0["msg"])
    # 并创建节点

    create_or_match_nodes(result0["data"], driver)
    # # 从网络中解析文献节点，并提取journal信息，创建venue节点、[wenxian]->[publication]
    # build_network_of_venues(node_type="ARTICLE", publication_field="journal")
    # build_network_of_venues(node_type="inproceedings".upper(), publication_field="book_title")
    # # 从文献中解析author字段，创建Person节点、person->publication
    # build_network_of_persons()

