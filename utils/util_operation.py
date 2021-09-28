from configparser import ConfigParser
from utils.models import Venue, Person, Publication
from utils.constants import GlobalVariables


def get_value_by_key(entry, key):
    value = entry.get(key)
    if value is None:
        return None
    else:
        return value


def judge_type(data):
    if isinstance(data, Publication):
        tt = 1
    elif isinstance(data, Venue):
        tt = 2
    elif isinstance(data, Person):
        tt = 3
    else:
        tt = -1
    return tt


def reverse_map_key_value(data):
    """
    将data中的key和value互换位置，可能重复，用list表示
    :param data:
    :return:
    """
    tmp = {}
    for (key, value) in data.items():
        tt = tmp.get(value, [])
        tt.append(key)
        tmp[value] = tt
    return tmp


def merge_person():
    """
    todo 这个是合并网络中的人节点（有可能出现多个节点表示一个人）
    :return:
    """
    return


def ini_neo4j(config_path="/Volumes/Transcend/web/web_pages/webs/neo4j.conf"):
    """
    这里是读取neo4j的配置
    :param config_path:
    :return:
    """
    cf = ConfigParser()
    cf.read(config_path, encoding="utf-8")
    # todo: 判断读取失败时应该怎么写日志及返回值
    uri = cf.get("neo4j", "uri")
    username = cf.get("neo4j", "username")
    pwd = cf.get("neo4j", "pwd")
    database_info = {"uri": uri, "username": username, "pwd": pwd}
    return database_info


def wrap_info_to_model(info, parameters=None):
    """
    将只有名称信息的数据封装成models.py中类
    :param info: dict,field包括type：节点类型，name：节点字段
    :param parameters:
    :return:
    """
    if not isinstance(info, dict):
        return None
    new_type = info.get("type", None)
    if new_type is None:
        return None
    names = info.get("name", None)
    if names is None:
        return None
    if new_type == "VENUE":
        nodes = []
        if parameters is not None:
            try:
                venue_type = parameters.get("node_type", "")
            except TypeError:
                venue_type = ""
        else:
            venue_type = ""
        for name in names:
            venue = Venue(uuid="", venue_type=venue_type, venue_name=name)
            nodes.append(venue)
    elif new_type == "PERSON":
        nodes = []
        for name in names:
            person = Person(uuid="", full_name=name)  # TODO 人名的解析
            nodes.append(person)
    else:
        return None
    return nodes


def check_uniqueness_pubs(data):
    """
    检查Publication数据中的唯一标识是否重复
    :param data: list of publication
    :return: 检查后结果
    """
    result = {"data": "", "msg": "", "code": 0, "repeat_data": ""}
    if data is None or not isinstance(data, list):
        result["code"] = -300
        result["msg"] = "输入数据错误"
        return result
    msg = ""
    found_fields = {}  # list of list，第i项为第i个unique tag的list
    unique_data = []
    repeat_data = []
    for item in data:
        if not isinstance(item, Publication):
            msg += "\n 数据【" + str(item) + "】格式错误，非Publication类"
            continue
        flag = True
        for field in GlobalVariables.pub_unique_fields:  # todo 后面还要在数据库中查询相应信息是否重复
            value = item[field]
            current_list = found_fields[field]
            try:
                index = current_list.index(value)
            except:
                flag = False
                break
        if not flag:
            repeat_data.append(item)
        else:
            unique_data.append(item)
            current_list.append(value)
            found_fields[field] = current_list
    if len(repeat_data) == 0:
        result["code"] = 300
        result["msg"] = "全部唯一"
        result["data"] = data
        return result
    else:
        result["code"] = 301
        result["msg"] = "部分唯一"
        result["data"] = unique_data
        result["repeat_data"] = repeat_data
        return result

