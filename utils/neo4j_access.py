from neo4j.v1 import GraphDatabase
import bibtexparser
import neo4j.v1
import uuid
from configparser import ConfigParser


cf = ConfigParser()
# cf.read("./neo4j.conf", encoding="utf-8")
cf.read("E:\\projects\\web_pages\\webs\\neo4j.conf", encoding="utf-8")

uri = cf.get("neo4j", "uri")
username = cf.get("neo4j", "username")
pwd = cf.get("neo4j", "pwd")


def build_network_of_publications(data_source='bibtex.bib', mode=1, is_list=False):
    """
    从文件中提取文献信息，并建立节点
    :param data_source: 若mode=1，则问文件名；若mode=2，则为pub信息list of dict or dict
    :param mode: 1：从文件中读取；2：给定pub的dict信息
    :param is_list: true：有多个文献的list；false：只有一个文献，是dict
    :return:
    """
    if mode == 1:
        bib_data = load_data(data_source)
        bib_data = bib_data.entries
    else:
        if is_list:
            bib_data = data_source
        else:
            bib_data = [data_source]

    if bib_data is None or bib_data == []:
        print('No valid bibliography in the database')
        return -1
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        # tx = session.begin_transaction()
        flag = 1
        for entry in bib_data:
            node = extract_publication(entry)  # 提取文献信息，构造节点
            if node is None or isinstance(node, int):
                flag = -2
            else:
                tmp = query_or_create_node(session, node)  # 创建/更新节点（更新未实现）
                if tmp is None:
                    flag = -1
    return flag


def revise_publications(data):
    """
    从文件中提取文献信息，并建立节点
    :param data: 要修改的文献信息，dict
    :return:-1:输入数据无效；-2：无法解析输入数据；-3：无法插入数据库;1:修改成功
    """
    if data is None or data == []:
        print('No valid bibliography in the database')
        return -1
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        node = extract_publication(data)  # 提取文献信息，构造节点
        if node is None or isinstance(node, int):
            return -2
        else:
            tmp = revise_node(session, node, data)  # 创建/更新节点
            if tmp is None:
                return -3
            return 1


def load_data(file_name):
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


