from django.shortcuts import render
from django.http import HttpResponse
import json
import sys
from configparser import ConfigParser
import datetime
import os

import utils.util_text_operation
from utils.tmp_db import create_or_match_nodes_dict

from django.core.cache import cache

import xlrd

from utils import query_data, db_operation
from django.core.files.uploadedfile import InMemoryUploadedFile

config_file = "./pages.conf"
cf = ConfigParser()
cf.read(os.path.abspath(config_file), encoding="utf-8")
address = cf.get("moduleAddress", "address1")
sys.path.append(address)

cf = ConfigParser()
cf.read("./neo4j.conf", encoding="utf-8")
uri = cf.get("neo4j", "uri")
username = cf.get("neo4j", "username")
pwd = cf.get("neo4j", "pwd")
database_info = {"uri": uri, "username": username, "pwd": pwd}


def resolve_coordinates(request):
    return render(request, 'coordinates.html')


def parse_excel_stations(request):
    """
    从Excel文件中解析出车站信息，提取的结果是excel表中的各个数据
    :param request:
    :return:
    """
    result = {"data": "", "msg": "", "code": 1}
    try:
        file = request.FILES.getlist('file')
    except:
        result["msg"] = 'No file in the request'
        result["code"] = -1
        return HttpResponse(json.dumps(result))
    if file is None:
        result["msg"] = 'No file in the request'
        result["code"] = -1
        return HttpResponse(json.dumps(result))
    file = file[0]
    try:
        wb = xlrd.open_workbook(filename=None, file_contents=file.read())  # 打开文件
    except:
        result["code"] = -2
        result["msg"] = '打开Excel文件失败'
        return HttpResponse(json.dumps(result))

    sheet_name = 'Sheet1'
    try:
        sheet_content = wb.sheet_by_name(sheet_name)  # 通过名字获取表格
    except:
        result["code"] = -3
        result["msg"] = '读取Excel指定工作簿失败'
        return HttpResponse(json.dumps(result))

    try:
        sheet_title = sheet_content.row_values(0)
    except:
        result["code"] = -4
        result["msg"] = '读取Excel工作簿表头失败'
        return HttpResponse(json.dumps(result))

    column_name = ["序号", "地址", '城市', '线路', '下一站']
    try:
        col_index = [sheet_title.index(j) for j in column_name]  # [sheet_title.index(column_name[0]), sheet_title.index(column_name[1]), sheet_title.index(column_name[2]), sheet_title.index(column_name[3])]
    except ValueError:
        result["code"] = -5
        result["msg"] = '指定的工作表中没有' + str(column_name) + '列'
        return HttpResponse(json.dumps(result))

    content = []
    counter_null = 1  #
    for index in range(1, sheet_content.nrows):  # index是行下标
        addr = sheet_content.cell_value(index, col_index[1])
        city = sheet_content.cell_value(index, col_index[2])
        line = sheet_content.cell_value(index, col_index[3])
        next = sheet_content.cell_value(index, col_index[4])
        if addr == "":
            print("第" + index + "行文献没有地址信息【" + str(sheet_content.row_values(index)) + "】")
            continue
        tmp = {"index": counter_null, "address": addr, 'city': city, "line": line, 'next': next}
        counter_null += 1
        content.append(tmp)
    result["data"] = content
    result["msg"] = "done"
    return HttpResponse(json.dumps(result))


def search_home(request):
    return render(request, 'search_home.html')


def search_result(request):
    return render(request, 'search_result.html')


