from django.shortcuts import render
from django.http import HttpResponse

import json
import os
import sys
import datetime
from configparser import ConfigParser
from pathlib import Path
import uuid

from utils.bib_util.utils import process_search_condition
from utils.nlp.utils import dd_parser_caller, generate_dep_rel_graph
from utils.file_util.utils import read_from_excel
from utils.task_understanding.command_resolver import resolve, ini_result
from utils.mqtt_util import MqttUtil

from utils.tmp_db import create_or_match_nodes_dict
from utils import query_data, db_operation, util_text_operation

os.environ["PATH"] += os.pathsep + 'D:\\Graphviz\\bin'

basedir = Path(__file__).parent.parent.parent.parent  # 项目根目录
current_dir = Path(__file__).parent
config_dir = Path(__file__).parent.parent
"""
日志配置
"""
log_dir = basedir.joinpath('logs/')

config_file_neo4j = os.path.join(config_dir, "neo4j.conf")
cf = ConfigParser()
cf.read(config_file_neo4j, encoding="utf-8")

"""
？？？
"""
address = cf.get("moduleAddress", "address1")
sys.path.append(address)
"""
neo4j 配置
"""
uri = cf.get("neo4j", "uri")
username = cf.get("neo4j", "username")
pwd = cf.get("neo4j", "pwd")

database_info = {"uri": uri, "username": username, "pwd": pwd}
"""
MQTT service
"""
broker = cf.get("mqtt", "broker")  # 连接地址
port = cf.get("mqtt", "port")  # 端口地址
topic = cf.get("mqtt", "topic")  # 主题topic
client_id = cf.get("mqtt", "clientPublish")

mqtt_client = MqttUtil(broker, port, client_id)

"""
load result field from config file 
"""
RESULT_DATA = cf.get("resultField", "data")
RESULT_MSG = cf.get("resultField", "message")
RESULT_CODE = cf.get("resultField", "code")
RESULT_COUNT = cf.get("resultField", "count")
"""
station file format
"""
SHEET_NAME = cf.get("stationFileFormat", "sheetname")
SHEET_TITLE = cf.get("stationFileFormat", "title").split(",")

"""
代码
"""


def wrap_result(result, ensure_ascii=False, content_type='application/json', charset='utf-8'):
    return HttpResponse(json.dumps(result, ensure_ascii=ensure_ascii), content_type=content_type, charset=charset)


def ini_result():
    result = {RESULT_DATA: None, RESULT_MSG: "", RESULT_CODE: -1}
    return result


"""
火车相关
"""


def resolve_coordinates(request):
    return render(request, 'coordinates.html')


def parse_excel_stations(request):
    """
    从Excel文件中解析出车站信息，提取的结果是excel表中的各个数据
    :param request:
    :return:
    """
    result = ini_result()
    try:
        file = request.FILES.getlist('file')
    except:
        result[RESULT_MSG] = 'failed to retrieve file in the request'
        result[RESULT_CODE] = -701
        return wrap_result(result)
    if file is None or len(file) == 0:
        result[RESULT_MSG] = 'No file in the request'
        result[RESULT_CODE] = -702
        return wrap_result(result)

    # 打开Excel文件# todo support multiple files
    result = read_from_excel(file[0], SHEET_NAME, SHEET_TITLE)

    return wrap_result(result)


"""
文献管理相关
"""


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
            result[RESULT_CODE] = -601
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

    parameters = process_search_condition(pub_info)  # 封装数据为后台数据库能够接收的格式
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
    if query_result[RESULT_CODE] < 0:  # 返回的code有1，2，0，-1共四中
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
        result[RESULT_CODE] = -601
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

    query_result = query_data.query_by_multiple_field_count(database_info, parameters, "PUBLICATION")  # -1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录

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


"""
意图理解相关
"""


def deprel(request):
    return render(request, 'deprel.html')


