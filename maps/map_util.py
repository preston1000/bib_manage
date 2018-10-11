#coding:utf-8
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from matplotlib.patches import Polygon
from matplotlib.colors import rgb2hex
import xlrd
import re
from adjustText import adjust_text
import numpy as np
from scipy import interpolate
from neo4j.v1 import GraphDatabase
import neo4j.v1
import uuid
from datetime import date

# 解决图像显示中文乱码的问题
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 数据库neo4j配置--和
uri = "bolt://localhost:7687"
username = 'neo4j'
pwd = '123456'

RAIL_LINES = 'rail_lines'
BELONGING_BUREAU = 'belonging_bureau'
NAME_EN = 'name_en'
NAME_CN = 'name_cn'
USED_NAMES = 'used_names'
POSITION = 'position'
PRE_STATION = 'pre_station'
SUC_STATION = 'suc_station'
USE_CARD = 'use_card'
FACE_RECOGNITION = 'face_recognition'
PLATFORM_NUM = 'platform_num'
RAIL_NUM = 'rail_num'
ADDRESS = 'address'
LEVEL = 'level'
BIRTHDAY = 'birthday'
FOR_PASSENGER = 'for_passenger'
FOR_LOADS = 'for_loads'
ABANDONED = 'abandoned'
READY = 'ready'
STATION_NUM = 'station_num'
STATION_START = 'station_start'
STATION_END = 'station_end'
LINES = 'lines'  # 线路总数
LENGTH = 'length'  # 线路长度
BALLASTED = 'ballasted'  # 是否有砟
TRACK_WIDTH = 'track_width'  # 轨距
BUILD_TIME_START = 'build_time_start'  # 开工时间
WORKING_TIME_START = 'working_time_start'  # 启用时间
WHOLE_LINE = 'whole_line'
SUB_LINE = 'sub_line'
REMARK = 'remark'
UUID = "uuid"


field_titles = [RAIL_LINES,	BELONGING_BUREAU,	NAME_EN,	NAME_CN,	USED_NAMES,
                POSITION,	PRE_STATION,	SUC_STATION,	USE_CARD,	FACE_RECOGNITION,
                PLATFORM_NUM,	RAIL_NUM,	ADDRESS,	LEVEL,	BIRTHDAY,	FOR_PASSENGER,
                FOR_LOADS,	ABANDONED,	READY, REMARK]
field_titles_rail_line = [NAME_CN, NAME_EN, USED_NAMES, STATION_START, STATION_END, STATION_NUM, READY,
                          LINES, LEVEL, LENGTH, BALLASTED, TRACK_WIDTH, BUILD_TIME_START, WORKING_TIME_START]
field_titles_rail_line_relation = [WHOLE_LINE, SUB_LINE]


SHEET_BUREAU = '铁路局'
SHEET_LINE_RELATION = '铁路线关系'
SHEET_LINE = '铁路线'
SHEET_STATION = '火车站1'
FIELD_NUM = 20
FIELD_NUM_LINE_RELATION = 2
FIELD_NUM_LINE = 14


