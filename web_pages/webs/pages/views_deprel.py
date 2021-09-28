import datetime
import json
import os
import uuid
from pathlib import Path

from django.http import HttpResponse
from django.shortcuts import render

from utils.nlp.nlp_utils import dd_parser_caller, generate_dep_rel_graph
from utils.task_understanding.command_resolver import resolve
from utils.initialization import wrap_result, ini_result, RESULT_DATA, RESULT_MSG, RESULT_CODE, topic, mqtt_client


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

    if data is None or data == "":
        result[RESULT_CODE] = -301
        result[RESULT_MSG] = "no data is given"
        return wrap_result(result)

    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if not is_ajax or request.method != 'POST':

        result[RESULT_CODE] = -103
        result[RESULT_MSG] = "not supported request form (should be post and with ajax)"
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
        result[RESULT_CODE] = -402
        result[RESULT_MSG] = "no valid data is given"

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
        result[RESULT_CODE] = -103
        result[RESULT_MSG] = "not supported request form (should be post and with ajax)"
        return wrap_result(result)

    data = request.body  #
    if data is None or data == "":
        result[RESULT_CODE] = -301
        result[RESULT_MSG] = "no data is given"
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
            result[RESULT_CODE] = -303
            result[RESULT_MSG] = "failed to generate dependency graph"
            result[RESULT_DATA] = {'sentence': sentence, 'deprel': None, 'relation': str(relation), 'words': str(words), 'head': str(head)}
        else:
            print('successfully generate dependency graph')
            result[RESULT_CODE] = 300
            result[RESULT_MSG] = "success"
            result[RESULT_DATA] = {'sentence': sentence, 'deprel': graph_name+".png", 'relation': str(relation), 'words': str(words), 'head': str(head)}

    except TypeError:
        result[RESULT_CODE] = -302
        result[RESULT_MSG] = "no valid data is given"

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


basedir = Path(__file__).parent.parent.parent.parent  # 项目根目录
log_dir = basedir.joinpath('logs/')
current_dir = Path(__file__).parent