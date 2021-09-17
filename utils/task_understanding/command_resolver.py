
"""
    code:
302: failed to resolve dependency
303: unrecognized task type
200: successfully resolved

304: 无效参数: None
305: during grounding, the task type was not recognized beforehand
306: during grounding, failed to connect exhibition server by name
307: during grounding, no record of exhibition in DB
308: during grounding, multiple records of exhibition in DB
309: during grounding, failed to query exhibition info from  in DB
"""
# import copy
import requests
import json
from json import JSONDecodeError

from utils.nlp.utils import dd_parser_caller
from model_files.NLP.task_list import WORDS, POSSIBILITY, SYNONYMS_INVERSE
from model_files.NLP.config import QUERY_URL, QUERY_EXHIBITION_BY_NAME, PARAMETER_DELIMITER, PARAMETER_KEY_VALUE_DELIMITER
"""
TU 参数配置
"""

ELE_SUB = "sub"
ELE_OBJ = "obj"
ELE_TASK = "action"
ELE_PLACE = "evn"
ELE_CONTENT = "extra"

RESULT_CODE = "code"
RESULT_MSG = "message"
RESULT_SUCCESS = "success"
RESULT_TASK = "task"
RESULT_DATA = "data"

CONTENT_PLACE = "destination"
EXHIBITION_NAME_IN_DB = "名称"
ARGUMENT_EXHIBITION_NAME = "name"
DATA_FIELD_IN_RESPONSE_EXHIBITION_NAME = "data"


def resolve(command=None, grounding=False):
    """
        同时将结果返回给语音系统和自主决策，前者可处理"停止"任务，后者处理其他任务
    :param grounding:
    :param command: string
    :return: formalized task
    """
    result = ini_result()
    task = ini_task()  # task elements will be filled after task type is recognized

    # tokenization
    tokens, head, dep_rel, pos_tag = dd_parser_caller(command)

    if tokens is None or head is None or dep_rel is None:
        result[RESULT_CODE] = 302
        result[RESULT_MSG] = 'failed to resolve dependency'
        return result

    # check synonyms of core verb and determine task type
    type_result = find_task_type(tokens, pos_tag)
    task_type = type_result.get("task_type", None)
    selected_verb = type_result.get('key_verb', None)

    if not task_type or not selected_verb:
        result[RESULT_MSG] = 'unrecognized task type'
        result[RESULT_CODE] = 303
        return result

    task[ELE_TASK] = task_type

    # task elements
    task_elements = find_task_element(task_type, selected_verb, tokens, head, dep_rel, pos_tag)

    if task_elements:
        task.update(task_elements)

    # grounding
    if grounding:
        task = ground(task)

    # results
    result[RESULT_MSG] = 'successfully resolved'
    result[RESULT_CODE] = 200
    result[RESULT_SUCCESS] = True
    result[RESULT_TASK] = task
    return result


def ini_task():
    task = {ELE_TASK: None, ELE_SUB: None, ELE_OBJ: None, ELE_PLACE: None, ELE_CONTENT: None}
    return task


def ini_result():
    result = {RESULT_CODE: 0, RESULT_MSG: '', RESULT_SUCCESS: False, RESULT_TASK: None}
    return result


def find_task_type(tokens, pos_tag):
    """
    利用关键字匹配任务类型
    :param tokens: list of str, 分词
    :param pos_tag: list of str, 词性
    :return:
    """
    result = {"key_verb": None, "task_type": None}

    verbs = [tokens[i] for i, tag in enumerate(pos_tag) if tag == "v"]

    intersection = list(set(verbs) & set(WORDS))

    if not intersection:
        if verbs is None:
            prep = [tokens[ii] for ii, tag in enumerate(pos_tag) if tag == "p"]
            intersection = list(set(prep) & set(WORDS))
            if not intersection:
                return result

    selected_word = compare_possible(intersection)

    if selected_word is None:
        return result

    task_type = SYNONYMS_INVERSE[selected_word][0]
    result["key_verb"] = selected_word
    result["task_type"] = task_type

    return result


def compare_possible(words):
    """
    若有多个匹配的动词，选择概率最高的所对应的任务
    :param words: list of str
    :return: str, 概率最高的任务类型
    """
    selected_word = None
    selected_possibility = -1

    for word in words:
        possibility = POSSIBILITY.get(word, 1)
        if possibility > selected_possibility:
            selected_word = word
            selected_possibility = possibility
    return selected_word