def get_data(data_file='/Users/xixiangming/Library/Mobile Documents/com~apple~CloudDocs/铁路.xlsx', sheet_name=None):
    """
    从Excel中获取数据，包括了处理数据的过程
    :param data_file:
    :param sheet_name:
    :return: stations: dict, whose key is the station name, and value is dict{field: value}
             line_relations: list of tuple, which is (start_line, end_line)，父->子
    """
    workbook = xlrd.open_workbook(data_file, formatting_info=False)  # 原样读取数据
    if workbook is None:
        print("找不到火车站数据文件")
        return -1
    if sheet_name is None:
        print("请指定sheet name")
        return -2
    table = workbook.sheet_by_name(sheet_name)
    if table is None:
        print("错误！数据文件中没有sheet名为：" + sheet_name)
        return -1
    # 提取火车站信息
    if sheet_name == SHEET_STATION:
        nrows = table.nrows
        ncols = table.ncols
        if nrows < 2:
            print("数据表中没有火车站信息")
            return -1
        print("共有" + str(nrows) + "," + str(ncols-1) + "个火车站信息")
        # 第一行是标题
        titles = table.row_values(0)
        if titles is None or len(titles) < FIELD_NUM:
            print("title：火车站属性不足，错误")
            return -1
        stations = {}  # 处理后的数据信息,key:火车站名，value：火车站信息
        name_index = titles.index(NAME_CN)
        if name_index < 0:
            print("标题中没有中文名")
            return -1

        for index_r in range(1, nrows):
            row_info = table.row_values(index_r)
            if row_info is None or len(row_info) < FIELD_NUM:
                print("第" + str(index_r + 1) + "行数据有问题: " + str(row_info))
                continue
            if row_info[name_index] in stations.keys():
                print("有重复车站：" + row_info[name_index] + "，忽略第" + str(index_r + 1) + "行数据 ")
                continue
            info = {}
            if row_info[name_index] == '华安':
                print("stop")
            for j in range(0, ncols):
                processed_data = cell_process_station(row_info[j], titles[j], workbook.datemode)
                if processed_data is None:
                    processed_data = ""
                info[titles[j].lower()] = processed_data
            stations[info[NAME_CN]] = info
        return stations
    # 提取火车线路信息
    if sheet_name == SHEET_LINE:
        nrows = table.nrows
        ncols = table.ncols
        if nrows < 2:
            print("数据表中没有火车线信息")
            return -1
        print("共有" + str(nrows) + "," + str(ncols - 1) + "个火车线信息")
        # 第一行是标题
        titles = table.row_values(0)
        if titles is None or len(titles) < FIELD_NUM_LINE:
            print("title：火车线属性不足，错误")
            return -1
        lines = {}  # 处理后的数据信息,key:火车站名，value：火车站信息
        name_index = titles.index(NAME_CN)
        if name_index < 0:
            print("标题中没有中文名")
            return -1
        for index_r in range(1, nrows):
            row_info = table.row_values(index_r)
            if row_info is None or len(row_info) < FIELD_NUM_LINE:
                print("第" + str(index_r + 1) + "行数据有问题: " + str(row_info))
                continue
            if row_info[name_index] in lines.keys():
                print("有重复线路：" + row_info[name_index] + "，忽略第" + str(index_r + 1) + "行数据 ")
                continue
            info = {}
            for j in range(0, ncols):
                processed_data = cell_process_line(row_info[j], titles[j], workbook.datemode)
                if processed_data is None or isinstance(processed_data, int) and processed_data < 0:
                    processed_data = ""
                info[titles[j].lower()] = processed_data
            lines[info[NAME_CN]] = info
        return lines
    # 提取铁路局信息
    if sheet_name == SHEET_BUREAU:
        print("未实现提取铁路局信息")
        return -1
    # 提火车线关系
    if sheet_name == SHEET_LINE_RELATION:
        nrows = table.nrows
        ncols = table.ncols
        if nrows < 2:
            print("数据表中没有火车线关系信息")
            return -1
        print("共有" + str(nrows) + "," + str(ncols - 1) + "个火车线关系信息")
        # 第一行是标题
        titles = table.row_values(0)
        if titles is None or len(titles) != FIELD_NUM_LINE_RELATION:
            print("title：只需要两列数据，错误")
            return -1
        parent_index = titles.index(WHOLE_LINE)
        child_index = titles.index(SUB_LINE)
        if parent_index < 0 or child_index < 0:
            print("铁路线关系表，列名称不正确，应为：" + WHOLE_LINE + "、" + SUB_LINE)
            return -1
        # 查找合并的单元格
        colspan = {}  # 用于保存计算出的合并的单元格，key=(7, 4)合并单元格坐标，value=(7, 2)合并单元格首格坐标
        # table.merged_cells是一个元组的集合，每个元组由4个数字构成(7，8，2，5)
        # 四个数字依次代表：行，合并的范围(不包含)，列，合并的范围(不包含)，类似range()，从0开始计算
        # (7，8，2，5)的意思是第7行的2,3,4列进行了合并
        if table.merged_cells:
            for item in table.merged_cells:
                for row in range(item[0], item[1]):  # 通过循环进行组合，从而得出所有的合并单元格的坐标
                    for col in range(item[2], item[3]):
                        if (row, col) != (item[0], item[2]):  # 合并单元格的首格是有值的，所以在这里进行了去重
                            colspan.update({(row, col): (item[0], item[2])})

        info = []  # 处理后的数据信息,list of tuple, which is (start_line, end_line)，父->子
        for index_r in range(1, nrows):
            row_info = table.row_values(index_r)
            if row_info is None or len(row_info) < FIELD_NUM_LINE_RELATION:
                print("第" + str(index_r + 1) + "行数据有问题: " + str(row_info))
                continue
            if colspan.get((index_r, parent_index)):
                start_station = table.cell_value(*colspan.get((index_r, parent_index)))
            else:
                start_station = table.cell_value(index_r, parent_index)
            end_station = table.cell_value(index_r, child_index)
            info.append((start_station, end_station))
        return info