def extract_publication(entry):
    entry_parsed_keys = parse_bib_keys(entry)
    entry_type = entry.get(entry_parsed_keys["ENTRYTYPE"], None).upper()

    if entry_type is None:
        print("unrecognized entry (type):" + str(entry))
        return None
    elif entry_type == "ARTICLE":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        journal = is_valid_key(entry_parsed_keys, "journal".upper())
        journal = "" if journal is None else entry.get(journal, None)
        journal = process_special_character(journal)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        pages = is_valid_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if author is None or title is None or journal is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, title=title, journal=journal, year=year,
                           volume=volume, number=number, pages=pages, month=month, note=note)
    elif entry_type == "BOOK":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = is_valid_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = is_valid_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        edition = is_valid_key(entry_parsed_keys, "edition".upper())
        edition = "" if edition is None else entry.get(edition, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if (author is None and editor is None) or title is None or publisher is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, publisher=publisher,
                           year=year,
                           volume=volume, number=number, series=series, address=address, month=month,
                           edition=edition, note=note)
    elif entry_type == "INBOOK":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = is_valid_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        chapter = is_valid_key(entry_parsed_keys, "chapter".upper())
        chapter = "" if chapter is None else entry.get(chapter, None)
        pages = is_valid_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = is_valid_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        book_type = is_valid_key(entry_parsed_keys, "type".upper())
        book_type = "" if book_type is None else entry.get(book_type, None)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        edition = is_valid_key(entry_parsed_keys, "edition".upper())
        edition = "" if edition is None else entry.get(edition, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if (author is None and editor is None) or title is None or (chapter is None and pages is None) or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, journal=None, year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=edition, book_title=None, organization=None,
                           chapter=chapter, school=None, type=book_type, how_published=None, keywords=None, institution=None)
    elif entry_type == "INPROCEEDINGS" or entry_type == "CONFERENCE":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = is_valid_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        book_title = is_valid_key(entry_parsed_keys, "booktitle".upper())
        book_title = "" if book_title is None else entry.get(book_title, None)
        book_title = process_special_character(book_title)
        publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = is_valid_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        pages = is_valid_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        organization = is_valid_key(entry_parsed_keys, "organization".upper())
        organization = "" if organization is None else entry.get(organization, None)
        organization = process_special_character(organization)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if author is None or title is None or book_title is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, journal=None, year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=None, book_title=book_title, organization=organization,
                           chapter=None, school=None, type=None, how_published=None, keywords=None, institution=None)
    elif entry_type == "INCOLLECTION":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = is_valid_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        book_title = is_valid_key(entry_parsed_keys, "booktitle".upper())
        book_title = "" if book_title is None else entry.get(book_title, None)
        book_title = process_special_character(book_title)
        publisher = is_valid_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = is_valid_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = is_valid_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        pages = is_valid_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        edition = is_valid_key(entry_parsed_keys, "edition".upper())
        edition = "" if edition is None else entry.get(edition, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        book_type = is_valid_key(entry_parsed_keys, "type".upper())
        book_type = "" if book_type is None else entry.get(book_type, None)
        chapter = is_valid_key(entry_parsed_keys, "chapter".upper())
        chapter = "" if chapter is None else entry.get(chapter, None)
        chapter = process_special_character(chapter)
        if author is None or title is None or book_title is None or year is None or publisher is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="INCOLLECTION", author=author, editor=editor, title=title, journal=None,
                           year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=edition, book_title=book_title, organization=None,
                           chapter=chapter, school=None, type=book_type, how_published=None, keywords=None, institution=None)
    elif entry_type == "MISC":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        how_published = is_valid_key(entry_parsed_keys, "howpublished".upper())
        how_published = "" if how_published is None else entry.get(how_published, None)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        node = Publication(uuid="", node_type="MISC", author=author, editor=None, title=title, journal=None, year=year,
                           volume=None, number=None, series=None, address=None, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=None, type=None, how_published=how_published, keywords=None, institution=None)
    elif entry_type == "PHDTHESIS":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        school = is_valid_key(entry_parsed_keys, "school".upper())
        school = "" if school is None else entry.get(school, None)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        keywords = is_valid_key(entry_parsed_keys, "keywords".upper())
        keywords = "" if keywords is None else entry.get(keywords, None)
        keywords = process_special_character(keywords)
        if author is None or title is None or school is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="PHDTHESIS", author=author, editor=None, title=title, journal=None, year=year,
                           volume=None, number=None, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=school, type=None, how_published=None, keywords=keywords, institution=None)
    elif entry_type == "MASTERSTHESIS":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        school = is_valid_key(entry_parsed_keys, "school".upper())
        school = "" if school is None else entry.get(school, None)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        type = is_valid_key(entry_parsed_keys, "type".upper())
        type = "" if type is None else entry.get(type, None)
        type = process_special_character(type)
        if author is None or title is None or school is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="MASTERSTHESIS", author=author, editor=None, title=title, journal=None,
                           year=year,
                           volume=None, number=None, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=school, type=type, how_published=None, keywords=None, institution=None)
    elif entry_type == "TECHREPORT":
        author = is_valid_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = is_valid_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        institution = is_valid_key(entry_parsed_keys, "institution".upper())
        institution = "" if institution is None else entry.get(institution, None)
        institution = process_special_character(institution)
        year = is_valid_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = is_valid_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = is_valid_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = is_valid_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        number = is_valid_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        report_type = is_valid_key(entry_parsed_keys, "type".upper())
        report_type = "" if report_type is None else entry.get(report_type, None)
        if author is None or title is None or institution is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="TECHREPORT", author=author, editor=None, title=title, journal=None, year=year,
                           volume=None, number=number, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=None, type=report_type, how_published=None, keywords=None,
                           institution=institution)
    else:
        print("unsupported entry (type):" + str(entry))
        return None
    return node


def query_or_create_node(tx, node):
    """
    先查询节点是否存在，若存在，直接返回节点id，否则，创建节点并返回id。-1表示出错
    :param tx:
    :param node:
    :return:
    """
    if node is None:
        return None
    cypher = node.get_match_cypher()
    node_id = tx.run(cypher)
    for record in node_id:
        print("查询到了节点：" + str(record["node"]['uuid']))
        return record["node"]['uuid']
    node.uuid = uuid.uuid1()
    create_cypher = node.get_create_cypher()
    node_id = tx.run(create_cypher)
    for record in node_id:
        print("创建新节点：" + str(record["node"]['uuid']))
        return record["node"]['uuid']
    return None


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