def search_publication_new(request):
    """
    这个实现的是在搜索结果界面的功能，包括高级搜索、查询和搜索数据的返回等，只查询，不创建
    :param request:
    :return:
    """
    result = {"msg": "", "code": 0, "data": "", "count": 0}
    if request.method == 'POST':
        # 解析传递参数，高级搜索的条件
        if request.is_ajax():
            the_paras = request.body
            if the_paras is None:
                result["msg"] = "no data is given"
                result["code"] = -3
                return HttpResponse(json.dumps(result))
            try:
                pub_info = bytes.decode(the_paras)
                pub_info = json.loads(pub_info)
            except:
                the_paras = request.POST
                pub_info = the_paras.get("param", None)
                if pub_info is None:
                    result["msg"] = "given data is not a json string"
                    result["code"] = -2
                    return HttpResponse(json.dumps(result))
                pub_info = json.loads(pub_info)
            page = None
            limit = None
        else:
            the_paras = request.POST
            pub_info = the_paras.get("param", None)
            if pub_info is None:
                result["msg"] = "no valid info is provided for search"
                result["code"] = -3
                return HttpResponse(json.dumps(result))
            pub_info = json.loads(pub_info)
            page = the_paras.get("page", None)
            limit = the_paras.get("limit", None)
        parameters = process_search_condition(pub_info) # 封装数据为后台数据库能够接收的格式
        # 分页条件
        page_para = None
        if page is not None and limit is not None:
            try:
                page_para = {"page": int(page), "limit": int(limit)}
            except ValueError:
                page_para = None
        # 查询
        query_result = query_data.query_pub_by_multiple_field(database_info, parameters, page_para)
        query_result = json.loads(query_result)
        if query_result["code"] < 0:  # 返回的code有1，2，0，-1共四中
            return HttpResponse(json.dumps(query_result))
        # 处理返回的数据
        count = 1
        pubs = []
        for pub in query_result["data"]:
            pub["ID"] = count
            if pub["pages1"] == "" or pub["pages2"] == "":
                pub["pages"] = ""
            else:
                pub["pages"] = str(pub["pages1"]) + "-" + str(pub["pages2"])
            # pub.pop("pages1")
            # pub.pop("pages2")
            count += 1
            pubs.append(pub)
        if request.is_ajax():
            result["msg"] = "done"
            result["count"] = len(pubs)  # todo 检查是否正确？
            result["code"] = query_result["code"]
            result["data"] = pubs
        else:
            result["msg"] = "done"
            result["count"] = pub_info["count"]
            result["code"] = query_result["code"]
            result["data"] = pubs
        return HttpResponse(json.dumps(result))
    else:
        result["msg"] = "not support request method, should be post"
        result["code"] = -4
        return HttpResponse(json.dumps(result))


def search_publication_count(request):
    """
    根据搜索条件，计算有多少条数据满足条件
    :param request:
    :return:
    """
    if request.is_ajax() and request.method == 'POST':
        pub_info = request.body
        if pub_info is None or pub_info == "":
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        try:
            pub_info = bytes.decode(pub_info)
            pub_info = json.loads(pub_info)
        except:
            return HttpResponse(json.dumps({"msg": "given data is not a json string", "status": -1}))

        if pub_info is None:
            return HttpResponse(json.dumps({"msg": "no valid info is provided for search", "status": 0}))

        # 封装数据为后台数据库能够接收的格式
        parameters = process_search_condition(pub_info)
        if parameters is None:
            return HttpResponse(json.dumps({"code": -1, "msg": "搜索条件解析失败，请重试", "count": 0, "data": ""}))
        query_result = query_data.query_by_multiple_field_count(database_info, parameters, "PUBLICATION")  # -1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
        query_result["status"] = query_result["code"]
        return HttpResponse(json.dumps(query_result))
    else:
        return HttpResponse(json.dumps({"status": -1, "msg": "not support request method, should be post", "count": 0, "data": ""}))


def process_search_condition(pub_info):
    parameters = {}
    # 标题关键字
    title = pub_info.get("title", None)
    if not(title is None or title == ""):
        parameters["title"] = title
    # 起止时间
    start_time = pub_info.get("startTime", None)
    end_time = pub_info.get("endTime", None)
    if not (start_time is None or start_time == ""):
        parameters["startTime"] = start_time
    if not (end_time is None or end_time == ""):
        parameters["endTime"] = end_time
    # 作者
    author = pub_info.get("author", None)
    if not (author is None or author == ""):
        parameters["author"] = author
    # 文章索引
    paper_index = pub_info.get("paperIndex", None)
    if not (paper_index is None or paper_index == ""):
        parameters["paperIndex"] = paper_index
    # 文献类型
    node_type = pub_info.get("node_type", None)
    if node_type is not None and node_type != "":
        parameters["node_type"] = node_type.upper()
    # 检查是否有效条件
    if parameters == {}:
        parameters = None
    return parameters


