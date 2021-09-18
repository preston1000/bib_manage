
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

from utils.nlp.utils import dd_parser_caller, get_modifier_as_children_att
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
            plc = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "VOB" and pos_tag[ii] in ['n', 'LOC', 's']]  # find index of destination(children of verb which satisfy given condition)
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
        except ValueError or IndexError:
            print("failed to resolve task element for task '导览'")
            return None
    elif task_type == '欢迎':  # todo revise
        try:
            # find index of destination(children of verb which satisfy given condition)
            ppl = [ii for ii, tmp_head in enumerate(head) if
                   tmp_head == selected_verb and dep_rel[ii] == "VOB" and pos_tag[ii] in ['n', 'PER']]
            if ppl:
                elements[ELE_OBJ] = words[ppl[0]]

        except ValueError:
            return None
    elif task_type == "讲解":  # 内容，听众
        try:

            # find index of destination(children of verb which satisfy given condition)
            plc = [ii for ii, tmp_head in enumerate(head) if
                   tmp_head == selected_verb and dep_rel[ii] == "VOB" and pos_tag[ii] in ['n', 'LOC', 's']]
            if plc:
                elements[ELE_CONTENT] = "destination=" + words[plc[0]]

            # find index of adverbs (children of verb which satisfy given condition)
            adv = [ii for ii, tmp_head in enumerate(head) if
                   tmp_head == selected_verb and dep_rel[ii] == "ADV"]

            if adv:
                # find index of person (children of verb which satisfy given condition)
                ppl = [ii for ii, tmp_head in enumerate(head) if
                       tmp_head == words[adv[0]] and dep_rel[ii] == "POB" and pos_tag[ii] in ['n', 'PER', 'r']]

                if ppl:
                    elements[ELE_OBJ] = words[ppl[0]]
                # else: todo 这是什么情况来着
                #     cmp = [ii for ii in children if dep_rel[ii] == "CMP"]
                #     if cmp:
                #         children = [ii for ii in range(len(words)) if head[ii] == (cmp[0] + 1)]
                #         ppl = [ii for ii in children if dep_rel[ii] == "VOB"]
                #         if ppl:
                #             elements[ELE_OBJ] = words[ppl[0]]

        except ValueError:
            print("error")
            return None
    elif task_type == "递送":  # 物品，对象
        try:
            # find index of candidate objects (children of verb which satisfy given condition)
            objects_vob = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "VOB" and pos_tag[ii] in ['n']]

            # find index of candidate objects (children of verb which satisfy given condition)
            objects_dob = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "DOB" and pos_tag[ii] in ['n']]

            # find index of candidate objects (children of verb which satisfy given condition)
            who_cmp = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "CMP"]

            # find index of candidate objects (children of verb which satisfy given condition)
            who_adv = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "ADV"]

            # find index of candidate person (children of verb which satisfy given condition)
            person_dob = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "DOB" and pos_tag[ii] in ['PER', 'r']]

            # resolve objects
            if objects_vob and objects_dob:
                print('Strange pattern with both VOB and DOB for 讲解' + str(words))
                return None
            elif objects_vob and not objects_dob:  # with VOB, 给张春华拿一杯水
                objects = objects_vob[0]  # todo multiple matching
            elif not objects_vob and objects_dob:  # with DOB, 给我一瓶水
                objects = objects_dob[0]  # todo multiple matching
            else:
                print('Strange pattern without VOB and DOB for 讲解' + str(words))
                return None

            quantity = get_modifier_as_children_att(words[objects], words, head, dep_rel)  # resolve quantity of objects
            if quantity:
                elements[ELE_CONTENT] = "destination=" + quantity + words[objects]
            else:
                elements[ELE_CONTENT] = "destination=" + words[objects]

            # resolve who to give the objects
            if person_dob:  # 给我一杯水
                ppl = person_dob
            else:
                if who_cmp and who_adv:
                    print('Strange pattern with both CMP and ADV for 讲解' + str(words))
                    return None
                elif who_cmp and not who_adv:  # 拿给我一瓶水
                    ppl = [ii for ii, tmp_head in enumerate(head) if tmp_head == words[who_cmp[0]] and dep_rel[ii] == "VOB" and pos_tag[ii] in ['n', 'PER', 'r']]
                elif not who_cmp and who_adv:  # 给张春华那一瓶水
                    ppl = [ii for ii, tmp_head in enumerate(head) if tmp_head == words[who_adv[0]] and dep_rel[ii] == "POB" and pos_tag[ii] in ['n', 'PER', 'r']]
                else:
                    print('Strange pattern without CMP and ADV for 讲解' + str(words))
                    return None
            if ppl:
                elements[ELE_OBJ] = words[ppl[0]]

        except ValueError:
            print("error")
            return None
    elif task_type == "送别":  # 对象，目的地
        try:
            destination_dbl = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "DBL" and pos_tag[ii] in ["v"]]
            destination_vob = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "VOB" and pos_tag[ii] in ['n', 's', 'LOC']]
            destination_cmp = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "CMP" and pos_tag[ii] in ['v']]

            person_dbl = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "DBL" and pos_tag[ii] in ["PER", "r"]]
            person_vob = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "VOB" and pos_tag[ii] in ["PER", "r"]]
            person_pob = [ii for ii, tmp_head in enumerate(head) if tmp_head == selected_verb and dep_rel[ii] == "POB" and pos_tag[ii] in ['p']]

            # 解析目的地
            destination = None
            if destination_cmp:  # 送张春华到这个展厅门口
                destination = [ii for ii, tmp_head in enumerate(head) if
                               tmp_head == words[destination_cmp[0]] and dep_rel[ii] == "VOB"]
            else:
                if destination_dbl and destination_vob:
                    print('Strange pattern without VOB and DBL for 送别' + str(words))
                elif destination_dbl and not destination_vob:  # 送张春华到一号展厅门口
                    destination = [ii for ii, tmp_head in enumerate(head) if tmp_head == words[destination_dbl[0]] and dep_rel[ii] == "VOB"]
                elif not destination_dbl and destination_vob:  # 把张春华送到展厅门口
                    destination = destination_vob
                else:
                    pass
            if destination:
                content = get_modifier_as_children_att(words[destination[0]], words, head, dep_rel)
                elements[ELE_CONTENT] = "destination=" + content + words[destination[0]]

            # 解析送别人
            ppl = None
            if person_pob and person_vob and person_dbl:
                print('Strange pattern with all VOB and DBL POB for person in 送别' + str(words))
            elif person_pob and not person_vob and not person_dbl:  # 把张春华送到展厅门口
                ppl = [ii for ii, tmp_head in enumerate(head) if tmp_head == words[person_pob[0]] and dep_rel[ii] == "POB" and pos_tag[ii] in ["PER", 'r']]
            elif not person_pob and not person_vob and person_dbl:  # 送张春华到一号展厅门口
                ppl = person_dbl
            elif not person_pob and person_vob and not person_dbl:  # 送张春华到这个展厅门口
                ppl = person_vob
            else:
                print('Strange pattern with any two of VOB and DBL POB for person in 送别' + str(words))
            if ppl:
                elements[ELE_OBJ] = words[ppl[0]]

        except ValueError:
            print("error")
            return None
    elif task_type == "停止":
        pass

    elements[ELE_SUB] = "导览机器人"
    elements[ELE_PLACE] = "展厅"

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