def cell_process_line(lines, field, date_mode):
    """
    处理火车线的字段属性，-----暂时只实现了处理中文名称
    :param lines:
    :param field:
    :param date_mode:
    :return:
    """
    if lines is None and field is None:
        return 0
    if (lines is None or lines == "") and field is not None:
        return None
    if lines is not None and field is None:
        return lines
    if field not in field_titles:
        print(field + "是无效字段")
        return -1
    field = field.lower()
    if field == NAME_CN:
        try:
            lines = lines.strip()
            return lines
        except:
            return -2
    else:
        return -1


def cell_process_station(data, field, date_mode):
    """
    处理Excel表格中数据，data是cell内容，field是字段名
    :param data:
    :param field:
    :param date_mode:
    :return: 处理后的数据
    """
    if data is None and field is None:
        return 0
    if (data is None or data == "") and field is not None:
        return None
    if data is not None and field is None:
        return data
    if field not in field_titles:
        print(field + "是无效字段")
        return -1
    if field.lower() == RAIL_LINES:
        lines = re.split("\n+|、+", data)  # 切分多个线路
        if isinstance(lines, str):
            lines = [lines]
        lines = [line.strip() for line in lines]
        return lines
    elif field.lower() == BELONGING_BUREAU or field.lower() == USED_NAMES or \
            field.lower() == USE_CARD or field.lower() == FACE_RECOGNITION or field.lower() == ADDRESS or \
            field.lower() == LEVEL or field.lower() == READY or field.lower() == REMARK or \
            field.lower() == FOR_LOADS or field.lower() == FOR_PASSENGER or field.lower() == ABANDONED:
        print("所属铁路局、英文名、曾用名、中铁银通卡、人脸识别、地址、等级、备注、在用、货运、客运、废弃未处理：" + str(data))
        return data
    elif field.lower() == NAME_EN:
        data = data.replace("'", '\\\'')
        return data
    elif field.lower() == BIRTHDAY:
        try:
            date_value = xlrd.xldate_as_tuple(data, date_mode)
            date_tmp = date(*date_value[:3]).strftime('%Y年%m月%d日')
            return date_tmp
        except:
            return data
        # if not isinstance(date, float):
        #     return data
        # else:
        #     date_value = xlrd.xldate_as_tuple(data, datemode)
        #     date_tmp = date(*date_value[:3]).strftime('%Y年%m月%d日')
        #     return date_tmp
    elif field.lower() == NAME_CN:
        if re.match("[\u4e00-\u9fa5]+站$", data):
            print("[" + data + "]已包含'站'字")
        else:
            data = data + "站"
        return data
    elif field.lower() == POSITION:
        coordinates = data.split(",")
        if not isinstance(coordinates, list):
            print("[" + data + "]不是合理坐标值！")
            return None
        try:
            coordinates = [float(coordinate) for coordinate in coordinates]
        except ValueError:
            print("[" + data + "]不是合理坐标值！")
            return None
        return coordinates
    elif field.lower() == PRE_STATION or field.lower() == SUC_STATION:
        stations = data.split("、")
        if isinstance(stations, str):
            stations = [stations]
        tmp = []
        for item in stations:
            if not re.match("[\u4e00-\u9fa5]+站$", item):
                tmp.append(item + "站")
            else:
                tmp.append(item)
        return tmp
    elif field.lower() == PLATFORM_NUM or field.lower() == RAIL_NUM:
        try:
            tmp = int(data)
        except ValueError:
            print(field + "值格式不正确：" + data)
            return data
        return tmp
    else:
        print("未识别的自段：" + field)
        return -1


