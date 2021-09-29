from django.shortcuts import render
from django.http import HttpResponse

import json
import os
import datetime

import utils.db_operation
import utils.db_util.operations
from utils.bib_util.extraction import extract_bib_info_from_file, extract_publication_from_bib_info
from utils.bib_util.utils import process_search_condition
from utils.file_util.utils import save_file_stream_on_disk
from utils.initialization import wrap_result, ini_result, initialize_neo4j_driver, RESULT_DATA, RESULT_MSG, RESULT_CODE, \
    RESULT_COUNT
from utils.db_util.operations import create_or_match_nodes as create_or_match_nodes, query_or_create_relation

from model_files.bibModels import Publication, Venue, Person

from utils import db_operation
from utils.nlp import text_utils

"""
文献管理相关
"""


def search_home(request):
    return render(request, 'search_home.html')


def search_result(request):
    return render(request, 'search_result.html')


def search_publication_new(request):
    """
    这个实现的是在搜索结果界面的功能，包括高级搜索、查询和搜索数据的返回等，只查询，不创建。AJAX + POST
    :param request:
    :return:
    """
    result = ini_result()
    result[RESULT_COUNT] = 0

    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if request.method != 'POST':
        result[RESULT_MSG] = "not support request method, should be post"
        result[RESULT_CODE] = -102
        return wrap_result(result)

    # 解析传递参数，高级搜索的条件
    if is_ajax:
        the_paras = request.body
        if the_paras is None:
            result[RESULT_MSG] = "no query condition is given"
            result[RESULT_CODE] = -301
            return wrap_result(result)

        try:
            pub_info = bytes.decode(the_paras)
            pub_info = json.loads(pub_info)
        except json.JSONDecodeError or TypeError:  # todo chech when this will happen
            result[RESULT_MSG] = "failed to serialize parameters"
            result[RESULT_CODE] = -602
            return wrap_result(result)
        page = None
        limit = None
    else:
        the_paras = request.POST
        pub_info = the_paras.get("param", None)
        if pub_info is None:
            result[RESULT_MSG] = "no valid info is provided for search"
            result[RESULT_CODE] = -601
            return wrap_result(result)

        pub_info = json.loads(pub_info)
        page = the_paras.get("page", None)
        limit = the_paras.get("limit", None)

    query_conditions = process_search_condition(pub_info)  # 封装数据为后台数据库能够接收的格式
    # 分页条件
    if page is not None and limit is not None:
        try:
            page = int(page)
            limit = int(limit)
        except ValueError:
            page = None
            limit = None
    # 查询
    driver = initialize_neo4j_driver()
    query_result = utils.db_util.operations.query_bib_node_by_multiple_field(driver, "PUBLICATION", query_conditions, page, limit)

    if query_result["code"] != 905:  # 返回的code有1，2，0，-1共四中
        return wrap_result(result)

    # 处理返回的数据
    count = 1
    pubs = []
    for pub in query_result[RESULT_DATA]:
        pub["ID"] = count
        if pub["pages1"] == "" or pub["pages2"] == "":
            pub["pages"] = ""
        else:
            pub["pages"] = str(pub["pages1"]) + "-" + str(pub["pages2"])
        count += 1
        pubs.append(pub)
    if is_ajax:
        result[RESULT_MSG] = "done"
        result["count"] = len(pubs)  # todo 检查是否正确？
        result[RESULT_CODE] = query_result[RESULT_CODE]
        result[RESULT_DATA] = pubs
    else:
        result[RESULT_MSG] = "done"
        result["count"] = pub_info["count"]
        result[RESULT_CODE] = query_result[RESULT_CODE]
        result[RESULT_DATA] = pubs
    return wrap_result(result)