def save_deprel_result(request):
    """
    存储页面标注结果,将修改信息存储在txt文件中，格式为：id 提交评论时间 句子 解析文件路径(名) relation words head 是否有问题 comments（\t 隔开）
    :param request:
    :return:
    """

    result = ini_result()

    data = request.body
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if not is_ajax or request.method != 'POST':

        result['code'] = -103
        result['msg'] = "not supported request form (should be post and with ajax)"
        return wrap_result(result)

    try:
        data = bytes.decode(data)
        data = json.loads(data)

        record_uuid = str(uuid.uuid1())
        record_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sentence = data.get('sentence', '-')

        result_file_name = data.get('image_path', '-')

        words = data.get('words', '-')
        relation = data.get('relation', '-')
        head = data.get('head', '-')

        is_correct = data.get('is_problematic', '-')
        comments = data.get('comments', '-')

        tmp = [record_uuid, record_time, sentence, result_file_name, words, relation, head, is_correct, comments]
        tmp = '\t'.join(tmp)

        with open(log_dir.joinpath('dep_rel_service_log.log'), 'a+', encoding="utf-8") as f:
            f.write(tmp + '\n')

        result[RESULT_MSG] = "successfully saved"
        result[RESULT_CODE] = 400
        # result["field"] = data

    except TypeError:
        result['code'] = -402
        result['msg'] = "no valid data is given"

    return wrap_result(result)


def resolve_deprel(request):
    """
    由“开始解析”按钮触发的对给定句子的解析，对外返回解析结果。

    注：采用ajax + post方式，header指定{"X-Requested-With"："XMLHttpRequest", "Content-Type"："application/x-www-form-urlencoded"}

    :param request: 包含待解析sentence
    :return:
    """
    result = ini_result()
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if not is_ajax or request.method != 'POST':
        result['code'] = -103
        result['msg'] = "not supported request form (should be post and with ajax)"
        return wrap_result(result)

    data = request.body  #
    if data is None or data == "":
        result['code'] = -301
        result['msg'] = "no data is given"
        return wrap_result(result)

    try:
        data = bytes.decode(data)
        data = json.loads(data)
        sentence = data["sentence"]

        # 调用ddparser处理结果-命名规则：sentence+timestamp
        resolve_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        words, head, relation, pos_tag = dd_parser_caller(sentence)

        # 生成依存关系图
        graph_name = sentence + '_' + resolve_time  # 拼装:句子+时间

        g = generate_dep_rel_graph(os.path.join(current_dir, 'static/images/cache'), graph_name,
                                   words, relation, head)
        if g is None:
            print("failed to generate dependency graph")
            result['code'] = -303
            result['msg'] = "failed to generate dependency graph"
            result[RESULT_DATA] = {'sentence': sentence, 'deprel': None, 'relation': str(relation), 'words': str(words), 'head': str(head)}
        else:
            print('successfully generate dependency graph')
            result['code'] = 300
            result['msg'] = "success"
            result[RESULT_DATA] = {'sentence': sentence, 'deprel': graph_name+".png", 'relation': str(relation), 'words': str(words), 'head': str(head)}

    except TypeError:
        result['code'] = -302
        result['msg'] = "no valid data is given"

    return wrap_result(result)


def command_resolve(request):
    """
    基本功能，按照模板匹配的方式处理指令，为进行grounding
    :return:
    """
    request_method = request.method
    result = ini_result()
    if request_method != 'GET':
        result[RESULT_CODE] = -101
        result["message"] = "request method should be get"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')

    command = request.GET.get("command", None)
    session_id = request.GET.get("sessionId", '')
    robot_id = request.GET.get("robotId", '')

    if not command or not session_id or not robot_id:
        result[RESULT_CODE] = -802
        result["message"] = "No command found"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')

    result = resolve(command)
    if not result["success"]:
        result[RESULT_CODE] = -803
        result["message"] = "failed to resolve"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')

    task = result.get("task", None)
    if task is None:
        result[RESULT_CODE] = -804
        result["message"] = "success without task information"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')

    task["sessionId"] = session_id
    task["robotId"] = robot_id

    # todo send to reasoning service
    # ret = requests.post(PLANNING_URL, json=task).text

    msg_to_front = {'input': command, 'output': task}
    msg_to_front = json.dumps(msg_to_front, ensure_ascii=False)

    mqtt_client.publish(topic, msg_to_front)

    ret = '{RESULT_CODE: 200}'
    try:
        ret_content = json.loads(ret)
        reason_code = ret_content.get(RESULT_CODE, 0)
    except json.JSONDecodeError or TypeError:
        result[RESULT_CODE] = 801
        result["message"] = "success but failed to send to reasoning module"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')

    if reason_code != 200:
        result[RESULT_CODE] = 802
        result["message"] = "success but reasoning failed"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')

    result[RESULT_CODE] = 800
    result["message"] = "success"

    print_log(request, result)

    return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')