def draw_figure(data=None):

    plt.figure(figsize=(16,8))
    m = Basemap(  # 其中西经和南纬坐标是负值，北纬和东经坐标是正值。
        llcrnrlon=77,  # 左下角的纬度
        llcrnrlat=14,  # 左下角的经度
        urcrnrlon=140,  # 右上角的纬度
        urcrnrlat=51,  # 右上角的经度
        projection='lcc',  # 投影方式
        lat_1=33,
        lat_2=45,
        lon_0=100,
        resolution="l"  # clhf分别为粗糙、低、高、完整
    )
    m.drawcountries(linewidth=1.5)  # 画出国家，并使用线宽为 1.5 的线条生成分界线。
    m.drawcoastlines()  # 画出海岸线？

    # 文件号越大，地图越精细
    # for i in range(0, 4):
    #     m.readshapefile('/Volumes/Transcend/map-file/gadm36_CHN_shp/gadm36_CHN_' + str(i), 'states', drawbounds=True)
    m.readshapefile('/Volumes/Transcend/map-file/gadm36_CHN_shp/gadm36_CHN_' + str(1), 'states', drawbounds=True)

    # state_names = []
    # cmap = plt.cm.YlOrRd
    # vmax = 100000000
    # vmin = 3000000
    # for shapedict in m.states_info:
    #     statename = shapedict['NL_NAME_1']
    #     p = statename.split('|')
    #     if len(p) > 1:
    #         s = p[1]
    #     else:
    #         s = p[0]
    #     s = s[:2]
    #     if s == '黑龍':
    #         s = '黑龙'
    #     state_names.append(s)
    #
    # ax = plt.gca()
    # for nshape, seg in enumerate(m.states):
    #     poly = Polygon(seg)
    #     ax.add_patch(poly)

    stations_x = []
    stations_y = []
    stations_names = []

    if data is not None:
        for station_name, station_info in data.items():
            if station_info[POSITION] is not None and station_info[POSITION] != "":
                try:
                    x, y = m(station_info[POSITION][0], station_info[POSITION][1])  # 经、纬
                    stations_x.append(x)
                    stations_y.append(y)
                    m.plot(x, y, 'c*', markersize=3)
                    # plt.annotate(station_name, xy=(x, y), xycoords='data', xytext=(+30, -30), textcoords='offset points',
                    #              fontsize=8, arrowprops=dict(arrowstyle='->', connectionstyle='arc3, rad=.2'))
                    stations_names.append(station_info[NAME_CN])
                except:
                    print("error")
            else:
                print(station_info[NAME_CN] + "没有地理位置信息")

    # texts = []
    # if stations_x and stations_y and stations_names:
    #     for xt, yt, s in zip(stations_x, stations_y, stations_names):
    #         texts.append(plt.text(xt, yt, s))
    # f = interpolate.interp1d(stations_x, stations_y)
    # x = np.linspace(min(stations_x), max(stations_x), 500)
    # y = f(x)

    # adjust_text(texts, x, y, arrowprops=dict(arrowstyle="->", color='r', lw=0.5),
    #             autoalign='', only_move={'points': 'y', 'text': 'y'})

    plt.show()