def search_publication_count(request):
    """
    根据搜索条件，计算有多少条数据满足条件. should be post and ajax
    :param request:
    :return:
    """
    result = ini_result()
    result[RESULT_COUNT] = -1
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if not is_ajax or request.method != 'POST':
        result[RESULT_CODE] = -103
        result[RESULT_MSG] = "not support request method, should be post"
        result["count"] = 0
        return wrap_result(result)

    pub_info = request.body
    if pub_info is None or pub_info == "":
        result[RESULT_CODE] = -301
        result[RESULT_MSG] = "no query condition is given"
        return wrap_result(result)

    try:
        pub_info = bytes.decode(pub_info)
        pub_info = json.loads(pub_info)
    except json.JSONDecodeError or TypeError:
        result[RESULT_CODE] = -603
        result[RESULT_MSG] = "query condition should be json string"
        return wrap_result(result)

    if pub_info is None:
        result[RESULT_CODE] = -601
        result[RESULT_MSG] = "no query condition is given"
        return wrap_result(result)

    # 封装数据为后台数据库能够接收的格式
    parameters = process_search_condition(pub_info)
    if parameters is None:
        result[RESULT_CODE] = -604
        result[RESULT_MSG] = "搜索条件解析失败，请重试"
        result["count"] = 0
        return wrap_result(result)

    driver = initialize_neo4j_driver()
    query_result = utils.db_util.operations.query_by_multiple_field_count(driver, parameters, "PUBLICATION")  # -1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录

    result[RESULT_CODE] = query_result[RESULT_CODE]
    result[RESULT_MSG] = query_result.get(RESULT_MSG, "")
    result["count"] = query_result.get("count", -1)
    return wrap_result(result)


def view_pdf(request):
    return render(request, 'view_pdf.html')


def show_pdf(request):
    # todo 实现文件存储
    return render(request)


def manage(request):
    return render(request, 'manage.html')


def upload_bib_add_record(request):
    result = ini_result()
    try:
        files = request.FILES.getlist('file')
    except:
        result[RESULT_MSG] = 'failed to retrieve file in the request'
        result[RESULT_CODE] = -701
        return wrap_result(result)

    if files is None or len(files) == 0:
        result[RESULT_MSG] = 'No file in the request'
        result[RESULT_CODE] = -702
        return wrap_result(result)

    driver = initialize_neo4j_driver()
    dir = os.path.join(os.path.dirname(__file__), 'upload_file')  # 拼装目录名称+文件名称

    file_not_processed = []
    for file in files:
        today = str(datetime.date.today())  # 获得今天日期
        filename = today + '_' + file.name  # 获得上传来的文件名称,加入下划线分开日期和名称

        file_path = save_file_stream_on_disk(file, dir, filename)  # 处理上传来的文件

        if file_path is None:
            file_not_processed.append(file)
            continue

        publication_info = extract_bib_info_from_file(file_path)  # dict

        pubs = []
        for entry in publication_info:
            # 解析文献
            tmp_result_pub = extract_publication_from_bib_info(entry)
            if tmp_result_pub[RESULT_CODE] == 1001:
                pubs.append(tmp_result_pub[RESULT_DATA])

        pubs = None if pubs == [] else pubs
        db_pub_result = create_or_match_nodes(driver, pubs, return_type="class", to_create=True)
        if db_pub_result[RESULT_CODE] != 1303:
            result[RESULT_CODE] = 00
            result[RESULT_MSG] = "Publication节点生成失败"
        else:
            result[RESULT_CODE] = 00
            result[RESULT_MSG] = "Publication节点生成成功"

        os.remove(file_path)

    if len(file_not_processed) > 0:
        result[RESULT_CODE] = -201
        result[RESULT_MSG] = "not all files are written into database"
        result[RESULT_DATA] = file_not_processed
    else:
        result[RESULT_CODE] = 200
        result[RESULT_MSG] = "success"

    return wrap_result(result)


"""
未修正
"""


def add_publication(request):
    """
    向cypher添加pub ---- 已改
    :param request:
    :return:
    """
    result = ini_result()
    result[RESULT_COUNT] = -1

    if request.method == 'POST':
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        if is_ajax:
            pub_info = request.body

            if pub_info is None or pub_info == "":
                result[RESULT_CODE] = -301
                result[RESULT_MSG] = "no data is given"
                return wrap_result(result)

            try:
                pub_info = bytes.decode(pub_info)
                pub_info = json.loads(pub_info)
            except json.JSONDecodeError:
                result[RESULT_MSG] = "given data is not a json string"
                result[RESULT_CODE] = -4
                return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        else:
            pub_info = request.POST
            if pub_info is None:
                result[RESULT_MSG] = "no data is given"
                result[RESULT_CODE] = -3
                return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
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
            result[RESULT_MSG] = "unsupported paper type"
            result[RESULT_CODE] = -5
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        # 调方法写数据库
        query_result = create_or_match_nodes(driver, pub_info, return_type=return_type, to_create=to_create)

        result[RESULT_MSG] = query_result.get(RESULT_MSG, "查询数据接口无返回值")
        result[RESULT_CODE] = query_result.get(RESULT_CODE, -6)
        result[RESULT_DATA] = query_result.get(RESULT_DATA, [])
        try:
            result["count"] = len(result[RESULT_DATA])
        except KeyError:
            result["count"] = 0
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    else:
        result[RESULT_MSG] = "请求方式应为post"
        result[RESULT_CODE] = -7
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')


