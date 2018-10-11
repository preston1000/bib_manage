from django.shortcuts import render
from django.http import HttpResponse
from pages.models import Publication, Person, Venue, Affiliation, Place
import json
import sys
from utils import query_data, neo4j_access
import datetime, os
import django.forms as forms
sys.path.append('/Volumes/Transcend/projects/CPWL_service')


# Create your views here.
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
    if current_data is None:
        data = [{"firstName": "", "middleName": "", "lastName": "", "ranking": "1"}]
    else:
        try:
            data = json.loads(current_data)
            try:
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
            except:
                print("解析失败")
        except:
            data = [{"firstName": "", "middleName": "", "lastName": "", "ranking": "1"}]

    json_str = {"code": 0, "msg": "successfully queried data", "count": 1, "data": data}
    return HttpResponse(json.dumps(json_str))


def add_publication(request):
    """
    向cypher添加pub
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
        if pub_info["ENTRYTYPE"] == "0":
            pub_info["ENTRYTYPE"] = "ARTICLE"
        elif pub_info["ENTRYTYPE"] == "1":
            pub_info["ENTRYTYPE"] = "Book"
        elif pub_info["ENTRYTYPE"] == "2":
            pub_info["ENTRYTYPE"] = "Booklet"
        elif pub_info["ENTRYTYPE"] == "3":
            pub_info["ENTRYTYPE"] = "Conference"
        elif pub_info["ENTRYTYPE"] == "4":
            pub_info["ENTRYTYPE"] = "InBook"
        elif pub_info["ENTRYTYPE"] == "5":
            pub_info["ENTRYTYPE"] = "InCollection"
        elif pub_info["ENTRYTYPE"] == "6":
            pub_info["ENTRYTYPE"] = "InProceedings"
        elif pub_info["ENTRYTYPE"] == "7":
            pub_info["ENTRYTYPE"] = "Manual"
        elif pub_info["ENTRYTYPE"] == "8":
            pub_info["ENTRYTYPE"] = "MastersThesis"
        elif pub_info["ENTRYTYPE"] == "9":
            pub_info["ENTRYTYPE"] = "Misc"
        elif pub_info["ENTRYTYPE"] == "10":
            pub_info["ENTRYTYPE"] = "PhDThesis"
        elif pub_info["ENTRYTYPE"] == "11":
            pub_info["ENTRYTYPE"] = "Proceedings"
        elif pub_info["ENTRYTYPE"] == "12":
            pub_info["ENTRYTYPE"] = "TechReport"
        elif pub_info["ENTRYTYPE"] == "13":
            pub_info["ENTRYTYPE"] = "Unpublished"
        else:
            return HttpResponse(json.dumps({"msg": "unsupported paper type", "status": -3}))
        # 调方法写数据库
        flag = neo4j_access.build_network_of_publications(pub_info, mode=2, is_list=False)
        if flag == 1:
            return HttpResponse(json.dumps({"msg": "successfully write into database", "status": 1}))
        else:
            return HttpResponse(json.dumps({"msg": "error when writing into database", "status": flag*3}))
    else:
        return HttpResponse(json.dumps({"msg": "not supported request form", "status": -2}))


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
        if pub_info["ENTRYTYPE"] == "0":
            pub_info["ENTRYTYPE"] = "ARTICLE"
        elif pub_info["ENTRYTYPE"] == "1":
            pub_info["ENTRYTYPE"] = "Book"
        elif pub_info["ENTRYTYPE"] == "2":
            pub_info["ENTRYTYPE"] = "Booklet"
        elif pub_info["ENTRYTYPE"] == "3":
            pub_info["ENTRYTYPE"] = "Conference"
        elif pub_info["ENTRYTYPE"] == "4":
            pub_info["ENTRYTYPE"] = "InBook"
        elif pub_info["ENTRYTYPE"] == "5":
            pub_info["ENTRYTYPE"] = "InCollection"
        elif pub_info["ENTRYTYPE"] == "6":
            pub_info["ENTRYTYPE"] = "InProceedings"
        elif pub_info["ENTRYTYPE"] == "7":
            pub_info["ENTRYTYPE"] = "Manual"
        elif pub_info["ENTRYTYPE"] == "8":
            pub_info["ENTRYTYPE"] = "MastersThesis"
        elif pub_info["ENTRYTYPE"] == "9":
            pub_info["ENTRYTYPE"] = "Misc"
        elif pub_info["ENTRYTYPE"] == "10":
            pub_info["ENTRYTYPE"] = "PhDThesis"
        elif pub_info["ENTRYTYPE"] == "11":
            pub_info["ENTRYTYPE"] = "Proceedings"
        elif pub_info["ENTRYTYPE"] == "12":
            pub_info["ENTRYTYPE"] = "TechReport"
        elif pub_info["ENTRYTYPE"] == "13":
            pub_info["ENTRYTYPE"] = "Unpublished"
        else:
            return HttpResponse(json.dumps({"msg": "unsupported paper type", "status": -3}))
        # 调方法写数据库
        flag = neo4j_access.revise_publications(pub_info)
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
    :return:
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
        flag = query_data.query_one_pub_by_multiple_field(parameters)  # -1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
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


def upload_bib_add_record(request):
    for file in request.FILES.getlist('file'):
        file_path = handle_uploaded_file(file)  # 处理上传来的文件
        flag = neo4j_access.build_network_of_publications(file_path, mode=1)
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