def write_neo4j_node(info, fields, node_type, key_fields):
    """
    根据节点信息，创建节点
    :param info: dict{ station name: the provided fields
    :param fields: dict, whose keys are keys of each item in info, and value is 1(mandatory) or 0 (optional)
    :param node_type : 节点类型（数据库中节点类型名，字符串）
    :param key_fields : 节点去重所需判别的字段，如火车站名等，字符串或列表，需是fields的子集
    :return: -1: 输入参数为None；2：输入参数类型错误；-3：关键字段不是字段的子集；1：查询到/创建了节点；2:节点数据错误，
                关键字段值为None或""；0：写入数据库失败
    """
    if info is None or fields is None or node_type is None or key_fields is None:
        return -1
    if not isinstance(info, dict) or not isinstance(fields, dict) or not isinstance(node_type, str) or node_type == "" or \
            not (isinstance(key_fields, list) or isinstance(key_fields, str)):
        return -2
    if isinstance(key_fields, str):
        key_fields = [key_fields]
    if not (set(fields) > set(key_fields)):
        print("关键字段中存在节点不存在的字段")
        return -3
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    success = 1
    with driver.session() as tx:
        for station_name, item in info.items():  # 对每个节点处理
            #  先match是否已有相应节点
            cypher = "MATCH (node:" + node_type.upper() + " {"
            for field in key_fields:
                cypher += field + ":'" + str(item[field]) + "',"
            cypher = cypher[0:len(cypher)-1] + "}) return node"
            node_id = tx.run(cypher)
            node_id = node_id.values()
            if len(node_id) > 0:  # 已有节点 ---- 暂不更新节点内容
                if len(node_id) > 1:
                    print("查询到了节点,但节点数大于1：" + str(node_id))
                else:
                    print("查询到了节点（不更新）：" + str(node_id[0][0]['uuid']) + ", \t" + station_name)
            else:  # 无匹配节点，创建新节点
                node_str = "{"
                for field, flag in fields.items():
                    msg = item.get(field, None)
                    if flag and (msg is None or msg == ""):
                        print("必填字段错误：" + str(item) + "." + field + ", 暂时置为-1")
                        success = 0
                    if isinstance(msg, list):
                        node_str += field + ":'" + ",".join(map(str, msg)) + "',"
                    else:
                        node_str += field + ":'" + ("-1" if msg is None else str(msg)) + "',"
                uuid_new = uuid.uuid1()
                node_str += "uuid:'" + uuid_new.__str__() + "'}"

                cypher = "CREATE (node:" + node_type.upper() + node_str + ") return node"
                node_id = tx.run(cypher)
                node_id = node_id.values()
                if len(node_id) > 0:
                    print("创建新节点成功：" + str(node_id[0][0]['uuid']) + ", \t" + station_name)
                else:
                    print("创建新节点失败：" + str(item))
                    success = 0
    return success


def get_railway_lines_from_station_info(stations):
    """
    从车站信息中提取线路名列表
    :param stations: station information, list of dict
    :return: list of string, which is the name of railway lines
    """
    if stations is None or isinstance(stations, list):
        return -1
    lines = []
    for station_name, station in stations.items():  # 前面已经处理过了，用、或\n分隔线路，是list of string
        if station[RAIL_LINES] is not None and station[RAIL_LINES] != "" \
                and station[RAIL_LINES] != -1 and station[RAIL_LINES] != "-1":
            lines.extend(station[RAIL_LINES])
    lines = list(set(lines))
    return lines