def index(request):
    # return HttpResponse('welcome to the front page')
    return render(request, 'index.html')


def about(request):
    pos = request.GET.get("pos", None)
    if pos is None:
        return render(request, 'about_backup.html', {"position": json.dumps('null')})
    else:
        return render(request, 'about_backup.html', {"position": json.dumps(pos)})


def about2(request):
    pos = request.GET.get("pos", None)
    if pos is None:
        return render(request, 'about.html', {"position": json.dumps('null')})
    else:
        return render(request, 'about.html', {"position": json.dumps(pos)})


def table(request):
    # return HttpResponse('welcome to the front page')
    return render(request, 'table.html')


def net(request):
    return render(request, "net.html")


def get_sample_data(request):
    page = request.GET.get("page", None)
    limit = request.GET.get("limit", None)
    # limit = None
    driver = initialize_neo4j_driver()

    person_list = []
    members = cf.get("cpwlGroup", "members")
    members_cn = cf.get("cpwlGroup", "members_cn")

    person_list.extend(members.split(" and "))
    person_list.extend(members_cn.split(" and "))
    person_list = [item.upper() for item in person_list]

    if page is None or limit is None:
        data = utils.db_util.operations.query_person_pub_venue_by_person_name(driver, person_list)
    else:
        data = utils.db_util.operations.query_person_pub_venue_by_person_name(driver, person_list, (int(page) - 1) * int(limit), int(limit))
    return HttpResponse(data)


def get_vis_data():
    driver = initialize_neo4j_driver()

    person_list = []
    members = cf.get("cpwlGroup", "members")
    members_cn = cf.get("cpwlGroup", "members_cn")

    person_list.extend(members.split(" and "))
    person_list.extend(members_cn.split(" and "))
    person_list = [item.upper() for item in person_list]

    query_result = utils.db_util.operations.query_person_pub_venue_by_person_name(driver, person_list)

    if query_result["status"] == 1:
        return wrap_result(query_result)
    else:
        return wrap_result("")


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
            except IndexError or KeyError:
                print("解析失败")
        except json.JSONDecodeError or TypeError:
            data = [{"firstName": "", "middleName": "", "lastName": "", "ranking": "1"}]

    json_str = {RESULT_CODE: 0, RESULT_MSG: "successfully queried data", "count": 1, RESULT_DATA: data}
    return HttpResponse(json.dumps(json_str, ensure_ascii=False), content_type='application/json', charset='utf-8')


def add_person(request):
    """
    向cypher添加person
    :param request:
    :return: {RESULT_MSG: "", RESULT_CODE: 0}, 0:缺少参数；-1：参数格式错误;-10:请求方式错误，-2~-5见create_or_match_persons方法
    """
    result = ini_result()
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'POST':
        result[RESULT_CODE] = -103
        result[RESULT_MSG] = "not supported request form"
        return wrap_result(result)

    node_info = request.body  # 处理后是dict，直接传到后台写入数据库就可以了

    if node_info is None or node_info == "":
        result[RESULT_CODE] = -301
        result[RESULT_MSG] = "no data is given"
        return wrap_result(result)

    try:
        node_info = bytes.decode(node_info)
        node_info = json.loads(node_info)
    except json.JSONDecodeError or TypeError:
        result[RESULT_CODE] = -1
        result[RESULT_MSG] = "given data is not a json string"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    # 调方法写数据库
    driver = initialize_neo4j_driver()

    person = [Person("", node_info)]
    tmp_result = create_or_match_nodes(driver, person)
    if tmp_result[RESULT_CODE] != 1303:
        result[RESULT_CODE] = 00
        result[RESULT_MSG] = "Person节点生成失败"
    else:
        result[RESULT_CODE] = 1
        result[RESULT_MSG] = "Person节点生成成功"

    return wrap_result(result)


