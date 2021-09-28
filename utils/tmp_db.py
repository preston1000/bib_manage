"""
这个是重构db_operation的文件 --- 是整理好的
"""
import time
import uuid
from neo4j import GraphDatabase
import neo4j
from utils.d_extraction import extract_publication
from utils.file_util.utils import parse_bib_file
from utils.util_operation import ini_neo4j
from utils.db_util.utils import process_neo4j_result
from utils.constants import GlobalVariables


node_types = GlobalVariables.const_node_type
edge_types = GlobalVariables.const_edge_tpe
field_names = GlobalVariables.const_field_name


def create_or_match_nodes_dict(bib_data, node_type, database_info, return_type='class', to_create=True):
    """
    todo not recorded in doc for error code
    :param bib_data:
    :param node_type:
    :param database_info:
    :param return_type:
    :param to_create:
    :return: code 【需要兼容extract_publication的错误码， 1， -2， -3】
    """
    result = {"data": "", "msg": "", "code": 0}
    # 把dict组装成Publication类
    if node_type == 'PUBLICATION':
        query_result = extract_publication(bib_data)
        if query_result["code"] < 1:
            result = query_result
            return result
        else:
            bib_data = [query_result["data"]]
        result = create_or_match_nodes(bib_data, database_info, return_type, to_create)
        return result
    else:
        result["code"] = -1
    return result


def create_or_match_nodes(bib_data, database_info, return_type="class", to_create=True):
    """
    根据指定的数据信息，建立节点，若节点已存在，则不操作, 要返回新生成或查询到的节点的，且要有对应关系（直接填到节点信息里）
    :param bib_data: 是Publication/Venue/Person类的list
    :param database_info: 数据库信息dict，包括URI，username，pwd，
    :param return_type:class/dict
    :param to_create: 查询后若没有记录，是否新建
    :return:list of Publication/Venue/Person
    """
    # 输入数据检查
    result = {"code": 0, "msg": "", "data": ""}
    if bib_data is None or not isinstance(bib_data, list) or len(bib_data) == 0:
        result["code"] = -140
        result["msg"] = "the given data is not of type list"
        return result
    if database_info is None:
        result["code"] = -141
        result["msg"] = "the database is not configured!"
        return result
    else:
        uri = database_info.get("uri", None)
        user_name = database_info.get("username", None)
        pwd = database_info.get("pwd", None)
        if uri is None or user_name is None or pwd is None:
            result["code"] = -142
            result["msg"] = "数据库信息不完整"
            return result
    if return_type != 'class' and return_type != "dict":
        result["code"] = -143
        result["msg"] = "返回值类型指定错误!"
        return result
    # 启动数据库
    driver = GraphDatabase.driver(uri, auth=neo4j.basic_auth(user_name, pwd))
    # 在数据库中查询数据
    counter_all = len(bib_data)
    counter_processed = 0
    has_failed = False
    bib_data_new = []
    with driver.session() as session:
        for entry in bib_data:
            query_result = query_or_create_node(session, entry, to_create=to_create, match_field=None)  # 查询或创建节点,返回是list of dict
            if query_result["code"] < 0:
                print(query_result["msg"])
                has_failed = True
            elif query_result["code"] == 150:
                print(query_result["msg"])
            else:
                counter_processed += 1
                result_content = query_result["data"][0]  # todo 有多个的时候怎么办
                if return_type == 'class':  # todo 这里要
                    entry.uuid = result_content["uuid"]
                    bib_data_new.append(entry)
                elif return_type == 'dict':
                    bib_data_new.append(result_content)
    # 查询结果分析
    if has_failed:
        result["code"] = -144
        result["msg"] = "过程中查询/新建过程出现错误，数据不完整"
    else:
        result["code"] = 140
        result["msg"] = "成功"
        result["data"] = bib_data_new
    return result


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
        node_types.index(node_type)
    except:
        result["code"] = -202
        result["msg"] = "节点类型指定错误"
        return result
    cypher = "MATCH (node:" + node_type + " {"
    for field, value in field_match.items():
        try:
            field_index = field_names.index(field)
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


