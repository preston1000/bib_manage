def is_valid_key(entry, key):
    value = entry.get(key)
    if value is None:
        return None
    else:
        return value


def key_2_upper(entry):
    """
    将每个文献中的字段名称转成大写，并对应其在entry中的key
    :param entry:
    :return:
    """
    mapping = {}
    for (key, value) in entry.items():
        mapping[key.upper()] = key
    return mapping


def merge_person():
    """
    todo 这个是合并网络中的人节点（有可能出现多个节点表示一个人）
    :return:
    """
    return
