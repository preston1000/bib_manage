import json
import os
import neo4j
import socket
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

"""
neo4j
"""
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

"""
nlp tool
"""
lac_file = cf.get('nlp', "lacFile")
ddp_file = cf.get('nlp', "ddpFile")

lac_file = os.path.join(basedir, lac_file)
ddp_file = os.path.join(basedir, ddp_file)

"""
dep rel
"""

PARAMETER_DELIMITER = cf.get("deprel", "delimiter")
PLANNING_URL = cf.get("deprel", "reasoning")
QUERY_URL = cf.get("deprel", "queryURL")
QUERY_EXHIBITION_BY_NAME = cf.get("deprel", "queryExhibitionByName")

hostname = socket.gethostname()
INTENTION_URL = socket.gethostbyname(hostname)  # 当前主机地址
# INTENTION_URL = "10.11.80.108"

"""
bibtex config
"""
PUBLICATION_TYPES = cf.get("bib", "publicationType").split(",")
EDGE_TYPES = cf.get("bib", "edgeType").split(",")
NODE_TYPES = cf.get("bib", "nodeType").split(",")
FIELD_NAMES_PUB = cf.get("bib", "fields").split(",")
FIELD_NAMES_VENUE = cf.get("bib", "fieldsVenue").split(",")
FIELD_NAMES_PERSON = cf.get("bib", "fieldPerson").split(",")
PUB_KEY_FIELD = cf.get("bib", "pubKeyField").split(",")

ARTICLE = "ARTICLE"
BOOK = "BOOK"
BOOKLET = "BOOKLET"
INPROCEEDINGS = "INPROCEEDINGS"
CONFERENCE = "CONFERENCE"
INCOLLECTION = "INCOLLECTION"
INBOOK = "INBOOK"
MISC = "MISC"
MANUAL = "MANUAL"
PHDTHESIS = "PHDTHESIS"
MASTERSTHESIS = "MASTERSTHESIS"
PROCEEDINGS = "PROCEEDINGS"
TECHREPORT = "TECHREPORT"
UNPUBLISHED = "unpublished"


MANDATORY_FIELDS = {ARTICLE: ["TITLE", 'JOURNAL', "YEAR", "AUTHOR"],
                    BOOK: ["TITLE", "PUBLISHER", "YEAR", ["AUTHOR", "EDITOR"]],
                    BOOKLET: ["TITLE"],
                    INPROCEEDINGS: ["AUTHOR", "TITLE", "BOOKTITLE", "YEAR"],
                    CONFERENCE: ["AUTHOR", "TITLE", "BOOKTITLE", "YEAR"],
                    INBOOK: [["AUTHOR", "EDITOR"], "TITLE", "YEAR", ["CHAPTER", "PAGES"]],
                    INCOLLECTION: ["AUTHOR", "TITLE", "BOOKTITLE", "YEAR", "PUBLISHER"],
                    MISC: [],
                    MANUAL: ["TITLE"],
                    PHDTHESIS: ["AUTHOR", "TITLE", "SCHOOL", "YEAR"],
                    MASTERSTHESIS: ["AUTHOR", "TITLE", "SCHOOL", "YEAR"],
                    PROCEEDINGS: ["TITLE", "YEAR"],
                    TECHREPORT: ["AUTHOR", "TITLE", "INSTITUTION", "YEAR"],
                    UNPUBLISHED: ["AUTHOR", "TITLE", "NOTE"]}

FIELD_OF_PUBLICATION_FOR_VENUE = cf.get("bib", "pubFieldValue")
FIELD_OF_PUBLICATION_FOR_VENUE = json.loads(FIELD_OF_PUBLICATION_FOR_VENUE)

VENUE_TYPE_FOR_NODE_TYPE = cf.get("bib", "venueType")
VENUE_TYPE_FOR_NODE_TYPE = json.loads(VENUE_TYPE_FOR_NODE_TYPE)