def process_special_character(word):
    """
    处理了特殊转义字符、全部转成大写，去掉中间多余的空格
    :param word:
    :return:
    """
    if word is None or word == "":
        return ""
    # 转换latex特殊字符
    mappings = {"\\`{a}": 'à',
                "\\'{a}": 'á',
                "\^{a}": 'â',
                "\\\"{a}": 'ä',
                "\\'{c}": 'ć',
                "\\c{c}": 'ç',
                "\\v{c}": 'č',
                "\\`{e}": 'è',
                "\\'{e}": 'é',
                "\\^{e}": 'ê',
                "\\\"{e}": 'ë',
                "\\={e}": 'ē',
                "\\.{e}": 'ė',
                "\\c{e}": 'ę',
                "\\^{i}": 'î',
                "\\\"{i}": 'ï',
                "\\'{i}": 'í',
                "\\={i}": 'ī',
                "\\c{i}": 'į',
                "\\`{i}": 'ì',
                "\\v{n}": 'ñ',
                "\\'{n}": 'ń',
                "\\^{o}": 'ô',
                "\\\"{o}": 'ö',
                "\\`{o}": 'ò',
                "\\'{o}": 'ó',
                '\\ae': 'œ',
                '\\o': 'ø',
                "\\={o}": 'ō',
                "\\~{o}": 'õ',
                "\\ss": 'ß',
                "\\'{s}": 'ś',
                "\\v{s}": 'š',
                "\\^{u}": 'û',
                "\\\"{u}": 'ü',
                "\\`{u}": 'ù',
                "\\'{u}": 'ú',
                "\\={u}": 'ū',
                "\\\"{y}": 'ÿ',
                "\\v{z}": 'ž',
                "\\'{z}": 'ź',
                "\\.{z}": 'ż',
                "{\\l}": "ł",
                "\\url": "url",
                "\\a{a}": "å",
                "\\infty": "infty"}
    for (special, replace) in mappings.items():
        try:
            word = word.replace(special, replace)
        except:
            print("failed: " + str(word))
    # 转单引号
    word = word.replace("'", '\\\'')
    # 转&
    word = word.replace("\&", '&')
    # 转希腊字母
    greek_letters = {
        "{\\aa}": "å",
        "{\\AA}": "å",
        "\\alpha": "\\\\alpha",
        "\\beta": "\\\\beta",
        "\\chi": "\\\\chi",
        "\\delta": "\\\\delta",
        "\\Delta": "\\\\Delta",
        "\\epsilon": "\\\\epsilon",
        "\\eta": "\\\\eta",
        "\\gamma": "\\\\gamma",
        "\\Gamma": "\\\\Gamma",
        "\\iota": "\\\\iota",
        "\\kappa": "\\\\kappa",
        "\\lambda": "\\\\lambda",
        "\\Lambda": "\\\\Lambda",
        "\\mu": "\\\\mu",
        "\\nu": "\\\\nu",
        "\\omega": "\\\\omega",
        "\\Omega": "\\\\Omega",
        "\\phi": "\\\\phi",
        "\\Phi": "\\\\Phi",
        "\\pi": "\\\\pi",
        "\\Pi": "\\\\Pi",
        "\\psi": "\\\\psi",
        "\\Psi": "\\\\Psi",
        "\\rho": "\\\\rho",
        "\\sigma": "\\\\sigma",
        "\\Sigma": "\\\\Sigma",
        "\\tau": "\\\\tau",
        "\\theta": "\\\\theta",
        "\\Theta": "\\\\Theta",
        "\\upsilon": "\\\\upsilon",
        "\\Upsilon": "\\\\Upsilon",
        "\\xi": "\\\\xi",
        "\\Xi": "\\\\Xi",
        "\\zeta": "\\\\zeta",
        "\\digamma": "\\\\digamma",
        "\\varepsilon": "\\\\varepsilon",
        "\\varkappa": "\\\\varkappa",
        "\\varphi": "\\\\varphi",
        "\\varpi": "\\\\varpi",
        "\\varrho": "\\\\varrho",
        "\\varsigma": "\\\\varsigma",
        "\\vartheta": "\\\\vartheta",
    }
    for (letter, letter_new) in greek_letters.items():
        word = word.replace(letter, letter_new)
    word = word.upper()
    word = word.split(" ")
    word = " ".join(word)
    return word