def write_neo4j_relation(start_point, end_point, edge_type, edge_attribute, directed):
    """
    创建节点之间的边，这里会判断是否已经建过
    :param start_point: dict{"info":节点信息dict, "key_fields":关键字段, "type":节点类型}
    :param end_point: dict{"info":节点信息dict, "key_fields":关键字段list}
    :param edge_type: 边类型,string
    :param edge_attribute: dict, 无属性时，应传入{}
    :param directed: boolean, 是否有向边
    :return: -1:节点类型缺失；-2：节点关键字段列表缺失；-3：节点信息缺失；-4：节点信息中关键字段信息缺失；
            -5：起点不在数据库中；-6终点不在数据库中；-7：写入数据库失败；1：创建成功；2：边已存在
    """
    if not isinstance(start_point, dict) or not isinstance(end_point, dict) or not isinstance(edge_type, str) \
       or not isinstance(edge_attribute, dict):
        return -1

    node_type1 = start_point.get("type", None)
    node_type2 = end_point.get("type", None)
    fields1 = start_point.get("key_fields", None)
    fields2 = end_point.get("key_fields", None)
    info1 = start_point.get("info", None)
    info2 = end_point.get("info", None)
    if node_type1 is None or node_type2 is None:
        print("创建节点关系时，所给节点未提供节点类型，放弃创建此关系：" + str(node_type1) + "-[" + edge_type + "]>" + str(end_point))
        return -1
    if fields1 is None or fields2 is None:
        print("创建节点关系时，所给节点未提供关键字段列表，放弃创建此关系：" + str(node_type1) + "-[" + edge_type + "]>" + str(end_point))
        return -2
    if fields1 is None or fields2 is None:
        print("创建节点关系时，所给节点未提供节点信息，放弃创建此关系：" + str(node_type1) + "-[" + edge_type + "]>" + str(end_point))
        return -3
    if isinstance(fields1, str):
        fields1 = [fields1]
    if isinstance(fields2, str):
        fields2 = [fields2]
    driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
    with driver.session() as tx:
        #  先match是否已有相应起点
        cypher = "MATCH (node:" + node_type1.upper() + " {"
        for field in fields1:
            data = info1.get(field, None)
            if data is None or data == "" or data == -1 or data == "-1":
                print("创建关系时，节点中字段" + field + "为空：" + str(info1))
                return -4
            cypher += field + ":'" + str(data) + "',"
        cypher = cypher[0:len(cypher) - 1] + "}) return node.uuid"
        node_id1 = tx.run(cypher)  # 返回节点的uuid
        node_id1 = node_id1.values()
        if len(node_id1) == 0:
            print("起点不在数据库中，先创建节点再调用本函数创建边！：" + str(start_point))
            return -5
        node_id1 = node_id1[0][0]
        #  先match是否已有相应终点
        cypher = "MATCH (node:" + node_type2.upper() + " {"
        for field in fields2:
            data = info2.get(field, None)
            if data is None or data == "" or data == -1 or data == "-1":
                print("创建关系时，节点中字段" + field + "为空：" + str(info2))
                return -4
            cypher += field + ":'" + str(data) + "',"
        cypher = cypher[0:len(cypher) - 1] + "}) return node.uuid"
        node_id2 = tx.run(cypher)  # 返回节点的uuid
        node_id2 = node_id2.values()
        if len(node_id2) == 0:
            print("终点不在数据库中，先创建节点再调用本函数创建边！:" + str(end_point))
            return -6
        node_id2 = node_id2[0][0]
        # 查询是否已有关系
        attrs = ""
        if edge_attribute:
            attrs = "{"
            for field, value in edge_attribute:
                attrs += field + ":'" + str(value) + "',"
            attrs = attrs[0:len(attrs)-1] + "}"
        if directed:
            cypher = "MATCH  (m:" + node_type1.upper() + " {uuid:'" + node_id1 + "'}) -[r: " + edge_type.upper() \
                     + "]-> (n: " + node_type2.upper() + "{uuid:'" + node_id2 + "'}) return r"
        else:
            cypher = "MATCH  (m:" + node_type1.upper() + " {uuid:'" + node_id1 + "'}) -[r: " + edge_type.upper() \
                     + "]- (n: " + node_type2.upper() + "{uuid:'" + node_id2 + "'}) return r"
        result = tx.run(cypher)
        result = result.values()
        if len(result) > 0:
            print("关系：" + str(start_point) + "-[" + edge_type + "]>" + str(end_point) + " 已存在，不重复建立")
            return 2
        else:
            # 创建边
            cypher = "MATCH  (m:" + node_type1.upper() + " {uuid:'" + node_id1 + "'}) , (n: " + node_type2.upper() + \
                     " {uuid:'" + node_id2 + "'}) " \
                     " CREATE (m) -[:" + edge_type.upper() + attrs + "]-> (n) return m, n"
            result = tx.run(cypher)
            if result is None:
                print("创建边失败：" + str(start_point) + "-[" + edge_type + "]>" + str(end_point))
                return -7
            else:
                print("创建边成功：" + str(start_point) + "-[" + edge_type + "]>" + str(end_point))
                return 1


