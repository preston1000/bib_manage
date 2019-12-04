"""
这个文件是用来从文本或网页中的数据生成结构化数据结构的
"""


import os
import bibtexparser
import xlrd
from utils.constants import GlobalVariables
from utils.models import Publication
from utils.util_operation_2 import upperize_dict_keys
from utils.util_text_operation import check_special, check_ordinary, check_special2, check_number

constant_pub_types = GlobalVariables.const_pub_type


def do_extract(file_path, ext=None, parameters=None):
    """
    从文件中提取文献信息，并返回models类
    :param file_path: 文件路径
    :param ext: 后缀，若无，则从file后缀进行判别
    :param parameters: 解析excel时需要的参数 todo 记录可接受参数
    :return: 结构化的数据
    """
    result = {"data": "", "msg": "", "code": 0}
    # 解析文件后缀
    if ext is None:
        ext = os.path.splitext(file_path)[-1]
    if ext is None:
        result["code"] = -100
        result["msg"] = "unable to extract he suffix of the file provided."
        return result
    # 按后缀名处理文件，获得文献的字符信息
    if ext == '.bib':
        parse_result = parse_bib_file(file_path)
    elif ext == 'xls' or ext == '.xlsx':
        parse_result = parse_excel_file(file_path, parameters)
    else:
        result["code"] = -115
        result["msg"] = "无法处理的类型的文件！【" + file_path + "】"
        return result
    if parse_result["code"] < 0:
        result["code"] = -116
        result["msg"] = parse_result["msg"]
        return result

    # 解析获得的bib信息
    bib_data = parse_result["data"]
    pubs = []
    counter_bib = 0
    counter_all = 0
    for entry in bib_data:
        counter_all += 1
        pub = extract_publication(entry)
        if pub["code"] == 120:
            pubs.append(pub["data"])
            counter_bib = counter_bib + 1
    if counter_all == 0:
        result["code"] = 110
        result["msg"] = "bib/excel文件解析成功，但不含文献信息\n" + parse_result["msg"]
    else:
        if counter_bib == counter_all:
            result["code"] = 111
            result["msg"] = "bib/excel文件解析成功，全部数据有效"
            result["data"] = pubs
        else:
            result["code"] = 112
            result["msg"] = "bib/excel文件解析成功，部分数据有效"
            result["data"] = pubs
    return result


def parse_bib_file(file_name):
    """
    从bib文件中解析出文献信息
    :param file_name:
    :return:
    """
    result = {"data": "", "msg": "", "code": 0}
    with open(file_name, encoding="utf-8") as bib_file:
        try:
            bib_database = bibtexparser.load(bib_file)
        except:
            result["code"] = -101
            result["msg"] = "无法解析bib文件【" + file_name + "】"
            return result
        if bib_database is not None:
            result["code"] = 100
            result["msg"] = "成功解析bib文件【" + file_name + "】"
            result["data"] = bib_database.entries
            return result
        else:
            result["code"] = -102
            result["msg"] = "未从bib文件中解析出结果！【" + file_name + "】"
            return result


def parse_excel_file(file_name, parameters=None):
    """
    从Excel文件中解析出文献信息，提取的结果是excel表中的各个数据，这里并不处理数据
    :param file_name:
    :param parameters: dict, fields include sheet_name(要分析的工作表名称)
    :return:
    """
    result = {"data": "", "msg": "", "code": 0}
    try:
        wb = xlrd.open_workbook(filename=file_name)  # 打开文件
    except:
        result["code"] = -105
        result["msg"] = '打开Excel文件失败'
        return result

    if parameters is not None and isinstance(parameters, dict):
        sheet_name = parameters.get("sheet_name", "deep learning")
        column_name = parameters.get("column_name", "bib")
    else:
        sheet_name = 'deep learning'
        column_name = "bib"

    try:
        sheet_content = wb.sheet_by_name(sheet_name)  # 通过名字获取表格
    except:
        result["code"] = -106
        result["msg"] = '读取Excel指定工作簿失败'
        return result
    try:
        sheet_title = sheet_content.row_values(0)
    except:
        result["code"] = -107
        result["msg"] = '读取Excel工作簿表头失败'
        return result
    try:
        col_index = sheet_title.index(column_name)  # 列下标
    except ValueError:
        result["code"] = -108
        result["msg"] = '指定的工作表中没有' + column_name + '列'
        return result
    content = []
    counter_bib = 0  # 成功解析出的行数
    counter_all = sheet_content.nrows - 1  # 总信息行数
    counter_null = 0  # 空白行个数
    for index in range(1, sheet_content.nrows):  # index是行下标
        value = sheet_content.cell_value(index, col_index)
        if value == "":
            print("第" + index + "行文献没有bib信息【" + str(sheet_content.row_values(index)) + "】")
            counter_null += 1
            continue
        try:
            tmp = bibtexparser.loads(value)
        except:
            print("第" + index + "行文献解析bib过程失败【" + str(sheet_content.row_values(index)) + "】")  # 内部错误，不返回错误码
        if tmp is not None:
            content.append(tmp.entries[0])
            counter_bib += counter_bib
        else:
            print("第" + index + "行文献解析bib过程失败2【" + str(sheet_content.row_values(index)) + "】")  # 内部错误，不返回错误码
    if counter_bib == (counter_all - counter_null):
        result["msg"] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + \
                        ">列全部信息(除空白行)均有效解析，共" + str(counter_all) + "行，" + str(counter_null) + "空白行，" + \
                        str(counter_bib) + "成功解析"
        result["code"] = 105
        result["data"] = content
        return result
    if counter_null == counter_all:
        result["msg"] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + ">列全部为空白"
        result["code"] = 107
        return result
    if (counter_all - counter_null) > counter_bib > 0:
        result["msg"] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + \
                        ">列全部信息(除空白行)部分有效解析，共" + str(counter_all) + "行，" + str(counter_null) + "空白行，" + \
                        str(counter_bib) + "成功解析"
        result["code"] = 106
        result["data"] = content
        return result
    if counter_all > counter_null and counter_bib == 0:
        result["msg"] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + ">列（除空白外）全部解析失败"
        result["code"] = -109
        return result
    result["msg"] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + ">列。结果未考虑！"
    result["code"] = -110
    return result