def view_pdf(request):
    return render(request, 'view_pdf.html')


def show_pdf(request):
    # todo 实现文件存储
    return  render(request)


def manage(request):

    return render(request, 'manage.html')


# 以上是新网页
######################################################################################


def add_publication(request):
    """
    向cypher添加pub ---- 已改
    :param request:
    :return:
    """
    result = {"msg": "", "code": 0, "data":"", "count": 0}
    if request.method == 'POST':
        if request.is_ajax():
            pub_info = request.body
            if pub_info is None:
                result["msg"] = "no data is given"
                result["code"] = -3
                return HttpResponse(json.dumps(result))
            try:
                pub_info = bytes.decode(pub_info)
                pub_info = json.loads(pub_info)
            except:
                result["msg"] = "given data is not a json string"
                result["code"] = -4
                return HttpResponse(json.dumps(result))
        else:
            pub_info = request.POST
            if pub_info is None:
                result["msg"] = "no data is given"
                result["code"] = -3
                return HttpResponse(json.dumps(result))
        # 参数提取
        to_create = pub_info.get("to_create", False)
        return_type = pub_info.get("return_type", 'dict')
        # 特殊字段的处理：作者
        authors = pub_info.get("author", None)
        if authors is None:
            pub_info["author"] = ""
        elif isinstance(authors, list):
            tmp, num, counter = ["", len(authors), 0]
            for author in authors:
                tmp += author["lastName"] + ", " + author["firstName"] + " " + author["middleName"]
                counter += 1
                if counter < num:
                    tmp += " and "
            pub_info["author"] = tmp
        # 特殊字段的处理：文章类型
        if pub_info["node_type"] == "0":
            pub_info["node_type"] = "ARTICLE"
        elif pub_info["node_type"] == "1":
            pub_info["node_type"] = "BOOK"
        elif pub_info["node_type"] == "2":
            pub_info["node_type"] = "BOOKLET"
        elif pub_info["node_type"] == "3":
            pub_info["node_type"] = "CONFERENCE"
        elif pub_info["node_type"] == "4":
            pub_info["node_type"] = "INBOOK"
        elif pub_info["node_type"] == "5":
            pub_info["node_type"] = "INCOLLECTION"
        elif pub_info["node_type"] == "6":
            pub_info["node_type"] = "INPROCEEDINGS"
        elif pub_info["node_type"] == "7":
            pub_info["node_type"] = "MANUAL"
        elif pub_info["node_type"] == "8":
            pub_info["node_type"] = "MASTERSTHESIS"
        elif pub_info["node_type"] == "9":
            pub_info["node_type"] = "MISC"
        elif pub_info["node_type"] == "10":
            pub_info["node_type"] = "PHDTHESIS"
        elif pub_info["node_type"] == "11":
            pub_info["node_type"] = "PROCEEDINGS"
        elif pub_info["node_type"] == "12":
            pub_info["node_type"] = "TECHREPORT"
        elif pub_info["node_type"] == "13":
            pub_info["node_type"] = "UNPUBLISHED"
        else:
            result["msg"] = "unsupported paper type"
            result["code"] = -5
            return HttpResponse(json.dumps(result))
        # 调方法写数据库
        query_result = create_or_match_nodes_dict(pub_info, "PUBLICATION", database_info, return_type=return_type, to_create=to_create)

        result["msg"] = query_result.get("msg", "查询数据接口无返回值")
        result["code"] = query_result.get("code", -6)
        result["data"] = query_result.get("data", [])
        try:
            result["count"] = len(result["data"])
        except:
            result["count"] = 0
        return HttpResponse(json.dumps(result))
    else:
        result["msg"] = "请求方式应为post"
        result["code"] = -7
        return HttpResponse(json.dumps(result))


def index(request):
    # return HttpResponse('welcome to the front page')
    return render(request, 'index.html')


def about(request):
    import json
    pos = request.GET.get("pos", None)
    if pos is None:
        return render(request, 'about_backup.html', {"position": json.dumps('null')})
    else:
        return render(request, 'about_backup.html', {"position": json.dumps(pos)})


def table(request):
    # return HttpResponse('welcome to the front page')
    return render(request, 'table.html')


