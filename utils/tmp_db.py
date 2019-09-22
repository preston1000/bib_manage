"""
这个是重构db_operation的文件
"""
from neo4j import GraphDatabase
import neo4j

from utils.inference_operations import query_or_create_node
from utils.d_extraction import parse_bib

from utils.util_operation import ini_neo4j


def create_or_match_nodes(bib_data, database_info):
    """
    根据指定的文献信息，建立节点，若节点已存在，则不操作
    :param bib_data: 是Publication类的list
    :param database_info: 数据库信息dict，包括URI，username，pwd，
    :return: -1:输入数据为空；1：处理成功；-2：提取文献信息失败；-3：写入数据库失败（可能全失败或部分失败）
    """
    if bib_data is None or ~isinstance(bib_data, list):
        return "the given data is not of type list"
    if database_info is None:
        return "the database is not configured!"
    driver = GraphDatabase.driver(database_info.uri, auth=neo4j.basic_auth(database_info.username, database_info.pwd))
    counter = 0
    with driver.session() as session:
        for entry in bib_data:
            tmp = query_or_create_node(session, entry)  # 创建/更新节点（更新未实现）
            if tmp is None:
                print("the bib " + entry.tostring() + " is not valid and can not be written into DB")
            else:
                counter = counter + 1
    if counter < len(bib_data):
        return "Not all entries are written into DB"
    return None


def revise_node(tx, node, field_value_revise):
    """
    先查询节点是否存在，若存在，修改内容，否则，创建节点。-1表示出错
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