def extract_publication(entry):
    """
    从bib parser中提取出的数据进行处理，组装成models类
    这里 ENTRYTYPE  ---> node_type
        booktitle ---> book_title
        howpublished ---> how_published
    :param entry: dict，包含bib parser提出的字段
    :return:
    """
    result = {"msg": "", "code": 0, "data": ""}
    if entry is None or not isinstance(entry, dict) or entry.keys() is None:
        result["code"] = -120
        result["msg"] = "输入数据错误！"
        return result
    entry = upperize_dict_keys(entry)
    node_type = entry.get("ENTRYTYPE", None)

    if node_type is None:
        result["code"] = -121
        result["msg"] = "unrecognized entry (type):" + str(entry)
        return result

    #  共24个
    node_type = node_type.upper()
    id = check_ordinary(entry, "id".upper())
    author = check_special2(entry, "author".upper())
    editor = check_special2(entry, "editor".upper())
    title = check_special2(entry, "title".upper())
    journal = check_special(entry, "journal".upper())
    publisher = check_special(entry, "publisher".upper())
    year = check_number(entry, "year".upper())
    volume = check_ordinary(entry, "volume".upper())
    number = check_ordinary(entry, "number".upper())
    pages = check_ordinary(entry, "pages".upper())
    month = check_ordinary(entry, "month".upper())
    note = check_special(entry, "note".upper())
    series = check_special(entry, "series".upper())
    address = check_ordinary(entry, "address".upper())
    edition = check_ordinary(entry, "edition".upper())
    chapter = check_ordinary(entry, "chapter".upper())
    book_title = check_special(entry, "booktitle".upper())
    organization = check_special(entry, "organization".upper())
    how_published = check_ordinary(entry, "howpublished".upper())
    school = check_ordinary(entry, "school".upper())
    keywords = check_special(entry, "keywords".upper())
    type = check_special(entry, "type".upper())
    institution = check_special(entry, "institution".upper())

    try:
        pub_index = constant_pub_types.index(node_type)
    except:
        result["code"] = -123
        result["msg"] = "文献类型不支持【" + str(entry) + "】"
        return result

    if pub_index == 0:  # "ARTICLE"
        if author is None or title is None or journal is None or year is None:
            result["code"] = -122
            result["msg"] = "article必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 1:  # "BOOK"
        if (author is None and editor is None) or title is None or publisher is None or year is None:
            result["code"] = -122
            result["msg"] = "book必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 2:  # booklet
        if title is None:
            result["code"] = -122
            result["msg"] = "booklet必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 3 or pub_index ==  6:  # INPROCEEDINGS, CONFERENCE
        if author is None or title is None or book_title is None or year is None:
            result["code"] = -122
            result["msg"] = "inproceedings或conference必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 4:  # INBOOK
        if (author is None and editor is None) or title is None or (chapter is None and pages is None) or year is None:
            result["code"] = -122
            result["msg"] = "inbook必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 5:  # INCOLLECTION
        if author is None or title is None or book_title is None or year is None or publisher is None:
            result["code"] = -122
            result["msg"] = "INCOLLECTION必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 9:  # MISC
        if author is None and title is None and how_published is None and year is None and month is None and note is None:
            result["code"] = -122
            result["msg"] = "misc字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 7:  # manual
        if title is None:
            result["code"] = -122
            result["msg"] = "manual必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 8 or pub_index == 10:  # PHDTHESIS, MASTERSTHESIS
        if author is None or title is None or school is None or year is None:
            result["code"] = -122
            result["msg"] = "phdthesis或mastersthesis必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 11:
        if title is None or year is None:
            result["code"] = -122
            result["msg"] = "proceedings必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 12:  # TECHREPORT
        if author is None or title is None or institution is None or year is None:
            result["code"] = -122
            result["msg"] = "techreport必填字段甄别未通过！【" + str(entry) + "】"
            return result
    elif pub_index == 13:  # unpublished
        if author is None or title is None or note is None:
            result["code"] = -122
            result["msg"] = "techreport必填字段甄别未通过！【" + str(entry) + "】"
            return result
    node = Publication(uuid="", node_type=node_type, author=author, editor=editor, title=title, journal=journal, year=year,
                       volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                       note=note, publisher=publisher, edition=edition, book_title=book_title, organization=organization,
                       chapter=chapter, school=school, type=type, how_published=how_published, keywords=keywords,
                       institution=institution, id=id)
    result["code"] = 120
    result["msg"] = "done！【" + str(entry) + "】"
    result["data"] = node
    return result


if __name__ == "__main__":
    # parse_excel('C:\\Users\\G314\\AppData\\Local\\kingsoft\\WPS Cloud Files\\userdata\\qing\\filecache\\独'
    #             '自行走的猪的云文档\\我的文档\\文献总结.xlsx')

    extract_result = do_extract('file.xlsx')
    # extract_result = do_extract('reference.bib')
    # extract_result = do_extract('bibtex.bib')
    print(str(extract_result))