def build_network_of_venues(venue_type="ARTICLE", publication_field='journal'):
    # 查询所有aritcles of publication
    cypher = "match (node:{NODE}) where node.node_type='{TYPE}' return node".format(NODE="Publication", TYPE=venue_type)
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        nodes = session.run(cypher)
        data = {}
        for record in nodes:
            print("提取{NODE}与{NODE2}之间关系过程：查询到节点：".format(NODE="Publication", NODE2="Venue")
                  + str(record["node"]['uuid']))
            if not string_util(record["node"][publication_field]):
                print("{ID} has empty {FIELD} field".format(ID=record["node"]['uuid'], FIELD=publication_field))
            else:
                data[record["node"]['uuid']] = record["node"][publication_field]
        if data is {}:
            print("提取{NODE}与{NODE2}之间关系过程：未查询到{NODE}.{TYPE}中的节点".format(NODE="Publication",
                                                                        TYPE="ARTICLE", NODE2="Venue"))
        else:
            # 提取Venue和Publication关系
            if venue_type == "ARTICLE":
                pub_venue_rel = extract_pub_ven_rel(session, data, venue_type)
            else:
                pub_venue_rel = extract_pub_ven_rel(session, data, "CONFERENCE")
            # 建立Venue和Publication关系
            if pub_venue_rel is None:
                print("未提取出有效的pub和venue关系。")
            else:
                for (pub_id, ven_id) in pub_venue_rel.items():
                    cypher = "MATCH  (pub:Publication {uuid:'" + pub_id + "'}) -[:PUBLISH_IN]-> (ven:Venue {uuid:'"\
                             + ven_id + "'})  return pub, ven"
                    result = session.run(cypher)
                    has_result = False
                    for record in result:
                        has_result = True
                        print("关系已存在(PUBLISH_IN):" + pub_id + "->" + ven_id)
                        break
                    if has_result:
                        continue
                    cypher = "MATCH  (pub:Publication {uuid:'" + pub_id + "'}) , (ven:Venue {uuid:'" + ven_id + "'}) " \
                             " CREATE (pub) -[:PUBLISH_IN]-> (ven) return pub, ven"
                    result = session.run(cypher)
                    has_result = False
                    for record in result:
                        has_result = True
                        print("创建关系成功(PUBLISH_IN):" + pub_id + "->" + ven_id)
                    if not has_result:
                        print("创建关系失败(PUBLISH_IN):" + pub_id + "->" + ven_id)


def build_network_of_persons(publication_field='author'):
    # 查询所有articles of publication
    cypher = "match (node:{NODE}) return node".format(NODE="Publication")
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as session:
        nodes = session.run(cypher)
        data = {}
        for record in nodes:
            print("提取{NODE}与{NODE2}之间关系过程：查询到节点：".format(NODE="Publication", NODE2="Person")
                  + str(record["node"]['uuid']))
            if not string_util(record["node"][publication_field]):
                print("{ID} has empty {FIELD} field".format(ID=record["node"]['uuid'], FIELD=publication_field))
            else:
                if record["node"]['uuid'] == 'a139070c79ef11e8bc9aa45e60c2e1a5':
                    print(record["node"]['uuid'])
                data[record["node"]['uuid']] = record["node"][publication_field]
        if data is {}:
            print("提取{NODE}与{NODE2}之间关系过程：未查询到{NODE}.{TYPE}中的节点".format(NODE="Publication",
                                                                        TYPE="author", NODE2="Person"))
        else:
            # 提取Person和Publication关系
            pub_person_rel = extract_pub_per_rel(session, data)  # {pubId: [{authorId, index}]}
            # 建立Venue和Publication关系
            if pub_person_rel is None:
                print("未提取出有效的pub和person关系。")
            else:
                for (pub_id, per_id_indexes) in pub_person_rel.items():
                    for per_id_index in per_id_indexes:
                        cypher = "MATCH  (pub:Publication {uuid:'" + pub_id + "'}) <-[r:Write]- (per:Person {uuid:'"\
                                 + per_id_index["id"] + "'})  return pub, per, r"
                        result = session.run(cypher)
                        result = result.data()
                        if len(result) > 0:
                            print("关系已存在(Write):" + pub_id + "<-" + per_id_index["id"])
                            existing_index = result[0]["r"]["index"]
                            if existing_index != per_id_index["index"]:
                                print("person:{person}-->publication:{pub}关系中作者顺序冲突(保持原有数据不变)，"
                                      "已有：{old}, 新{current}".format(person=per_id_index["id"], pub=pub_id,
                                                                    old=existing_index, current=per_id_index["index"]))
                        else:
                            print("创建关系(Write):" + pub_id + "<-" + per_id_index["id"])
                            cypher = "MATCH  (pub:Publication {uuid:'" + pub_id + "'}) , (per:Person {uuid:'" + \
                                     per_id_index["id"] + "'}) CREATE (pub) <-[:Write{index:" + str(per_id_index["index"]) \
                                     + "}]- (per) return pub, per"
                            result = session.run(cypher)
                            result = result.data()
                            if len(result) == 0:
                                print("创建关系失败(Write):" + pub_id + "<-" + per_id_index["id"])
                            else:
                                print("创建关系成功(Write):" + pub_id + "<-" + per_id_index["id"])