def query_or_create_node(tx, node, to_create=True, match_field=None):
    """
    先查询节点是否存在，若存在，直接返回节点所有字段，否则，创建节点并返回所有数据。
    :param tx: neo4j连接
    :param node:节点信息，是models.py中定义的类
    :param to_create:当节点不在数据库中时是否创建新节点
    :param match_field: 用来匹配数据库中记录的条件，dict
    :return: 若查到数据，返回uuid，否则，若to_create为真，返回新建节点uuid，否则，返回0；出错返回-1
    """
    # 取回查询语句
    result = {"data": "", "msg": "", "code": 0}
    if node is None:
        result["code"] = -150
        result["msg"] = "未提供数据查询/新建节点"
        return result
    if match_field is None:
        cypher = node.get_match_cypher()
    else:
        if not isinstance(match_field, dict):
            result["code"] = -151
            result["msg"] = "提供查询的条件格式错误"
            return result
        else:
            cypher = node.get_match_cypher(match_field)
    # 查询数据库
    try:
        nodes = tx.run(cypher)
    except:
        result["code"] = -152
        result["msg"] = "数据库连接错误"
        return result
    nodes = nodes.data()
    # 分析结果
    if nodes is None or len(nodes) == 0:
        result["code"] = 150
        result["msg"] = "查询成功，无记录，且不创建新节点"
    else:
        tmp = process_neo4j_result(nodes, "node", 1)
        if tmp["code"] > 0:
            result["data"] = tmp["data"]
            result["code"] = 151
            result["msg"] = "查询成功，有" + str(len(tmp["data"])) + "个匹配节点："
            result["count"] = len(tmp)
        else:
            result["code"] = -153
            result["msg"] = "查询成功,但查询数据处理失败！"
        print(result["msg"])
        return result
    if to_create:
        node.uuid = uuid.uuid1()
        node.added_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        create_cypher = node.get_create_cypher()
        try:
            nodes = tx.run(create_cypher)
        except:
            result["code"] = -154
            result["msg"] = "查询无记录，创建过程中数据库连接失败！"
            return result
        for record in nodes:
            tmp = process_neo4j_result(record, "node", 2)
            if tmp["code"] > 0:
                result["data"] = tmp["data"]
                result["code"] = 152
                result["msg"] = "查询无记录，创建成功！"
                result["count"] = 1
            else:
                result["code"] = -153
                result["msg"] = "查询无记录，创建成功，但数据解析失败！"
            break
    return result


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
        result["code"] = -170
        result["msg"] = "输入参数不完整"
        return result
    try:
        node_types.index(source_type)
        node_types.index(target_type)
    except:
        result["code"] = -171
        result["msg"] = "起终点类型不符合要求"
        return result
    try:
        edge_types.index(relation_type)
    except:
        result["code"] = -172
        result["msg"] = "边类型不符合要求"
        return result
    if parameters is not None and not isinstance(parameters, dict):
        result["code"] = -175
        result["msg"] = "指定边属性不是dict，取消生成节点"
        return result
    # 生成查询语句
    cypher = "MATCH (s:{source}) -[r:{rel}]-> (t:{target}) where s.uuid='{IDs}' and t.uuid='{IDt}'  " \
             "return r" .format(source=source_type, target=target_type, IDs=source_id,
                                      IDt=target_id, rel=relation_type.upper())
    try:
        edges = tx.run(cypher)
    except:
        result["code"] = -173
        result["msg"] = "数据库连接失败"
        return result
    edges = edges.data()
    if len(edges) > 0:
        tmp = process_neo4j_result(edges, "r", 1)
        if tmp["code"] < 0:
            result["code"] = -174
            result["msg"] = "边查询成功，但结果处理失败"
        else:
            result["code"] = 170
            result["data"] = tmp["data"]
            result["msg"] = "{IDs}和{IDt}的{REL}关系已经存在".format(IDs=source_id, IDt=target_id, REL=relation_type)
        print(result["msg"])
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
            edges = tx.run(cypher)
        except:
            result["code"] = -176
            result["msg"] = "数据库连接失败"
            return result

        edges = edges.data()
        if len(edges) > 0:
            tmp = process_neo4j_result(edges, "r", 2)
            if tmp["code"] < 0:
                result["code"] = -177
                result["msg"] = "边新建成功，但结果处理失败"
            else:
                result["code"] = 171
                result["data"] = tmp["data"]
                result["msg"] = "{IDs}和{IDt}的{REL}关系已经存在".format(IDs=source_id, IDt=target_id, REL=relation_type)
            print(result["msg"])
            return result
        else:
            result["code"] = -178
            result["msg"] = "{IDs}和{IDt}的{REL}关系创建关系失败，数据库操作失败".format(IDs=source_id, IDt=target_id, REL=relation_type)
            return result
    else:
        result["code"] = 172
        result["msg"] = "数据库无记录，已选择不创建新节点"
        return result


if __name__ == "__main__":
    # 从文件中解析文献，
    # flag, msg, info = parse_bib("bibtex.bib")
    result = parse_bib_file("/Users/X/Downloads/reference.bib")
    if result["code"] < 0:
        print(result["msg"])
    # 并创建节点
    database_info = ini_neo4j("/Volumes/Transcend/web/web_pages/webs/neo4j.conf")
    create_or_match_nodes(result["data"], database_info)
    # # 从网络中解析文献节点，并提取journal信息，创建venue节点、[wenxian]->[publication]
    # build_network_of_venues(node_type="ARTICLE", publication_field="journal")
    # build_network_of_venues(node_type="inproceedings".upper(), publication_field="book_title")
    # # 从文献中解析author字段，创建Person节点、person->publication
    # build_network_of_persons()