def add_venue(request):
    """
    向cypher添加venue
    :param request:
    :return: {RESULT_MSG: "", RESULT_CODE: 0}, 0:缺少参数；-1：参数格式错误;-10:请求方式错误，-2~-5见create_or_match_persons方法
    """
    result = ini_result()
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'POST':
        node_info = request.body  # 处理后是dict，直接传到后台写入数据库就可以了

        if node_info is None or node_info == "":
            result[RESULT_CODE] = -301
            result[RESULT_MSG] = "no data is given"
            return wrap_result(result)

        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except json.JSONDecodeError or TypeError:
            result[RESULT_CODE] = -1
            result[RESULT_MSG] = "given data is not a json string"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        # 调方法写数据库
        driver = initialize_neo4j_driver()

        # 应先从node_info构建Venue，然后创建
        venue = [Venue("", node_info)]

        db_ven_result = create_or_match_nodes(driver, venue, return_type="class", to_create=True)
        if db_ven_result[RESULT_CODE] != 1303:
            result[RESULT_CODE] = 00
            result[RESULT_MSG] = "Venue节点生成失败"
        else:
            result[RESULT_CODE] = 1
            result[RESULT_MSG] = "Venue节点生成成功"

    else:
        result[RESULT_CODE] = -10
        result[RESULT_MSG] = "not supported request form"
    return wrap_result(result)


def add_relation(request):
    """
    向cypher添加relation
    :param request:
    :return: {RESULT_MSG: "", RESULT_CODE: 0}, 0:缺少参数；-1：参数格式错误;-10:请求方式错误，-2~-5见create_or_match_persons方法
    """
    result = ini_result()
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'POST':
        node_info = request.body  # 处理后是dict，直接传到后台写入数据库就可以了

        if node_info is None or node_info == "":
            result[RESULT_CODE] = -301
            result[RESULT_MSG] = "no data is given"
            return wrap_result(result)

        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except json.JSONDecodeError or TypeError:
            result[RESULT_CODE] = -1
            result[RESULT_MSG] = "given data is not a json string"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        # 调方法写数据库
        source_id = node_info["sourceID"]
        source_type = node_info["sourceType"]
        target_id = node_info["targetID"]
        target_type = node_info["targetType"]
        rel_type = node_info["relType"]

        driver = initialize_neo4j_driver()
        query_result = query_or_create_relation(driver, source_type, source_id, target_type, target_id, rel_type)

        if query_result[RESULT_CODE] == 1306:
            result[RESULT_CODE] = 1
            result[RESULT_MSG] = "successfully write into database"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        else:
            result[RESULT_CODE] = 0
            result[RESULT_MSG] = "error when writing into database: " + query_result[RESULT_MSG]
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    else:
        result[RESULT_CODE] = -10
        result[RESULT_MSG] = "not supported request form"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')


def revise_publication(request):
    """
    利用cypher修改pub
    :param request:
    :return:
    """
    result = ini_result()
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'POST':
        pub_info = request.body

        if pub_info is None or pub_info == "":
            result[RESULT_CODE] = -301
            result[RESULT_MSG] = "no data is given"
            return wrap_result(result)

        try:
            pub_info = bytes.decode(pub_info)
            pub_info = json.loads(pub_info)
        except json.JSONDecodeError or TypeError:
            result[RESULT_CODE] = -1
            result[RESULT_MSG] = "given data is not a json string"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
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
            result[RESULT_CODE] = -3
            result[RESULT_MSG] = "unsupported paper type"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        # 特殊处理，pages
        p1 = pub_info.get("pages1", None)
        p2 = pub_info.get("pages2", None)
        if p1 is not None and p2 is not None:
            pub_info["pages"] = str(p1) + "-" + str(p2)
        # 调方法写数据库
        driver = initialize_neo4j_driver()
        flag = db_operation.revise_publications(driver, pub_info)
        if flag == 1:
            result[RESULT_CODE] = 1
            result[RESULT_MSG] = "successfully write into database"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        else:
            result[RESULT_CODE] = flag * 3
            result[RESULT_MSG] = "error when writing into database"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    else:
        result[RESULT_CODE] = -2
        result[RESULT_MSG] = "not supported request form"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')