def extract_pub_ven_rel(session, data, venue_type):
    if data is None or data is {}:
        return None
    #  提取所有venue，创建节点，并记录uuid
    venues = data.values()
    venues_mappings = process_venue_names(venues)
    venue_name_id = {}
    pub_venue_rel = {}
    for (pub_id, venue) in data.items():
        venue_mapping = venues_mappings[venue]  # 映射后的venue
        if venue_mapping in venue_name_id.keys():  # 已经创建过Venue节点
            pub_venue_rel[pub_id] = venue_name_id[venue_mapping]
        else:  # 未创建过Venue节点，或已创建但未缓存
            venue_node = Venue(uuid="", venue_type=venue_type.upper(), venue_name=venue_mapping)
            cypher = venue_node.get_match_cypher()
            result = session.run(cypher)
            has_result = False
            for record in result: # 查询到了venue节点
                has_result = True
                venue_name_id[venue_mapping] = record["node"]["uuid"]
            if not has_result:  # 未查询到Venue节点
                venue_node.uuid = uuid.uuid1()
                cypher = venue_node.get_create_cypher()
                result = session.run(cypher)
                has_result = False
                for record in result:
                    print("创建Venue节点成功")
                    has_result = True
                    venue_name_id[venue_mapping] = venue_node.uuid.hex
                    break
                if not has_result:
                    print("创建Venue节点失败")
                    continue
            pub_venue_rel[pub_id] = venue_name_id[venue_mapping]
    if pub_venue_rel is {}:
        return None
    else:
        return pub_venue_rel


def extract_pub_per_rel(session, data):
    """

    :param session:
    :param data: dict, key是pub的uuid， value是pub的author字段
    :return:
    """
    if data is None or data is {}:
        return None
    #  提取所有person，创建节点，并记录uuid
    persons = data.values()
    persons_mappings = process_person_names(persons)  # author field --> [{author1, index}<,...>]
    person_name_id = {}  # 当前已经出现过的人的uuid，减少查询数据库次数
    pub_person_rel = {}  # pub_id --> [{author1, index}<, ...>]
    for (pub_id, person) in data.items():
        person_mapping = persons_mappings[person]  # 映射后的author list {author_name, index}
        if person_mapping is None:
            continue
        author_ids = []  # 用来存放当前pub的persons {author_id, index}
        for author in person_mapping:  # author是{author_id, index}形式
            if author["name"] in person_name_id.keys():  # 已经创建过Person节点
                author_ids.append({"id": person_name_id[author["name"]], "index": author["index"]})
            else:  # 未创建过Person节点，或已创建但未缓存
                person_node = Person(uuid="", name=author["name"])
                cypher = person_node.get_match_cypher()
                try:
                    result = session.run(cypher)
                except:
                    print("Invalid cypher: " + cypher)
                    continue
                result = result.value()
                the_id = ""
                if len(result) == 0:
                    print("未匹配人员：" + author["name"] + ", 创建新节点")
                    person_node.uuid = uuid.uuid1()
                    cypher = person_node.get_create_cypher()
                    result = session.run(cypher)
                    result = result.value()
                    if len(result) == 0:
                        print("创建Person节点失败!!!: " + author["name"])
                        continue
                    else:
                        print("创建Person节点成功: " + author["name"])
                        person_name_id[author["name"]] = person_node.uuid.hex
                        the_id = person_node.uuid.hex
                else:  # 有匹配数据
                    the_id = result[0]["uuid"]
                    print("匹配人员：" + author["name"] + ": " + the_id)
                person_name_id[author["name"]] = the_id
                author_ids.append({"id": the_id, "index": author["index"]})

        pub_person_rel[pub_id] = author_ids
    if pub_person_rel is {}:
        return None
    else:
        return pub_person_rel


