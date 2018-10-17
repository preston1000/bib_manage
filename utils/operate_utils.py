import bibtexparser


def is_valid_key(entry, key):
    value = entry.get(key)
    if value is None:
        return None
    else:
        return value


def parse_bib_keys(entry):
    """
    将每个文献中的字段名称转成大写，并对应其在entry中的key
    :param entry:
    :return:
    """
    mapping = {}
    for (key, value) in entry.items():
        mapping[key.upper()] = key
    return mapping


def load_bib_file(file_name):
    """
    从bib文件中解析出文献信息
    :param file_name:
    :return:
    """
    with open(file_name, encoding="utf-8") as bib_file:
        bib_database = bibtexparser.load(bib_file)
    if bib_database is None:
        return None
    else:
        return bib_database