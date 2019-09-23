def upperize_dict_keys(entry):
    """
    将每个文献中的字段名称转成大写，并对应其在entry中的key
    :param entry:
    :return:
    """
    mapping = {}
    for (key, value) in entry.items():
        mapping[key.upper()] = value
    return mapping