def write_neo4j(info, mode):
    """
    生成火车站节点、火车线路节点
    :param info: 火车站节点信息list of dict
    :param mode: 1:火车站，2:铁路线
    :return:
    """
    if info is None or not isinstance(info, dict):
        print("无效的信息")
        return -1
    # 建立火车站节点
    if mode == 1:
        fields = {RAIL_LINES: 0, BELONGING_BUREAU: 0, NAME_EN: 0, NAME_CN: 1, USED_NAMES: 0,
                  POSITION: 0, PRE_STATION: 0, SUC_STATION: 0, USE_CARD: 0, FACE_RECOGNITION: 0,
                  PLATFORM_NUM: 0, RAIL_NUM: 0, ADDRESS: 0, LEVEL: 0, BIRTHDAY: 0, FOR_PASSENGER: 0,
                  FOR_LOADS: 0, ABANDONED: 0, READY: 0}
        node_type = "station".upper()
        key_fields = NAME_EN
        flag = write_neo4j_node(info, fields, node_type, key_fields)
        if flag < 0:
            print("创建火车站节点失败")
            return -1
        else:
            return 1
    # 建立铁路线节点
    if mode == 2:
        fields = {NAME_CN: 1, NAME_EN: 0, USED_NAMES: 0, STATION_START: 0, STATION_END: 0, STATION_NUM: 0, READY: 0,
                  LINES: 0, LEVEL: 0, LENGTH: 0, BALLASTED: 0, TRACK_WIDTH: 0, BUILD_TIME_START: 0,
                  WORKING_TIME_START: 0}
        node_type = "railway".upper()
        key_fields = NAME_CN
        flag = write_neo4j_node(info, fields, node_type, key_fields)
        if flag < 0:
            print("创建火车线节点失败")
            return -1
        else:
            return 1