def process_venue_names(names):
    """
    将文献字段中的venue，映射为处理过的venue
    :param names:
    :return:
    """
    if names is None:
        return None
    names_mapping = {}
    for name in names:
        #  去除前后空格，转成大写
        tmp = name.strip().upper()
        #  去掉重复空格
        tmp = " ".join(tmp.split())
        #  替换某些简写等 todo: 未实现
        tmp = tmp
        names_mapping[name] = tmp
    return names_mapping


def process_person_names(names):
    """
    将文献字段中的author，映射为处理过的author list，list中每个是一个字典，name&index
    :param names:
    :return:
    """
    if names is None:
        return None
    names_mapping = {}
    for name in names:
        #  去除前后空格，转成大写
        tmp = name.strip().upper()
        #  去掉重复空格
        tmp = " ".join(tmp.split())
        # 转换单引号
        tmp = tmp.replace("'", '\\\'')
        # 分开多个作者
        author_list = tmp.split(" AND ")
        # 将姓名格式统一为first_name last_name格式
        tmp_list = []
        for i in range(0, len(author_list)):
            author = author_list[i]
            if author.find(",") > -1:
                tmp_l = author.split(",")
                tmp_l = " ".join(tmp_l[::-1])
                tt = {"name": tmp_l, "index": (i+1)}
                tmp_list.append(tt)
            else:
                tt = {"name": author, "index": (i+1)}
                tmp_list.append(tt)

        names_mapping[name] = tmp_list
    return names_mapping


def string_util(string):
    if string is None or string is "":
        return False
    return True