def print_log(request, response):
    ip_address = request.META.get('REMOTE_ADDR', "")
    api_method = request.method
    api_path = request.META.get("PATH_INFO", "") + request.META.get("QUERY_STRING", "")
    if len(api_path) == 0:
        api_path = None

    request_data = request.GET.get("command", "")

    with open(log_dir.joinpath('tu_service_log.log'), 'a+', encoding="utf-8") as f:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(current_time + " " + ip_address + " " + api_method + " " + api_path + '->' + request_data + '->' +
                str(response) + '\n')

    # # 记录慢查询日志，在日志处理器函数中会将其写入到文件中
    # for query in get_debug_queries():
    #     if query.duration >= app.config['FLASK_SLOW_DB_QUERY_TIME']:
    #         app.logger.warning(
    #             'Slow query: %s\n Parameters: %s\n Duration: %fs\n Context: %s'
    #             % (query.statement, query.parameters, query.duration, query.context))
    # pass

# 以上是意图理解相关网页
######################################################################################


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
            if pub_info is None:
                result[RESULT_MSG] = "no data is given"
                result[RESULT_CODE] = -3
                return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
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
        query_result = create_or_match_nodes_dict(pub_info, "PUBLICATION", database_info, return_type=return_type, to_create=to_create)

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


def get_vis_data():
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
        node_info = request.body  # 处理后是dict，直接传到后台写入数据库就可以了
        if node_info is None or node_info == "":
            result[RESULT_CODE] = 0
            result[RESULT_MSG] = "no data is given"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except json.JSONDecodeError or TypeError:
            result[RESULT_CODE] = -1
            result[RESULT_MSG] = "given data is not a json string"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        # 调方法写数据库
        flag = db_operation.create_or_match_persons(node_info, mode=2)
        if flag[RESULT_CODE] == 1:
            result[RESULT_CODE] = 1
            result[RESULT_MSG] = "successfully write into database"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        else:
            result[RESULT_CODE] = flag
            result[RESULT_MSG] = "error when writing into database" + flag[RESULT_MSG]
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    else:
        result[RESULT_CODE] = -10
        result[RESULT_MSG] = "not supported request form"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')


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
            result[RESULT_CODE] = 0
            result[RESULT_MSG] = "no data is given"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except json.JSONDecodeError or TypeError:
            result[RESULT_CODE] = -1
            result[RESULT_MSG] = "given data is not a json string"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        # 调方法写数据库
        flag = db_operation.create_or_match_venues(node_info, mode=2)
        if flag[RESULT_CODE] == 1:
            result[RESULT_CODE] = 1
            result[RESULT_MSG] = "successfully write into database"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        else:
            result[RESULT_CODE] = flag
            result[RESULT_MSG] = "error when writing into database" + flag[RESULT_MSG]
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    else:
        result[RESULT_CODE] = -10
        result[RESULT_MSG] = "not supported request form"
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')


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
            result[RESULT_CODE] = 0
            result[RESULT_MSG] = "no data is given"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
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
        flag = db_operation.query_or_create_relation(None, source_type, source_id, target_type, target_id, rel_type)
        if flag[RESULT_CODE] > 0:
            result[RESULT_CODE] = 1
            result[RESULT_MSG] = "successfully write into database"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
        else:
            result[RESULT_CODE] = flag[RESULT_CODE]
            result[RESULT_MSG] = "error when writing into database" + flag[RESULT_MSG]
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
            result[RESULT_CODE] = 0
            result[RESULT_MSG] = "no data is given"
            return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
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
        flag = db_operation.revise_publications(pub_info)
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
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'POST':
        node_info = request.body
        if node_info is None or node_info == "":
            return HttpResponse(json.dumps({RESULT_MSG: "no data is given", RESULT_CODE: 0}))
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except json.JSONDecodeError or TypeError:
            return HttpResponse(json.dumps({RESULT_MSG: "given data is not a json string", RESULT_CODE: -1}))
        # 调方法写数据库
        flag = db_operation.revise_persons(node_info)
        if flag == 1:
            return HttpResponse(json.dumps({RESULT_MSG: "successfully write into database", RESULT_CODE: 1}))
        else:
            return HttpResponse(json.dumps({RESULT_MSG: "error when writing into database", RESULT_CODE: flag*3}))
    else:
        return HttpResponse(json.dumps({RESULT_MSG: "not supported request form", RESULT_CODE: -2}))