def net(request):
    return render(request, "net.html")


def get_sample_data(request):
    page = request.GET.get("page", None)
    limit = request.GET.get("limit", None)
    # limit = None
    if page is None or limit is None:
        data = query_data.sample_data()
    else:
        data = query_data.sample_data((int(page)-1)*int(limit), int(limit))
    return HttpResponse(data)


def get_vis_data(request):
    json_str = query_data.query_vis_data()
    return HttpResponse(json_str)


def get_author_table_data(request):
    """
    编辑作者页面时，数据源
    :param request:
    :return:
    """
    current_data = request.GET.get("currentData", None)
    mode = request.GET.get("mode", 1)
    mode = int(mode)
    if current_data is None:
        data = [{"firstName": "", "middleName": "", "lastName": "", "ranking": "1"}]
    else:
        try:
            data = json.loads(current_data)
            try:
                if mode == 1:
                    data1 = []
                    for item in data:
                        item.pop("LAY_TABLE_INDEX")
                        data1.append(item)
                    data = data1
                    current_numbers = [int(item["ranking"]) for item in data]
                    ranges = range(1, len(current_numbers)+2)
                    new_number = [number for number in ranges if number not in current_numbers]
                    if new_number is None:
                        new_number = len(current_numbers)+1
                    else:
                        new_number = new_number[0]
                    data.append({"firstName": "", "middleName": "", "lastName": "", "ranking": str(new_number)})
                elif mode == 2:
                    data = data
                else:
                    data = [{"firstName": "", "middleName": "", "lastName": "", "ranking": "1"}]
                    print("未能识别的mode")
            except:
                print("解析失败")
        except:
            data = [{"firstName": "", "middleName": "", "lastName": "", "ranking": "1"}]

    json_str = {"code": 0, "msg": "successfully queried data", "count": 1, "data": data}
    return HttpResponse(json.dumps(json_str))


def add_person(request):
    """
    向cypher添加person
    :param request:
    :return: {"msg": "", "status": 0}, 0:缺少参数；-1：参数格式错误;-10:请求方式错误，-2~-5见create_or_match_persons方法
    """
    if request.is_ajax() and request.method == 'POST':
        node_info = request.body  # 处理后是dict，直接传到后台写入数据库就可以了
        if node_info is None or node_info == "":
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except:
            return HttpResponse(json.dumps({"msg": "given data is not a json string", "status": -1}))
        # 调方法写数据库
        flag = db_operation.create_or_match_persons(node_info, mode=2)
        if flag["code"] == 1:
            return HttpResponse(json.dumps({"msg": "successfully write into database", "status": 1}))
        else:
            return HttpResponse(json.dumps({"msg": "error when writing into database" + flag["msg"], "status": flag}))
    else:
        return HttpResponse(json.dumps({"msg": "not supported request form", "status": -10}))


def add_venue(request):
    """
    向cypher添加venue
    :param request:
    :return: {"msg": "", "status": 0}, 0:缺少参数；-1：参数格式错误;-10:请求方式错误，-2~-5见create_or_match_persons方法
    """
    if request.is_ajax() and request.method == 'POST':
        node_info = request.body  # 处理后是dict，直接传到后台写入数据库就可以了
        if node_info is None or node_info == "":
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except:
            return HttpResponse(json.dumps({"msg": "given data is not a json string", "status": -1}))
        # 调方法写数据库
        flag = db_operation.create_or_match_venues(node_info, mode=2)
        if flag["code"] == 1:
            return HttpResponse(json.dumps({"msg": "successfully write into database", "status": 1}))
        else:
            return HttpResponse(json.dumps({"msg": "error when writing into database" + flag["msg"], "status": flag}))
    else:
        return HttpResponse(json.dumps({"msg": "not supported request form", "status": -10}))


