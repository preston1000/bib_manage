import json
import os
import neo4j
from pathlib import Path
from django.http import HttpResponse
from neo4j import GraphDatabase
from configparser import ConfigParser

from utils.mqtt_util import MqttUtil


def wrap_result(result, ensure_ascii=False, content_type='application/json', charset='utf-8'):
    return HttpResponse(json.dumps(result, ensure_ascii=ensure_ascii), content_type=content_type, charset=charset)


def ini_result():
    result = {RESULT_DATA: None, RESULT_MSG: "", RESULT_CODE: -1}
    return result


def initialize_neo4j_driver():
    # 初始化Neo4j数据库连接,及查询结果
    driver = GraphDatabase.driver(uri, auth=neo4j.basic_auth(neo4j_username, neo4j_pwd))
    return driver


basedir = Path(__file__).parent.parent  # 项目根目录


cf = ConfigParser()
config_file_neo4j = os.path.join(basedir, "neo4j.conf")

try:
    cf.read(config_file_neo4j, encoding="utf-8")
except:
    print("failed to read from configuration file")
    exit()


uri = cf.get("neo4j", "uri")
neo4j_username = cf.get("neo4j", "username")
neo4j_pwd = cf.get("neo4j", "pwd")

RESULT_DATA = cf.get("resultField", "data")
RESULT_MSG = cf.get("resultField", "message")
RESULT_CODE = cf.get("resultField", "code")
RESULT_COUNT = cf.get("resultField", "count")


"""
MQTT service
"""


broker = cf.get("mqtt", "broker")  # 连接地址
port = int(cf.get("mqtt", "port"))  # 端口地址
topic = cf.get("mqtt", "topic")  # 主题topic
client_id = cf.get("mqtt", "clientPublish")
mqtt_client = MqttUtil(broker, port, client_id)

"""
graphviz
"""
graphviz_dir = cf.get("graphviz", "binFolder")
os.environ["PATH"] += os.pathsep + graphviz_dir


SHEET_NAME = cf.get("stationFileFormat", "sheetname")
SHEET_TITLE = cf.get("stationFileFormat", "title").split(",")

lac_file = cf.get('nlp', "lacFile")
ddp_file = cf.get('nlp', "ddpFile")

lac_file = os.path.join(basedir, lac_file)
ddp_file = os.path.join(basedir, ddp_file)