class Publication:
    author = None
    editor = None
    title = None
    journal = None
    year = None
    volume = None
    number = None
    series = None
    address = None
    pages = None
    month = None
    note = None
    publisher = None
    edition = None
    book_title = None
    organization = None
    chapter = None
    school = None
    type = None
    how_published = None
    keywords = None
    institution = None
    node_type = None
    uuid = None

    def __init__(self, uuid, node_type, author=None, editor=None, title=None, journal=None, year=None,
                 volume=None, number=None, series=None, address=None, pages=None, month=None,
                 note=None, publisher=None, edition=None, book_title=None, organization=None,
                 chapter=None, school=None, type=None, how_published=None, keywords=None,
                 institution=None):
        self.uuid = uuid
        self.node_type = node_type
        self.author = author
        self.editor = editor
        self.title = title
        self.journal = journal
        self.year = year
        self.volume = volume
        self.number = number
        self.series = series
        self.address = address
        self.pages = pages
        self.month = month
        self.note = note
        self.publisher = publisher
        self.edition = edition
        self.book_title = book_title
        self.organization = organization
        self.chapter = chapter
        self.school = school
        self.type = type
        self.how_published = how_published
        self.keywords = keywords
        self.institution = institution

    def to_string(self):
        word = "{uuid:'" + ("" if self.uuid is None else self.uuid.hex) + "'," + \
               "node_type:'" + ("" if self.node_type is None else self.node_type) + "'," + \
               "author:'" + ("" if self.author is None else self.author) + "'," + \
               "editor:'" + ("" if self.editor is None else self.editor) + "'," + \
               "title:'" + ("" if self.title is None else self.title) + "'," + \
               "journal:'" + ("" if self.journal is None else self.journal) + "'," + \
               "year:'" + ("" if self.year is None else self.year) + "'," + \
               "volume:'" + ("" if self.volume is None else self.volume) + "'," + \
               "number:'" + ("" if self.number is None else self.number) + "'," + \
               "series:'" + ("" if self.series is None else self.series) + "'," + \
               "address:'" + ("" if self.address is None else self.address) + "'," + \
               "pages:'" + ("" if self.pages is None else self.pages) + "'," + \
               "month:'" + ("" if self.month is None else self.month) + "'," + \
               "note:'" + ("" if self.note is None else self.note) + "'," + \
               "publisher:'" + ("" if self.publisher is None else self.publisher) + "'," + \
               "edition:'" + ("" if self.edition is None else self.edition) + "'," + \
               "book_title:'" + ("" if self.book_title is None else self.book_title) + "'," + \
               "organization:'" + ("" if self.organization is None else self.organization) + "'," + \
               "chapter:'" + ("" if self.chapter is None else self.chapter) + "'," + \
               "school:'" + ("" if self.school is None else self.school) + "'," + \
               "type:'" + ("" if self.type is None else self.type) + "'," + \
               "how_published:'" + ("" if self.how_published is None else self.how_published) + "'," + \
               "keywords:'" + ("" if self.keywords is None else self.keywords) + "'," + \
               "institution:'" + ("" if self.institution is None else self.institution) + "'}"
        return word

    def to_string_for_set(self, node_identifier, field_value):
        if node_identifier is None or node_identifier == "" or not isinstance(field_value, dict):
            return ""
        word = ""
        for field, value in field_value.items():
            if value is None or value == '':
                value = ""
            word += node_identifier + "." + field + "='" + value + "',"
        word = word[:-1]
        return word

    def get_create_cypher(self):
        cypher = "CREATE (node:Publication " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self):
        cypher = "MATCH (node:Publication {"
        try:
            if self.node_type is None:
                print("unrecognized entry (type):" + self.to_string())
                return None
            elif self.node_type == "ARTICLE":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', journal:'" + self.journal + "', year:'" + self.year + "'})"
            elif self.node_type == "BOOK":
                if self.author is not None:
                    cypher += "author:'" + self.author + "', title:'" + self.title + \
                             "',publisher:'" + self.publisher + "', year:'" + self.year + "'})"
                elif self.editor is not None:
                    cypher += "editor:'" + self.editor + "', title:'" + self.title + \
                             "',publisher:'" + self.publisher + "', year:'" + self.year + "'})"
                else:
                    return None
            elif self.node_type == "INBOOK":
                if self.author is not None:
                    cypher += "author:'" + self.author + "', title:'" + self.title + \
                              "', year:'" + self.year
                elif self.editor is not None:
                    cypher += "editor:'" + self.editor + "', title:'" + self.title + \
                              "', year:'" + self.year
                else:
                    return None

                if self.chapter is not None:
                    cypher += "', chapter:'" + self.chapter + "'})"
                elif self.pages is not None:
                    cypher += "', pages:'" + self.pages + "'})"
                else:
                    return None
            elif self.node_type == "INPROCEEDINGS" or self.node_type == "CONFERENCE":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', book_title:'" + self.book_title + "', year:'" + self.year + "'})"
            elif self.node_type == "INCOLLECTION":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', book_title:'" + self.book_title + "', year:'" + self.year + "', publisher:'" + \
                          self.publisher + "'})"
            elif self.node_type == "MISC":
                if self.title is not None:
                    cypher += "title:'" + self.title + "'})"
                else:
                    return -1
            elif self.node_type == "PHDTHESIS":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', school:'" + self.school + "', year:'" + self.year + "'})"
            elif self.node_type == "MASTERSTHESIS":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', school:'" + self.school + "', year:'" + self.year + "'})"
            elif self.node_type == "TECHREPORT":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', institution:'" + self.institution + "', year:'" + self.year + "'})"
            else:
                print("unsupported entry (type):" + self.to_string())
                return None
        except:
            print("failed when generating match cypher: " + self.to_string())
            return None
        cypher += " return node"
        return cypher

    def get_revise_cypher(self, field_value_revise, field_value_match):
        if field_value_match is None or not isinstance(field_value_match, dict) or not isinstance(field_value_revise, dict):
            return ""
        cypher = "CREATE (node:Publication {"
        for field, value in field_value_match.items():
            cypher += field + ":'" + str(value) + "',"
        cypher = cypher[:-1] + "}) set " + self.to_string_for_set("node", field_value_revise) + " return node"
        return cypher