def add_relation(request):
    """
    向cypher添加relation
    :param request:
    :return: {"msg": "", "status": 0}, 0:缺少参数；-1：参数格式错误;-10:请求方式错误，-2~-5见create_or_match_persons方法
    """
    if request.is_ajax() and request.method == 'POST':
        node_info = request.body  # 处理后是dict，直接传到后台写入数据库就可以了
        if node_info is None or node_info == "":
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except:
            return HttpResponse(json.dumps({"msg": "given data is not a json string", "status": -1}))
        # 调方法写数据库
        source_id = node_info["sourceID"]
        source_type = node_info["sourceType"]
        target_id = node_info["targetID"]
        target_type = node_info["targetType"]
        rel_type = node_info["relType"]
        flag = db_operation.query_or_create_relation(None, source_type, source_id, target_type, target_id, rel_type)
        if flag["status"] > 0:
            return HttpResponse(json.dumps({"msg": "successfully write into database", "status": 1}))
        else:
            return HttpResponse(json.dumps({"msg": "error when writing into database" + flag["msg"], "status": flag["status"]}))
    else:
        return HttpResponse(json.dumps({"msg": "not supported request form", "status": -10}))


def revise_publication(request):
    """
    利用cypher修改pub
    :param request:
    :return:
    """
    if request.is_ajax() and request.method == 'POST':
        pub_info = request.body
        if pub_info is None or pub_info == "":
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        try:
            pub_info = bytes.decode(pub_info)
            pub_info = json.loads(pub_info)
        except:
            return HttpResponse(json.dumps({"msg": "given data is not a json string", "status": -1}))
        # 特殊字段的处理：作者
        authors = pub_info.get("author", None)
        if authors is None:
            pub_info["author"] = ""
        elif isinstance(authors, list):
            tmp, num, counter = ["", len(authors), 0]
            for author in authors:
                tmp += author["lastName"] + ", " + author["firstName"] + " " + author["middleName"]
                counter += 1
                if counter < num:
                    tmp += " and "
            pub_info["author"] = tmp
        # 特殊字段的处理：文章类型
        if pub_info["node_type"] == "0":
            pub_info["node_type"] = "ARTICLE"
        elif pub_info["node_type"] == "1":
            pub_info["node_type"] = "Book"
        elif pub_info["node_type"] == "2":
            pub_info["node_type"] = "Booklet"
        elif pub_info["node_type"] == "3":
            pub_info["node_type"] = "Conference"
        elif pub_info["node_type"] == "4":
            pub_info["node_type"] = "InBook"
        elif pub_info["node_type"] == "5":
            pub_info["node_type"] = "InCollection"
        elif pub_info["node_type"] == "6":
            pub_info["node_type"] = "InProceedings"
        elif pub_info["node_type"] == "7":
            pub_info["node_type"] = "Manual"
        elif pub_info["node_type"] == "8":
            pub_info["node_type"] = "MastersThesis"
        elif pub_info["node_type"] == "9":
            pub_info["node_type"] = "Misc"
        elif pub_info["node_type"] == "10":
            pub_info["node_type"] = "PhDThesis"
        elif pub_info["node_type"] == "11":
            pub_info["node_type"] = "Proceedings"
        elif pub_info["node_type"] == "12":
            pub_info["node_type"] = "TechReport"
        elif pub_info["node_type"] == "13":
            pub_info["node_type"] = "Unpublished"
        else:
            return HttpResponse(json.dumps({"msg": "unsupported paper type", "status": -3}))
        # 特殊处理，pages
        p1 = pub_info.get("pages1", None)
        p2 = pub_info.get("pages2", None)
        if p1 is not None and p2 is not None:
            pub_info["pages"] = str(p1) + "-" + str(p2)
        # 调方法写数据库
        flag = db_operation.revise_publications(pub_info)
        if flag == 1:
            return HttpResponse(json.dumps({"msg": "successfully write into database", "status": 1}))
        else:
            return HttpResponse(json.dumps({"msg": "error when writing into database", "status": flag*3}))
    else:
        return HttpResponse(json.dumps({"msg": "not supported request form", "status": -2}))


def revise_person(request):
    """
    利用cypher修改person
    :param request:
    :return:{"msg": "no data is given", "status": 0} 0:无参数,-1:参数格式错误,
    """
    if request.is_ajax() and request.method == 'POST':
        node_info = request.body
        if node_info is None or node_info == "":
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except:
            return HttpResponse(json.dumps({"msg": "given data is not a json string", "status": -1}))
        # 调方法写数据库
        flag = db_operation.revise_persons(node_info)
        if flag == 1:
            return HttpResponse(json.dumps({"msg": "successfully write into database", "status": 1}))
        else:
            return HttpResponse(json.dumps({"msg": "error when writing into database", "status": flag*3}))
    else:
        return HttpResponse(json.dumps({"msg": "not supported request form", "status": -2}))


