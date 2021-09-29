from neo4j import GraphDatabase
import neo4j
import uuid
import os
import time

from utils.bib_util.extraction import extract_publication_from_bib_info, extract_venue_from_bib_info, extract_person_from_bib_info
from utils.db_util.operations import query_or_create_node
from utils.nlp.text_utils import string_util
from utils.file_util.utils import parse_bib_file
from utils.initialization import ini_result, RESULT_CODE, RESULT_DATA


def revise_publications(driver, data):
    """
    从文件中提取文献信息，并建立节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid bibliography in the database')
        return -1

    with driver.session() as session:
        tmp = extract_publication_from_bib_info(data)  # 提取文献信息，构造节点

        if tmp[RESULT_CODE] != 1001:
            return -2
        else:
            tmp = revise_node(session, tmp[RESULT_DATA], data)  # 创建/更新节点
            if tmp is None:
                return -3
            return 1


def revise_persons(driver, data):
    """
    提取人信息，并修改节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid person info is given')
        return -1

    with driver.session() as session:
        node = extract_person_from_bib_info(data)  # 提取文献信息，构造节点
        if node is None or isinstance(node, int):
            return -2
        else:
            tmp = revise_node(session, node, data)  # 更新节点
            if tmp is None:
                return -3
            return 1


def revise_venues(driver, data):
    """
    提取人信息，并修改节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid venue info is given')
        return -1

    with driver.session() as session:
        node = extract_venue_from_bib_info(data)  # 提取文献信息，构造节点
        if node is None or isinstance(node, int):
            return -2
        else:
            tmp = revise_node(session, node, data)  # 更新节点
            if tmp is None:
                return -3
            return 1


def revise_node(tx, node, field_value_revise):
    """
    先查询节点是否存在，若存在，修改内容，否则，创建节点。-1表示出错
    :param tx:
    :param node:
    :param field_value_revise:
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

