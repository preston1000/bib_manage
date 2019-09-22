"""
这个文件是用来从文本或网页中的数据生成结构化数据结构的
"""


import os
import bibtexparser
import xlrd
from datetime import date, datetime
from utils.models import Pub, Publication
from utils.util_operation import upperize_dict_keys, get_value_by_key
from utils.util_text_operation import check_special, check_number, check_ordinary,check_special2


def do_extract(file, ext=None, parameters=None):
    """

    :param file: 文件路径
    :param ext: 后缀，若无，则从file后缀进行判别
    :return: 结构化的数据结构
    """
    # 解析文件后缀
    if ext is None:
        ext = os.path.splitext(file)[-1]
    if ext is None:
        flag = -1
        msg = "unable to extract he suffix of the file provided."
        return flag, msg, None
    # 按后缀名处理文件，获得文献的字符信息
    if ext == '.bib':
        flag, msg, bib_data = parse_bib(file)
    elif ext == 'xls' or ext == '.xlsx':
        flag, msg, bib_data = parse_excel(file, parameters)
    else:
        flag = -2
        msg = "file type is not supported."
        return flag, msg, None
    # 解析获得的bib信息
    if flag > 0:
        pubs = []
        counter = 0
        for entry in bib_data:
            pub = extract_publication(entry)
            if pub is not None:
                pubs.append(pub)
                counter = counter + 1
        if counter == 0:
            flag = -7
            msg = "no information in the bib is extracted"
            pubs = None
        elif counter == len(bib_data):
            flag = 1
            msg = "successfully"
        else:
            flag = 3
            msg = "some entries is not successfully parsed"
    else:
        pubs = None
    return flag, msg, pubs


def parse_bib(file_name):
    """
    从bib文件中解析出文献信息
    :param file_name:
    :return:
    """
    flag = 1
    msg = "successfully!"
    with open(file_name, encoding="utf-8") as bib_file:
        bib_database = bibtexparser.load(bib_file)
        if bib_database is not None:
            bib_database = bib_database.entries
    return flag, msg, bib_database # todo 要考虑可能出现的异常


def parse_excel(file_name, parameters=None):
    """
    从Excel文件中解析出文献信息，提取的结果是excel表中的各个数据，这里并不处理数据
    :param file_name:
    :param parameters: dict, fields include sheet_name(要分析的工作表名称)
    :return:
    """
    msg = "Successfully!"
    flag = 1
    try:
        wb = xlrd.open_workbook(filename=file_name)  # 打开文件
    except:
        flag = -3
        msg = 'failed to open file'
        return flag, msg

    if parameters is not None and isinstance(parameters, dict) and "sheet_name" in parameters.keys():
        sheet_name = parameters.get("sheet_name")
    else:
        sheet_name = 'deep learning'

    sheet_content = wb.sheet_by_name(sheet_name)  # 通过名字获取表格

    sheet_title = sheet_content.row_values(0)
    try:
        rol_index = sheet_title.index('bib')
    except ValueError:
        print("指定的工作表中没有bib列")
        return -10, "指定的工作表中没有bib列"
    content = []
    counter = 0
    for index in range(1, sheet_content.nrows):
        value = sheet_content.cell_value(index, rol_index)
        if value == "":
            print("当前文献没有bib信息" + str(sheet_content.row_values(index)))
            continue
        tmp = bibtexparser.loads(value)
        if tmp is not None:
            content.append(tmp.entries[0])
            counter = counter + 1
        else:
            print("信息无效：" + value)
    if counter == (sheet_content.nrows - 1):
        msg = "全部信息均有效解析"
        flag = 1
    elif counter == 0:
        msg = "全部信息无效或未成功解析"
        content = None
        flag = -11
    else:
        msg = "部分bib信息无效"
        flag = 2
    return flag, msg, content


def extract_publication(entry):
    entries = upperize_dict_keys(entry)
    entry_type = entries.get("ENTRYTYPE", None)

    if entry_type is None:
        print("unrecognized entry (type):" + str(entry))
        return None
    else:
        entry_type = entry_type.upper()

    id = get_value_by_key(entries, "id".upper())
    id = "" if id is None else id.upper()

    author = check_special2(entries, "author".upper())
    editor = check_special2(entries, "editor".upper())
    title = check_special2(entries, "title".upper())
    journal = check_special(entries, "journal".upper())
    publisher = check_special(entries, "publisher".upper())
    year = check_ordinary(entries, "year".upper())
    volume = check_ordinary(entries, "volume".upper())
    number = check_ordinary(entries, "number".upper())
    pages = check_ordinary(entries, "pages".upper())
    month = check_ordinary(entries, "month".upper())
    note = check_special(entries, "note".upper())
    series = check_special(entries, "series".upper())
    address = check_ordinary(entries, "address".upper())
    edition = check_ordinary(entries, "edition".upper())
    chapter = check_ordinary(entries, "chapter".upper())
    book_type = check_ordinary(entries, "type".upper())
    book_title = check_special(entries, "booktitle".upper())
    organization = check_special(entries, "organization".upper())
    how_published = check_ordinary(entries, "howpublished".upper())
    school = check_ordinary(entries, "school".upper())
    keywords = check_special(entries, "keywords".upper())
    type = check_special(entries, "type".upper())
    institution = check_special(entries, "institution".upper())
    report_type = check_ordinary(entries, "type".upper())

    if entry_type == "ARTICLE":
        if author is None or title is None or journal is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
    elif entry_type == "BOOK":
        if (author is None and editor is None) or title is None or publisher is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
    elif entry_type == "INBOOK":
        if (author is None and editor is None) or title is None or (chapter is None and pages is None) or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
    elif entry_type == "INPROCEEDINGS" or entry_type == "CONFERENCE":
        if author is None or title is None or book_title is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
    elif entry_type == "INCOLLECTION":
        if author is None or title is None or book_title is None or year is None or publisher is None:
            print("publication without mandatory fields: " + str(entry))
            return None
    elif entry_type == "MISC":
        # nothing to be done
        entry_type = "MISC"
    elif entry_type == "PHDTHESIS":
        if author is None or title is None or school is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
    elif entry_type == "MASTERSTHESIS":
        if author is None or title is None or school is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
    elif entry_type == "TECHREPORT":
        if author is None or title is None or institution is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
    else:
        print("unsupported entry (type):" + str(entry))
        return None

    node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, journal=journal, year=year,
                       volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                       note=note, publisher=publisher, edition=edition, book_title=book_title, organization=organization,
                       chapter=chapter, school=school, type=type, how_published=how_published, keywords=keywords,
                       institution=institution, id=id)
    return node


if __name__ == "__main__":
    # parse_excel('C:\\Users\\G314\\AppData\\Local\\kingsoft\\WPS Cloud Files\\userdata\\qing\\filecache\\独'
    #             '自行走的猪的云文档\\我的文档\\文献总结.xlsx')

    flag, msg, nodes = do_extract('file.xlsx')
    # flag, msg, nodes = do_extract('reference.bib')
    # flag, msg, nodes = do_extract('bibtex.bib')
    print(flag)
    print(msg)
    print(nodes[0].title)