def revise_venue(request):
    """
    利用cypher修改person
    :param request:
    :return:{"msg": "no data is given", "status": 0} 0:无参数,-1:参数格式错误,
    """
    if request.is_ajax() and request.method == 'POST':
        node_info = request.body
        if node_info is None or node_info == "":
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except:
            return HttpResponse(json.dumps({"msg": "given data is not a json string", "status": -1}))
        # 调方法写数据库
        flag = db_operation.revise_venues(node_info)
        if flag == 1:
            return HttpResponse(json.dumps({"msg": "successfully write into database", "status": 1}))
        else:
            return HttpResponse(json.dumps({"msg": "error when writing into database", "status": flag*3}))
    else:
        return HttpResponse(json.dumps({"msg": "not supported request form", "status": -2}))


def search_publication(request):
    """
    在neo4j中搜索pub
    :param request:
    :return:0:无参数，-1：请求方式错误，-2：缺少标题；
    """
    if request.method == 'POST':
        the_paras = request.POST
        pub_info = the_paras.keys()
        if pub_info is None:
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        # 调方法写数据库
        title = the_paras.get("title", None)
        if title is None or title.strip() == "":
            return HttpResponse(
                json.dumps({"code": -2, "msg": "标题一定要有才能搜索", "count": 0, "data": ""}))
        parameters = {"title": title}
        paper_type = the_paras.get("paperType", None)
        if paper_type is not None and paper_type.strip() != "":
            parameters["paperTypeEdit"] = paper_type
        flag = query_data.query_pub_by_multiple_field(parameters)  # -1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
        data = json.loads(flag)
        if data["code"] < 1:
            return HttpResponse(flag)
        else:  # 返回数据
            count = 1
            pubs = []
            for pub in data["data"]:
                pub["ID"] = count
                if pub["pages1"] == "" or pub["pages2"] == "":
                    pub["pages"] = ""
                else:
                    pub["pages"] = str(pub["pages1"]) + "-" + str(pub["pages2"])
                pub.pop("pages1")
                pub.pop("pages2")
                count += 1
                pubs.append(pub)
            data["data"] = pubs
            data["code"] = 0
            return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps({"code": -1, "msg": "not support request method, should be post", "count": 0, "data": ""}))


def search_person(request):
    """
    在neo4j中搜索person
    :param request:
    :return:
    """
    if request.method == 'POST':
        the_paras = request.POST
        pub_info = the_paras.keys()
        if pub_info is None:
            return HttpResponse(json.dumps({"msg": "no data is given", "status": 0}))
        # 调方法写数据库
        full_name = the_paras.get("full_name", None)
        if full_name is None or full_name.strip() == "":
            return HttpResponse(
                json.dumps({"code": -2, "msg": "标题一定要有才能搜索", "count": 0, "data": ""}))
        parameters = {"full_name": full_name}
        flag = query_data.query_person_or_venue_by_multiple_field(parameters, "PERSON")
        data = json.loads(flag)
        if data["code"] < 1:
            return HttpResponse(flag)
        else:  # 返回数据
            count = 1
            persons = []
            for person in data["data"]:
                person["ID"] = count
                count += 1
                persons.append(person)
            data["data"] = persons
            data["code"] = 0
            return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps({"code": -1, "msg": "not support request method, should be post", "count": 0, "data": ""}))