if __name__ == "__main__":
    process_stations = True
    abstract_lines = False
    process_lines = False
    process_rel_line_line = False
    process_rel_line_station = False
    process_rel_station_station = False
    # 1.1 提取、入网：火车站
    if process_stations:
        rail_stations = get_data(sheet_name=SHEET_STATION)
        flag = write_neo4j(rail_stations, mode=1)
        if flag < 0:
            print("写入火车站数据库失败")
        else:
            print("写入火车站数据库成功")
    # 1.2 提取火车线路信息
    if abstract_lines:
        railway_lines = get_railway_lines_from_station_info(rail_stations)
        if railway_lines == -1:
            print("提取火车线路失败")
        print("火车线：\n")
        [print(line_name) for line_name in railway_lines]
    # 2. 提取、入网：火车线 --- 只有名称
    if process_lines:
        rail_lines = get_data(sheet_name=SHEET_LINE)
        flag = write_neo4j(rail_lines, mode=2)
        if flag < 0:
            print("写入火车线数据库失败")
        else:
            print("写入火车线数据库成功")
    # 3. 提取、入网：火车线-火车线
    if process_rel_line_line:
        relations = get_data(sheet_name=SHEET_LINE_RELATION)  # 返回的数据：list of tuple，（大，小）
        if isinstance(relations, int):
            print("解析火车线路之间关系失败")
        else:
            flag = 1
            edge_type = "railway_contain_railway".upper()
            for relation in relations:
                start_point = {"info": {NAME_CN: relation[0]}, "key_fields": NAME_CN, "type": "RAILWAY"}
                end_point = {"info": {NAME_CN: relation[1]}, "key_fields": NAME_CN, "type": "RAILWAY"}
                tmp = write_neo4j_relation(start_point, end_point, edge_type, {}, True)
                flag = min(tmp, flag)
            if flag < 0:
                print("建立火车线关系失败")
            else:
                print("建立火车线关系成功")

    # 4. 提取、入网：火车站-火车线 (从neo4j中读火车站节点，解析)
    if process_rel_line_station:
        edge_type = "railway_contain_station".upper()
        driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
        with driver.session() as tx:
            cypher = "match (m:" + "station".upper() + ") return m"
            stations = tx.run(cypher)
            for station in stations:
                lines = station["m"][RAIL_LINES]
                if lines is None or lines == "":
                    continue
                lines = re.split(",", lines)
                for line in lines:
                    start_point = {"info": {NAME_CN: line}, "key_fields": NAME_CN, "type": "RAILWAY"}
                    end_point = {"info": {NAME_CN: station["m"][NAME_CN]}, "key_fields": NAME_CN, "type": "station".upper()}
                    flag = write_neo4j_relation(start_point, end_point, edge_type, {}, True)
                    if flag < 0:
                        print("\t失败建立：火车站【" + station["m"][NAME_CN] + "】与所在线路【" + line + "】")
                    else:
                        print("\t成功建立：火车站【" + station["m"][NAME_CN] + "】与所在线路【" + line + "】")

    # 5. 提取、入网；火车站-火车站之间关系 (从neo4j中读火车站节点，解析)
    if process_rel_station_station:
        unrecorded_stations = []
        edge_type = "station_next_to_station".upper()
        driver = GraphDatabase.driver(uri, auth=neo4j.v1.basic_auth(username, pwd))
        with driver.session() as tx:
            cypher = "match (m:" + "station".upper() + ") return m"
            stations = tx.run(cypher)
            for station in stations:
                other_stations = ""  # 所有的前后站
                if station["m"][PRE_STATION] is not None:
                    other_stations += station["m"][PRE_STATION]
                if station["m"][SUC_STATION] is not None:
                    other_stations += ("," + station["m"][SUC_STATION])
                other_stations = re.split(",", other_stations)
                while other_stations.count("") > 0:
                    other_stations.remove("")
                for other_station in other_stations:
                    end_point = {"info": {NAME_CN: other_station}, "key_fields": NAME_CN, "type": "station".upper()}
                    start_point = {"info": {NAME_CN: station["m"][NAME_CN]}, "key_fields": NAME_CN, "type": "station".upper()}
                    flag = write_neo4j_relation(start_point, end_point, edge_type, {}, False)
                    if flag == -6 :
                        unrecorded_stations.append(other_station)
                    if flag < 0:
                        print("\t失败建立：火车站【" + station["m"][NAME_CN] + "】与所在线路【" + other_station + "】")
                    else:
                        print("\t成功建立：火车站【" + station["m"][NAME_CN] + "】与所在线路【" + other_station + "】")
        print("未记录的车站列表：\n ---------------")
        [print(station) for station in unrecorded_stations]
    # draw_figure(stations)
