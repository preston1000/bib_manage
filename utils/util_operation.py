from configparser import ConfigParser
from utils.models import Venue, Person

def get_value_by_key(entry, key):
    value = entry.get(key)
    if value is None:
        return None
    else:
        return value


def upperize_dict_keys(entry):
    """
    将每个文献中的字段名称转成大写，并对应其在entry中的key
    :param entry:
    :return:
    """
    mapping = {}
    for (key, value) in entry.items():
        mapping[key.upper()] = value
    return mapping


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
    database_info = {"uri":uri, "username":username, "pwd":pwd}
    return database_info


def wrap_info_to_model(info, parameters=None):
    if not isinstance(info, dict):
        return None
    new_type = info.get("type", None)
    if new_type is None:
        return None
    names = info.get("name", None)
    if names is None:
        return None
    if new_type == "Venue":
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
    elif new_type == "Person":
        nodes = []
        for name in names:
            person = Person(uuid="", full_name=name)  # TODO 人名的解析
            nodes.append(person)
    else:
        return None
    return nodes