class Venue:
    uuid = None
    venue_type = None  # 会议、期刊
    venue_name = None  # 名称
    abbr = None  # 简称
    start_year = None  # 创刊年、第一届会议年
    year = None  # 会议年
    address = None  # 会议地址、期刊地址
    note = None  # 注释
    publisher = None  # 会议主办者、期刊出版社
    ei_index = None  # 是否EI检索
    sci_index = None  # 是否SCI检索
    ssci_index = None  # 是否SSCI检索

    def __init__(self, uuid, venue_type, venue_name, abbr=None, start_year=None, year=None,
                 address=None, note=None, publisher=None, ei_index=None, sci_index=None, ssci_index=None):
        self.uuid = uuid
        self.venue_type = venue_type
        self.venue_name = venue_name
        self.abbr = abbr
        self.start_year = start_year
        self.year = year
        self.address = address
        self.note = note
        self.publisher = publisher
        self.ei_index = ei_index
        self.sci_index = sci_index
        self.ssci_index = ssci_index

    def to_string(self):
        word = "{uuid:'" + ("" if self.uuid is None else self.uuid.hex) + "'," + \
               "venue_type:'" + ("" if self.venue_type is None else self.venue_type) + "'," + \
               "venue_name:'" + ("" if self.venue_name is None else self.venue_name) + "'," + \
               "abbr:'" + ("" if self.abbr is None else self.abbr) + "'," + \
               "start_year:'" + ("" if self.start_year is None else self.start_year) + "'," + \
               "year:'" + ("" if self.year is None else self.year) + "'," + \
               "address:'" + ("" if self.address is None else self.address) + "'," + \
               "note:'" + ("" if self.note is None else self.note) + "'," + \
               "publisher:'" + ("" if self.publisher is None else self.publisher) + "'," + \
               "ei_index:'" + ("" if self.ei_index is None else self.ei_index) + "'," + \
               "sci_index:'" + ("" if self.sci_index is None else self.sci_index) + "'," + \
               "ssci_index:'" + ("" if self.ssci_index is None else self.ssci_index) + "'}"
        return word

    def get_create_cypher(self):
        cypher = "CREATE (node:Venue " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self):
        cypher = "MATCH (node:Venue { venue_name:'" + self.venue_name + "'})  return node"
        return cypher


class Person:
    """
    name是first_name last_name格式
    """
    name = None
    name_ch = None
    affiliation_current = None
    research_interest = None
    uuid = None

    def __init__(self, uuid, name, name_ch=None, affiliation_current=None, research_interest=None):
        self.uuid = uuid
        self.name = name
        self.name_ch = name_ch
        self.affiliation_current = affiliation_current
        self.research_interest = research_interest

    def to_string(self):
        word = "{uuid:'" + ("" if self.uuid is None else self.uuid.hex) + "'," + \
               "name:'" + ("" if self.name is None else self.name) + "'," + \
               "name_ch:'" + ("" if self.name_ch is None else self.name_ch) + "'," + \
               "affiliation_current:'" + ("" if self.affiliation_current is None else self.affiliation_current) + "'," + \
               "research_interest:'" + ("" if self.research_interest is None else self.research_interest) + "'}"
        return word

    def get_create_cypher(self):
        cypher = "CREATE (node:Person " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self):
        cypher = "MATCH (node:Person {name:'" + self.name + "'}) return node"
        return cypher


if __name__ == "__main__":
    # # 从文件中解析文献，并创建节点
    build_network_of_publications('E:\\reference.bib')
    # # build_network_of_publications("bibtex.bib")
    # # 从网络中解析文献节点，并提取journal信息，创建venue节点、[wenxian]->[publication]
    build_network_of_venues(venue_type="ARTICLE", publication_field="journal")
    build_network_of_venues(venue_type="conference".upper(), publication_field="book_title")
    build_network_of_venues(venue_type="inproceedings".upper(), publication_field="book_title")
    # 从文献中解析author字段，创建Person节点、person->publication
    build_network_of_persons()
