"""
这个文件是用来从文本或网页中的数据生成结构化数据结构的
"""


import os
import bibtexparser
import xlrd
from datetime import date, datetime
from utils.models import Pub


def do_extract(file, ext=None, parameters=None):
    """

    :param file: 文件路径
    :param ext: 后缀，若无，则从file后缀进行判别
    :return: 结构化的数据结构
    """
    if ext is None:
        ext = os.path.splitext(file)[-1]
    if ext is None:
        flag = -1
        msg = "unable to extract he suffix of the file provided."
        return flag, msg
    if ext == '.bib':
        flag, msg, pubs = parse_bib(file)
    elif ext == 'xls' or ext == '.xlsx':
        flag, msg, content = parse_excel(file, parameters)
        if flag > 0:
            pubs = analyze_excel_content(content)
    else:
        flag = -2
        msg = "file type is not supported."
        return flag, msg
    if flag > 0:
        return flag, msg, pubs
    else:
        return flag, msg


def parse_bib(file_name):
    """
    从bib文件中解析出文献信息
    :param file_name:
    :return:
    """
    flag = 1
    msg = ""
    with open(file_name, encoding="utf-8") as bib_file:
        bib_database = bibtexparser.load(bib_file)
    if bib_database is None:
        flag = -4
        msg = "no information in the bib"
        return flag, msg
    bib_data = bib_database.entries
    pubs = []
    for entry in bib_data:
        flag, msg, pub = analyze_bib_content(entry)
        if flag > 0:
            pubs.append(pub)
    if pubs:
        return flag, msg, pubs
    else:
        flag = -7
        msg = "no information in the bib"
        return flag, msg


def parse_excel(file_name, parameters=None):
    """
    从Excel文件中解析出文献信息，提取的结果是excel表中的各个数据，这里并不处理数据
    :param file_name:
    :param parameters:
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
    content = []
    for index in range(1, sheet_content.nrows):
        content.append(dict(zip(sheet_title, sheet_content.row_values(index))))
    return flag, msg, content


def analyze_excel_content(content):
    if content is None or not isinstance(content, list):
        return
    pubs, venues, persons, relations = []
    # titles = content[0].keys()
    for info in content:
        tmp = bibtexparser.loads(info['bib'])
        flag, msg, pub, venue, person, relation = analyze_bib_content(tmp)
        if flag > 0:
            pubs = add_list(pubs, pub)
            venues = add_list(venues, venue)
            persons = add_list(persons, person)
            relations = add_list(relation, relation)
        else:
            print(str(info) + ", can not be processed")
    return pubs, venues, persons, relations


def analyze_bib_content(content):
    """
    对bib文件提取出的数据进行分析，得到pubs, venue, person, relation（venue_pub, person_pub等）信息
    :param content: 是bibtexparser生成的对象
    :return:
    """
    flag = 1
    msg = "successful"

    pub = Pub.create_node(content)  # 提取文献信息，构造节点
    if pub is  None:
        print(str(content) + ", can not be analyzed")
        flag = -6
        msg = "failed to extract any information in the bib"
        return flag, msg
    # if pub.ENTRYTYPE == 'article'.upper():
    #     venue = pub.get("journal".upper(), None)
    # elif pub.ENTRYTYPE == 'conference'.upper() or pub.ENTRYTYPE == 'inproceedings'.upper():
    #     venue = pub.get("booktitle".upper(), None)
    # else:
    #     venue = None
    #
    # persons = None if "author".upper() not in pub.keys() else pub.get("author".upper())
    # persons = persons.split(" and ")

    return flag, msg, pub  # , venue, persons


def add_list(old, new):
    """
    将new加到old里，
    :param old: list
    :param new:
    :return:
    """
    return None  # todo


if __name__ == "__main__":
    # parse_excel('C:\\Users\\G314\\AppData\\Local\\kingsoft\\WPS Cloud Files\\userdata\\qing\\filecache\\独'
    #             '自行走的猪的云文档\\我的文档\\文献总结.xlsx')

    parse_bib('bibtex.bib')
