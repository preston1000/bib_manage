

"""
为支撑数据库操作所需完成的基本动作
"""


def generate_cypher_for_multi_field_condition(node_info, node_type, node_identifier="m"):
    """
    根据节点的多个属性，设置查询条件， todo 增加条件
        Publication：仅支持node_type, title, year(start_year, end_year),不支持paperIndex和author
        venue：仅支持venue_name
    :param node_info: dict，节点属性条件
    :param node_type: 节点类型，对不同的节点配置不同的可用参数以供查询
    :param node_identifier: str，查询语句中节点的标识符
    :return: str："" 或查询语句
    """
    if node_type == 'VENUE':  # todo 定义配置文件
        currently_supported_fields = ["venue_name"]
    elif node_type == 'PERSON':
        currently_supported_fields = []
    elif node_type == "PUBLICATION":
        currently_supported_fields = ["title", "node_type"]
    else:
        currently_supported_fields = []

    tmp = list(set(node_info.keys()).intersection(set(currently_supported_fields)))

    if tmp is None or len(tmp) == 0:
        print("no supported fields for search are given")
        return None

    cypher = "where "
    key_flag = 0
    for key, value in node_info.items():
        if key not in currently_supported_fields:
            continue

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

    cypher = cypher[:-4]
    return cypher


def process_neo4j_result(data, identifier, flag):
    """
    checked
    :param data:
    :param identifier:
    :param flag, 1返回为数组时，用match，2：返回为dict时，用create
    :return: dict格式
    """
    if data is None:
        return None
    processed = []
    if flag == 1:
        for item in data:
            tmp = {}
            for (key, value) in item[identifier].items():  # todo 对不对？
                tmp[key] = value
            processed.append(tmp)
    else:  # create
        for item in data:
            tmp = {}
            for (key, value) in item.items():  # todo 对不对？
                tmp[key] = value
            processed.append(tmp)

    if not processed:
        processed = None

    return processed