def search_venue(request):
    """
    在neo4j中搜索venue ---- 已改
    :param request:
    :return:
    """
    if request.method == 'POST':
        if request.is_ajax():
            the_paras = request.body
            if the_paras is None:
                return HttpResponse(json.dumps({"msg": "no data is given", "code": 0, "data":"", "count": 0}))
            try:
                the_paras = bytes.decode(the_paras)
                the_paras = json.loads(the_paras)
            except:
                return HttpResponse(json.dumps({"msg": "given data is not a json string", "code": -1, "data": "", "count": 0}))
            # page = None
            # limit = None
        else:
            the_paras = request.POST
            pub_info = the_paras.keys()
            if pub_info is None:
                return HttpResponse(json.dumps({"msg": "no data is given", "code": 0, "data":"", "count": 0}))
            # page = the_paras.get("page", None)
            # limit = the_paras.get("limit", None)

        # 调方法写数据库
        title = the_paras.get("venue_name", None)
        if title is None or title.strip() == "":
            return HttpResponse(
                json.dumps({"code": -2, "msg": "标题一定要有才能搜索", "count": 0, "data": ""}))
        parameters = {"venue_name": title}
        flag = query_data.query_person_or_venue_by_multiple_field(parameters, "VENUE")
        data = json.loads(flag)
        if data["code"] < 1:
            return HttpResponse(flag)
        else:  # 返回数据
            count = 1
            venues = []
            for venue in data["data"]:
                venue["ID"] = count
                count += 1
                venues.append(venue)
            data["data"] = venues
            data["count"] = count
            data["code"] = 1
            return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps({"code": -1, "msg": "not support request method, should be post", "count": 0, "data": ""}))


def verify_auth(request):
    """
        验证用户-----现在是从固定列表中读取
        :param request:
        :return:
        """
    user_list = {"user": "123456"}
    result = {}
    if request.is_ajax() and request.method == 'GET':
        user = request.GET.get("username", None)
        pwd = request.GET.get("pwd", None)
        if user is None or pwd is None:
            result = {"status": -1, "msg": "invalid request parameters"}
        else:
            pwd_in_database = user_list.get(user, None)
            if pwd_in_database is None:
                result = {"status": -1, "msg": "no registered user"}
            elif pwd_in_database != pwd:
                result = {"status": -1, "msg": "unmatched password"}
            else:
                result = {"status": 1, "msg": "matched user and password", "user":user, "pwd": pwd}
    else:
        result = {"status": -1, "msg": "invalid request"}
    return HttpResponse(json.dumps(result))


def get_pib_info_for_edit(request):
    if request.is_ajax() and request.method == 'GET':
        uuid = request.GET.get("id", None)
        if uuid is None:
            return HttpResponse(json.dumps({"msg": "no valid publication id is provided.", "status": -1}))
        else:
            data = query_data.query_one_pub_by_uuid(uuid)
            if data["code"] != 1:
                return HttpResponse(json.dumps({"msg": data["msg"], "status": -1}))
            else:
                return HttpResponse(json.dumps({"msg": data["msg"], "status": 1, "data":data["data"]}))
    return HttpResponse(json.dumps({"msg": "not ajax request or the request method is not get", "status": -1}))


def pub_interface(request):
    return render(request, "public_interface.html")


def search_pub_popup(request):
    return render(request, "searchPub.html")


def search_person_popup(request):
    return render(request, "searchPerson.html")


def search_venue_popup(request):
    return render(request, "searchVenue.html")


def upload_bib_add_record(request):
    for file in request.FILES.getlist('file'):
        file_path = handle_uploaded_file(file)  # 处理上传来的文件
        flag = db_operation.create_or_match_publications(file_path, mode=1)
        os.remove(file_path)
        if flag == 1:
            return HttpResponse(json.dumps({"msg": "successfully write into database", "status": 1}))
        else:
            return HttpResponse(json.dumps({"msg": "error when writing into database", "status": flag * 3}))


# 文件保存方法
def handle_uploaded_file(f):
    today = str(datetime.date.today())  # 获得今天日期
    file_name = today + '_' + f.name  # 获得上传来的文件名称,加入下划线分开日期和名称
    file_path = os.path.join(os.path.dirname(__file__), 'upload_file')  # 拼装目录名称+文件名称
    os.makedirs(file_path, exist_ok=True)
    file_path = os.path.join(file_path, file_name)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()
    return file_path


def split_name(request):
    name = request.body
    name = bytes.decode(name)
    name = json.loads(name)
    if name is None or name == {}:
        return HttpResponse(json.dumps({"first_name": '', "middle_name": "", "last_name": "", "status": -1,
                                        "msg": "no given name"}))
    result = utils.util_text_operation.analyze_person_name(name)
    return HttpResponse(json.dumps(result))