def find_task_element(task_type, selected_verb, words, head, dep_rel, pos_tag):
    """
    解析任务元素
    :param task_type: str
    :param selected_verb: str
    :param words: list of str
    :param head: list of str
    :param dep_rel: list of str
    :param pos_tag: list of str
    :return:
    """
    elements = {}

    if not task_type:
        return None

    if task_type == "导览":  # 目的地，被带领人
        try:
            plc = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "VOB" and pos_tag[ii] in ['n', 'LOC']]  # find index of destination
            if plc:
                elements[ELE_CONTENT] = "destination=" + words[plc[0]]
                if len(plc) > 1:
                    print("multiple destination")

            father = [head[ii] for ii, tmp_word in enumerate(words) if tmp_word == selected_verb]
            if len(father) > 1:
                print("multiple father father")
            elif len(father) < 1:
                print(" no father")
                return None
            father = father[0]

            sibling = [ii for ii, tmp_head in enumerate(head) if words[ii] != selected_verb and tmp_head == father and pos_tag[ii] == 'PER']  # and (dep_rel[ii] == "DBL" or dep_rel[ii] == 'VOB')
            if sibling:
                elements[ELE_OBJ] = words[sibling[0]]
                if len(plc) > 1:
                    print("multiple person")

            elements[ELE_SUB] = "导览机器人"
            elements[ELE_PLACE] = "展厅"
        except ValueError or IndexError:
            print("failed to resolve task element for task 导览")
            return None
    elif task_type == '欢迎':
        try:
            verb_index = words.index(selected_verb)
            children = [ii for ii in range(len(words)) if head[ii] == (verb_index + 1)]
            ppl = [ii for ii in children if dep_rel[ii] == "VOB"]
            if ppl:
                elements[ELE_OBJ] = words[ppl[0]]

            elements[ELE_SUB] = "导览机器人"
            elements[ELE_PLACE] = "展厅"
        except ValueError:
            return None
    elif task_type == "讲解":  # 内容，听众
        try:
            verb_index = words.index(selected_verb)
            children = [ii for ii in range(len(words)) if head[ii] == (verb_index + 1)]
            plc = [ii for ii in children if dep_rel[ii] == "VOB"]
            if plc:
                elements[ELE_CONTENT] = "destination=" + words[plc[0]]

            adv = [ii for ii in children if dep_rel[ii] == "ADV"]
            if adv:
                children = [ii for ii in range(len(words)) if head[ii] == (adv[0] + 1)]
                ppl = [ii for ii in children if dep_rel[ii] == "POB"]
                if ppl:
                    elements[ELE_OBJ] = words[ppl[0]]
                else:
                    cmp = [ii for ii in children if dep_rel[ii] == "CMP"]
                    if cmp:
                        children = [ii for ii in range(len(words)) if head[ii] == (cmp[0] + 1)]
                        ppl = [ii for ii in children if dep_rel[ii] == "VOB"]
                        if ppl:
                            elements[ELE_OBJ] = words[ppl[0]]

            elements[ELE_SUB] = "导览机器人"
            elements[ELE_PLACE] = "展厅"
        except ValueError:
            print("error")
            return None
    # elif task_type == "讲解":  # 内容，听众
    #     try:
    #         verb_index = sentence.index(selected_verb)
    #         children = [ii for ii in range(len(sentence)) if head[ii] == (verb_index + 1)]
    #         plc = [ii for ii in children if dep_rel[ii] == "VOB"]
    #         if plc:
    #             elements[ELE_CONTENT] = sentence[plc[0]]
    #
    #         adv = [ii for ii in children if dep_rel[ii] == "ADV"]
    #         if adv:
    #             children = [ii for ii in range(len(sentence)) if head[ii] == (adv[0] + 1)]
    #             ppl = [ii for ii in children if dep_rel[ii] == "POB"]
    #             if ppl:
    #                 elements[ELE_OBJ] = sentence[ppl[0]]
    #
    #         elements[ELE_SUB] = "导览机器人"
    #         elements[ELE_PLACE] = "展厅"
    #     except ValueError:
    #         print("error")
    #         return None
    elif task_type == "递送":  # 物品，对象
        try:
            verb_index = words.index(selected_verb)
            children = [ii for ii in range(len(words)) if head[ii] == (verb_index + 1)]
            plc1 = [ii for ii in children if dep_rel[ii] == "VOB"]
            plc2 = [ii for ii in children if dep_rel[ii] == "DOB"]

            if plc1 and plc2:
                print('Strange pattern without VOB and DOB for 讲解' + str(words))
                return None
            elif plc1 and not plc2:
                children = [ii for ii in range(len(words)) if head[ii] == (plc1[0] + 1)]
                quantity = [ii for ii in children if dep_rel[ii] == "ATT"]
                if quantity:
                    elements[ELE_CONTENT] = "destination=" + words[quantity[0]] + words[plc1[0]]
                else:
                    elements[ELE_CONTENT] = "destination=" + words[plc1[0]]

                children = [ii for ii in range(len(words)) if head[ii] == (verb_index + 1)]
                cmp = [ii for ii in children if dep_rel[ii] == "CMP"]
                adv = [ii for ii in children if dep_rel[ii] == "ADV"]
                if cmp and not adv:
                    children = [ii for ii in range(len(words)) if head[ii] == (cmp[0] + 1)]
                    ppl = [ii for ii in children if dep_rel[ii] == "VOB"]
                    if ppl:
                        elements[ELE_OBJ] = words[ppl[0]]
                elif cmp and adv:
                    print('unknown pattern')
                    return None
                elif not cmp and adv:
                    children = [ii for ii in range(len(words)) if head[ii] == (adv[0] + 1)]
                    ppl = [ii for ii in children if dep_rel[ii] == "POB"]
                    if ppl:
                        elements[ELE_OBJ] = words[ppl[0]]
                else:
                    pass
            elif not plc1 and plc2:
                ppl = [ii for ii in children if pos_tag[ii] == "r" or pos_tag[ii] == "PER"]
                if ppl:
                    elements[ELE_OBJ] = words[ppl[0]]
                obj = [ii for ii in children if pos_tag[ii] == "n"]
                if obj:
                    children = [ii for ii in range(len(words)) if head[ii] == (obj[0] + 1)]
                    quantity = [ii for ii in children if dep_rel[ii] == "ATT"]
                    if quantity:
                        elements[ELE_CONTENT] = "destination=" + words[quantity[0]] + words[obj[0]]
                    else:
                        elements[ELE_CONTENT] = "destination=" + words[obj[0]]
            else:
                pass

            elements[ELE_SUB] = "导览机器人"
            elements[ELE_PLACE] = "展厅"
        except ValueError:
            print("error")
            return None
    elif task_type == "送别":  # 对象，目的地
        try:
            verb_index = words.index(selected_verb)
            children = [ii for ii in range(len(words)) if head[ii] == (verb_index + 1)]
            pattern1 = [ii for ii in children if dep_rel[ii] == "DBL"]
            pattern2 = [ii for ii in children if dep_rel[ii] == "VOB"]
            if pattern1 and pattern2:
                print('Strange pattern without VOB and DOB for 讲解' + str(words))
                return None
            elif pattern1 and not pattern2:

                ppl = [ii for ii in children if pos_tag[ii] == "r" or pos_tag[ii] == "PER"]
                if ppl:
                    elements[ELE_OBJ] = words[ppl[0]]

                des_v = [ii for ii in children if pos_tag[ii] == "v"]
                if des_v:
                    children = [ii for ii in range(len(words)) if head[ii] == (des_v[0] + 1)]
                    des = [ii for ii in children if dep_rel[ii] == "VOB"]
                    if des:

                        start = des[0]
                        content = ""
                        while True:
                            children = [ii for ii in range(len(words)) if head[ii] == (start + 1)]
                            att = [ii for ii in children if dep_rel[ii] == "ATT"]
                            if att:
                                content = words[att[0]] + content
                                start = att[0]
                            else:
                                break
                        elements[ELE_CONTENT] = "destination=" + content + words[des[0]]

            elif not pattern1 and pattern2:

                ppl_v = [ii for ii in children if dep_rel[ii] == "POB"]
                ppl_c = [ii for ii in children if dep_rel[ii] == "CMP"]
                if ppl_v and not ppl_c:
                    children = [ii for ii in range(len(words)) if head[ii] == (ppl_v[0] + 1)]
                    ppl = [ii for ii in children if dep_rel[ii] == "POB"]
                    if ppl:
                        elements[ELE_OBJ] = words[ppl[0]]

                    start = pattern2[0]
                    content = ""
                    while True:
                        children = [ii for ii in range(len(words)) if head[ii] == (start + 1)]
                        att = [ii for ii in children if dep_rel[ii] == "ATT"]
                        if att:
                            content = words[att[0]] + content
                            start = att[0]
                        else:
                            break
                    elements[ELE_CONTENT] = "destination=" + content + words[pattern2[0]]
                elif ppl_v and ppl_c:
                    print('unknown pattern' + str(words))
                    return None
                elif not ppl_v and ppl_c:
                    elements[ELE_OBJ] = words[pattern2[0]]

                    children = [ii for ii in range(len(words)) if head[ii] == (ppl_c[0] + 1)]

                    des = [ii for ii in children if dep_rel[ii] == "VOB"]
                    if des:
                        start = des[0]
                        content = ""
                        while True:
                            children = [ii for ii in range(len(words)) if head[ii] == (start + 1)]
                            att = [ii for ii in children if dep_rel[ii] == "ATT"]
                            if att:
                                content = words[att[0]] + content
                                start = att[0]
                            else:
                                break
                        elements[ELE_CONTENT] = "destination=" + content + words[des[0]]
                else:
                    pass

            else:

                pass

            elements[ELE_SUB] = "导览机器人"
            elements[ELE_PLACE] = "展厅"
        except ValueError:
            print("error")
            return None
    elif task_type == "停止":
        pass
    if elements == {}:
        elements = None
    return elements