def revise_venue(request):
    """
    利用cypher修改person
    :param request:
    :return:{RESULT_MSG: "no data is given", RESULT_CODE: 0} 0:无参数,-1:参数格式错误,
    """
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax and request.method == 'POST':
        node_info = request.body
        if node_info is None or node_info == "":
            return HttpResponse(json.dumps({RESULT_MSG: "no data is given", RESULT_CODE: 0}))
        try:
            node_info = bytes.decode(node_info)
            node_info = json.loads(node_info)
        except json.JSONDecodeError or TypeError:
            return HttpResponse(json.dumps({RESULT_MSG: "given data is not a json string", RESULT_CODE: -1}))
        # 调方法写数据库
        flag = db_operation.revise_venues(node_info)
        if flag == 1:
            return HttpResponse(json.dumps({RESULT_MSG: "successfully write into database", RESULT_CODE: 1}))
        else:
            return HttpResponse(json.dumps({RESULT_MSG: "error when writing into database", RESULT_CODE: flag*3}))
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
        flag = query_data.query_pub_by_multiple_field(parameters)  # -1:没有传入数据;0:未搜索到数据；2：搜索到多条记录；1：搜索到1条记录
        data = json.loads(flag)
        if data[RESULT_CODE] < 1:
            return HttpResponse(flag)
        else:  # 返回数据
            count = 1
            pubs = []
            for pub in data[RESULT_DATA]:
                pub["ID"] = count
                if pub["pages1"] == "" or pub["pages2"] == "":
                    pub["pages"] = ""
                else:
                    pub["pages"] = str(pub["pages1"]) + "-" + str(pub["pages2"])
                pub.pop("pages1")
                pub.pop("pages2")
                count += 1
                pubs.append(pub)
            data[RESULT_DATA] = pubs
            data[RESULT_CODE] = 0
            return HttpResponse(json.dumps(data))
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
        flag = query_data.query_person_or_venue_by_multiple_field(parameters, "PERSON")
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
    if request.method == 'POST':
        is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
        if is_ajax:
            the_paras = request.body
            if the_paras is None:
                return HttpResponse(json.dumps({RESULT_MSG: "no data is given", RESULT_CODE: 0, RESULT_DATA: "", "count": 0}))
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
        flag = query_data.query_person_or_venue_by_multiple_field(parameters, "VENUE")
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
            data = query_data.query_one_pub_by_uuid(the_uuid)
            if data[RESULT_CODE] != 1:
                return HttpResponse(json.dumps({RESULT_MSG: data[RESULT_MSG], RESULT_CODE: -1}))
            else:
                return HttpResponse(json.dumps({RESULT_MSG: data[RESULT_MSG], RESULT_CODE: 1, RESULT_DATA: data[RESULT_DATA]}))
    return HttpResponse(json.dumps({RESULT_MSG: "not ajax request or the request method is not get", RESULT_CODE: -1}))


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
            return HttpResponse(json.dumps({RESULT_MSG: "successfully write into database", RESULT_CODE: 1}))
        else:
            return HttpResponse(json.dumps({RESULT_MSG: "error when writing into database", RESULT_CODE: flag * 3}))


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
    person_name = request.body
    result = {"first_name": '', "middle_name": "", "last_name": "", RESULT_CODE: -1,
              RESULT_MSG: "no given name"}
    try:
        person_name = bytes.decode(person_name)
        person_name = json.loads(person_name)
    except json.JSONDecodeError or TypeError:
        print("error")
        HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    if person_name is None or person_name == {}:
        return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
    result = util_text_operation.analyze_person_name(person_name)
    return HttpResponse(json.dumps(result, ensure_ascii=False), content_type='application/json', charset='utf-8')