def revise_person(request):
    """
    利用cypher修改person
    :param request:
    :return:{RESULT_MSG: "no data is given", RESULT_CODE: 0} 0:无参数,-1:参数格式错误,
    """
    result = ini_result()
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'POST':
        node_info = request.body

        if node_info is None or node_info == "":
            result[RESULT_CODE] = -301
            result[RESULT_MSG] = "no data is given"
            return wrap_result(result)

        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except json.JSONDecodeError or TypeError:
            return HttpResponse(json.dumps({RESULT_MSG: "given data is not a json string", RESULT_CODE: -1}))
        # 调方法写数据库
        driver = initialize_neo4j_driver()
        flag = db_operation.revise_persons(driver, node_info)
        if flag == 1:
            return HttpResponse(json.dumps({RESULT_MSG: "successfully write into database", RESULT_CODE: 1}))
        else:
            return HttpResponse(json.dumps({RESULT_MSG: "error when writing into database", RESULT_CODE: flag * 3}))
    else:
        return HttpResponse(json.dumps({RESULT_MSG: "not supported request form", RESULT_CODE: -2}))


def revise_venue(request):
    """
    利用cypher修改person
    :param request:
    :return:{RESULT_MSG: "no data is given", RESULT_CODE: 0} 0:无参数,-1:参数格式错误,
    """
    result = ini_result()
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'POST':
        node_info = request.body

        if node_info is None or node_info == "":
            result[RESULT_CODE] = -301
            result[RESULT_MSG] = "no data is given"
            return wrap_result(result)

        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except json.JSONDecodeError or TypeError:
            return HttpResponse(json.dumps({RESULT_MSG: "given data is not a json string", RESULT_CODE: -1}))
        # 调方法写数据库
        driver = initialize_neo4j_driver()
        flag = db_operation.revise_venues(driver, node_info)
        if flag == 1:
            return HttpResponse(json.dumps({RESULT_MSG: "successfully write into database", RESULT_CODE: 1}))
        else:
            return HttpResponse(json.dumps({RESULT_MSG: "error when writing into database", RESULT_CODE: flag * 3}))
    else:
        return HttpResponse(json.dumps({RESULT_MSG: "not supported request form", RESULT_CODE: -2}))


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
            return HttpResponse(json.dumps({RESULT_MSG: "no data is given", RESULT_CODE: 0}))
        # 调方法写数据库
        title = the_paras.get("title", None)
        if title is None or title.strip() == "":
            return HttpResponse(
                json.dumps({RESULT_CODE: -2, RESULT_MSG: "标题一定要有才能搜索", "count": 0, RESULT_DATA: ""}))
        parameters = {"title": title}
        paper_type = the_paras.get("paperType", None)
        if paper_type is not None and paper_type.strip() != "":
            parameters["paperTypeEdit"] = paper_type
        driver = initialize_neo4j_driver()
        query_result = utils.db_util.operations.query_bib_node_by_multiple_field(driver, "PUBLICATION", parameters)  # -1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录

        return wrap_result(query_result)
    else:
        return HttpResponse(json.dumps({RESULT_CODE: -1, RESULT_MSG: "not support request method, should be post", "count": 0, RESULT_DATA: ""}))


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
            return HttpResponse(json.dumps({RESULT_MSG: "no data is given", RESULT_CODE: 0}))
        # 调方法写数据库
        full_name = the_paras.get("full_name", None)
        if full_name is None or full_name.strip() == "":
            return HttpResponse(
                json.dumps({RESULT_CODE: -2, RESULT_MSG: "标题一定要有才能搜索", "count": 0, RESULT_DATA: ""}))
        parameters = {"full_name": full_name}

        driver = initialize_neo4j_driver()
        flag = utils.db_util.operations.query_bib_node_by_multiple_field(driver, "PERSON", parameters)
        data = json.loads(flag)
        if data[RESULT_CODE] < 1:
            return HttpResponse(flag)
        else:  # 返回数据
            count = 1
            persons = []
            for person in data[RESULT_DATA]:
                person["ID"] = count
                count += 1
                persons.append(person)
            data[RESULT_DATA] = persons
            data[RESULT_CODE] = 0
            return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps({RESULT_CODE: -1, RESULT_MSG: "not support request method, should be post", "count": 0, RESULT_DATA: ""}))