def ground(task):
    """
    对task中的指令进行grounding，理解其在机器人认知中的含义
    :param task:
    :return:
    """
    result = {RESULT_CODE: 0, RESULT_MSG: None, RESULT_DATA: None}
    if not task:
        result[RESULT_MSG] = "Invalid argument: TASK"
        result[RESULT_CODE] = 304
        return result
    task_type = task.get(ELE_TASK, None)
    if not task_type:
        result[RESULT_MSG] = "during grounding, the task type was not recognized beforehand"
        result[RESULT_CODE] = 305
        return task

    if task_type == "导览":
        content = task.get(ELE_CONTENT, None)
        if content:
            pairs = content.split(PARAMETER_DELIMITER)
            pairs = resolve_parameters(pairs)
            place = pairs.get(CONTENT_PLACE, None)
            if place:
                query_cmd = {ARGUMENT_EXHIBITION_NAME: place}
                query_result = requests.post(QUERY_URL + QUERY_EXHIBITION_BY_NAME, json=query_cmd)
                try:
                    query_result = json.loads(query_result.text)

                    state = query_result.get("state", -1)
                    if state == 1:  # 查询成功
                        data = query_result.get(DATA_FIELD_IN_RESPONSE_EXHIBITION_NAME)
                        if len(data) == 0:  # todo 无记录
                            result[RESULT_MSG] = "during grounding, no record of exhibition in DB"
                            result[RESULT_CODE] = 307
                            pairs.pop(CONTENT_PLACE)
                            print("未找到匹配展点，已删除数据")
                        elif len(data) == 1:
                            pairs[CONTENT_PLACE] = data[0][EXHIBITION_NAME_IN_DB]
                        else:  # todo: 多种可能时消歧，没有匹配时的消歧
                            result[RESULT_MSG] = "during grounding, multiple records of exhibition in DB"
                            result[RESULT_CODE] = 308
                            pairs[CONTENT_PLACE] = data[0][EXHIBITION_NAME_IN_DB]
                    else:
                        pairs.pop(CONTENT_PLACE)
                        result[RESULT_MSG] = "during grounding, failed to query exhibition info from  in DB"
                        result[RESULT_CODE] = 309
                except JSONDecodeError or TypeError:
                    result[RESULT_MSG] = "during grounding, failed to connect exhibition server by name"
                    result[RESULT_CODE] = 306
                    pairs.pop(CONTENT_PLACE)

                parameters = generate_parameters(pairs)
                if len(parameters) > 0:
                    task[ELE_CONTENT] = parameters
                else:
                    task[ELE_CONTENT] = None
    return task


def resolve_parameters(lists):
    """

    :param lists: list of parameters in the form of ["des=a", "num=2]
    :return: dict with keys (des, num) and values (a, 2)
    """
    if not lists:
        return None
    result = {}
    for item in lists:
        items = item.split(PARAMETER_KEY_VALUE_DELIMITER)
        result[str.strip(items[0])] = str.strip(items[1])
    return result


def generate_parameters(parameters):
    """
    生成字符串
    :param parameters: dict with keys (des, num) and values (a, 2)
    :return: str like "des=a;num=2"
    """
    result = ""
    if not parameters:
        return result
    for key, value in parameters.items():
        result = result + str(key) + PARAMETER_KEY_VALUE_DELIMITER + str(value) + PARAMETER_DELIMITER
    if len(result) > 1:
        result = result[:-1]
    return result