def search_venue(request):
    """
    在neo4j中搜索venue ---- 已改
    :param request:
    :return:
    """
    result = ini_result()
    result[RESULT_COUNT] = -1
    if request.method == 'POST':
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        if is_ajax:
            the_paras = request.body

            if the_paras is None or the_paras == "":
                result[RESULT_CODE] = -301
                result[RESULT_MSG] = "no data is given"
                return wrap_result(result)

            try:
                the_paras = bytes.decode(the_paras)
                the_paras = json.loads(the_paras)
            except json.JSONDecodeError or TypeError:
                return HttpResponse(json.dumps({RESULT_MSG: "given data is not a json string", RESULT_CODE: -1, RESULT_DATA: "", "count": 0}))
            # page = None
            # limit = None
        else:
            the_paras = request.POST
            pub_info = the_paras.keys()
            if pub_info is None:
                return HttpResponse(json.dumps({RESULT_MSG: "no data is given", RESULT_CODE: 0, RESULT_DATA: "", "count": 0}))
            # page = the_paras.get("page", None)
            # limit = the_paras.get("limit", None)

        # 调方法写数据库
        title = the_paras.get("venue_name", None)
        if title is None or title.strip() == "":
            return HttpResponse(
                json.dumps({RESULT_CODE: -2, RESULT_MSG: "标题一定要有才能搜索", "count": 0, RESULT_DATA: ""}))
        parameters = {"venue_name": title}

        driver = initialize_neo4j_driver()
        flag = utils.db_util.operations.query_bib_node_by_multiple_field(driver, "VENUE", parameters)
        data = json.loads(flag)
        if data[RESULT_CODE] < 1:
            return HttpResponse(flag)
        else:  # 返回数据
            count = 1
            venues = []
            for venue in data[RESULT_DATA]:
                venue["ID"] = count
                count += 1
                venues.append(venue)
            data[RESULT_DATA] = venues
            data["count"] = count
            data[RESULT_CODE] = 1
            return HttpResponse(json.dumps(data))
    else:
        return HttpResponse(json.dumps({RESULT_CODE: -1, RESULT_MSG: "not support request method, should be post", "count": 0, RESULT_DATA: ""}))


def verify_auth(request):
    """
        验证用户-----现在是从固定列表中读取
        :param request:
        :return:
        """
    result = ini_result()
    user_list = {"user": "123456"}
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'GET':
        user = request.GET.get("username", None)
        password = request.GET.get("pwd", None)
        if user is None or password is None:
            result[RESULT_CODE] = -1
            result[RESULT_MSG] = "invalid request parameters"
        else:
            pwd_in_database = user_list.get(user, None)
            if pwd_in_database is None:
                result[RESULT_CODE] = -1
                result[RESULT_MSG] = "no registered user"
            elif pwd_in_database != password:
                result[RESULT_CODE] = -1
                result[RESULT_MSG] = "unmatched password"
            else:
                result[RESULT_CODE] = 1
                result[RESULT_MSG] = "matched user and password"
                result[RESULT_DATA] = {"user": user, "pwd": password}
    else:
        result[RESULT_CODE] = -1
        result[RESULT_MSG] = "invalid request"
    return result


def get_pib_info_for_edit(request):
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'GET':
        the_uuid = request.GET.get("id", None)
        if the_uuid is None:
            return HttpResponse(json.dumps({RESULT_MSG: "no valid publication id is provided.", RESULT_CODE: -1}))
        else:
            driver = initialize_neo4j_driver()
            data = utils.db_util.operations.query_one_pub_by_uuid(driver, the_uuid)
            if data[RESULT_CODE] != 1:
                return HttpResponse(json.dumps({RESULT_MSG: data[RESULT_MSG], RESULT_CODE: -1}))
            else:
                return HttpResponse(json.dumps({RESULT_MSG: data[RESULT_MSG], RESULT_CODE: 1, RESULT_DATA: data[
                    RESULT_DATA]}))
    return HttpResponse(json.dumps({RESULT_MSG: "not ajax request or the request method is not get", RESULT_CODE: -1}))


def pub_interface(request):
    return render(request, "public_interface.html")


def search_pub_popup(request):
    return render(request, "searchPub.html")


def search_person_popup(request):
    return render(request, "searchPerson.html")


def search_venue_popup(request):
    return render(request, "searchVenue.html")


def split_name(request):
    result = {"first_name": '', "middle_name": "", "last_name": "", RESULT_CODE: -1,
              RESULT_MSG: "no given name"}

    person_name = request.body

    if person_name is None or person_name == "":
        result[RESULT_CODE] = -301
        result[RESULT_MSG] = "no data is given"
        return wrap_result(result)

    try:
        person_name = bytes.decode(person_name)
        person_name = json.loads(person_name)
    except json.JSONDecodeError or TypeError:
        print("error")
        HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    if person_name is None or person_name == {}:
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    result = text_utils.analyze_person_name(person_name)
    return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
