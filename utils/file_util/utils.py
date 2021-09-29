
import os
import xlrd
import bibtexparser
from utils.initialization import ini_result, RESULT_CODE, RESULT_DATA, RESULT_MSG


def read_from_excel(file, sheet_name, column_specified):
    result = ini_result()
    try:
        wb = xlrd.open_workbook(filename=None, file_contents=file.read())  # 打开文件
    except xlrd.XLRDError:
        result["code"] = -703
        result[RESULT_MSG] = '打开Excel文件失败'
        return result

    # 读取工作表
    try:
        sheet_content = wb.sheet_by_name(sheet_name)  # 通过名字获取表格
    except ValueError:
        result["code"] = -704
        result[RESULT_MSG] = '读取Excel指定工作簿失败'
        return result

    # 读取表头
    try:
        sheet_title = sheet_content.row_values(0)
    except:
        result["code"] = -705
        result[RESULT_MSG] = '读取Excel工作簿表头失败'
        return result

    # 按列读取车站信息
    if column_specified is not None and isinstance(column_specified, list):
        correspondence = {}
        for column_name in column_specified:
            try:
                col_index = sheet_title.index(column_name)
            except ValueError:
                print("Excel文件中未包含<" + column_name + ">列")
                continue
            correspondence[col_index] = column_name
    else:
        correspondence = {i: j for i, j in enumerate(sheet_title)}

    # 读取内容
    content = []
    for iii in range(1, sheet_content.nrows):  # index是行下标
        tmp = {"index": iii}
        for index, column_name in correspondence:
            value = sheet_content.cell_value(iii, index)
            if value == "":
                print("第" + str(iii) + "行文献没有" + column_name + "信息【" + str(sheet_content.row_values(iii)) + "】")
                tmp[column_name] = None
            else:
                tmp[column_name] = value
        content.append(tmp)

    result["code"] = 700
    result[RESULT_MSG] = '读取Excel工作簿成功'
    result[RESULT_DATA] = content


def parse_bib_file(file_name):
    """
    从bib文件中解析出文献信息. checked
    :param file_name:
    :return:
    """
    result = ini_result()
    if file_name is None or not isinstance(file_name, str):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "invalid arguments"
        return result
    try:
        with open(file_name, encoding="utf-8") as bib_file:
            bib_database = bibtexparser.load(bib_file)
    except:
        result[RESULT_CODE] = -1100
        result[RESULT_MSG] = "文件打开失败:【" + file_name + "】"
        return result

    if bib_database is not None:
        result[RESULT_CODE] = 1100
        result[RESULT_MSG] = "成功解析bib文件【" + file_name + "】"
        result[RESULT_DATA] = bib_database.entries
    else:
        result[RESULT_CODE] = 1101
        result[RESULT_MSG] = "未从bib文件中解析出结果！【" + file_name + "】"
    return result


def save_file_stream_on_disk(file, dir, filename):
    """
    把文件流写入本地临时文件
    :param filename: file name
    :param dir: directory
    :param file: file stream
    :return:
    """
    os.makedirs(dir, exist_ok=True)
    file_path = os.path.join(dir, filename)
    try:
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
            destination.close()
        return file_path
    except:
        return None


def parse_bib_file_excel(file_name, sheet_name, column_name):
    """
    从Excel文件中解析出文献信息，提取的结果是excel表中的各个数据，这里并不处理数据
    :param column_name: 列名, e.g. bib
    :param sheet_name: 要分析的工作表名称, e.g. deep learning
    :param file_name: str 文件名
    :return:
    """
    result = ini_result()

    if file_name is None or not isinstance(file_name, str) or sheet_name is None or not isinstance(sheet_name, str) \
            or column_name is None or not isinstance(column_name, str):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "invalid arguments"
        return result

    try:
        wb = xlrd.open_workbook(filename=file_name)  # 打开文件
    except:
        result[RESULT_CODE] = -703
        result[RESULT_MSG] = '打开Excel文件失败'
        return result

    try:
        sheet_content = wb.sheet_by_name(sheet_name)  # 通过名字获取表格
    except:
        result[RESULT_CODE] = -704
        result[RESULT_MSG] = '读取Excel指定工作簿失败'
        return result
    try:
        sheet_title = sheet_content.row_values(0)
    except:
        result[RESULT_CODE] = -705
        result[RESULT_MSG] = '读取Excel工作簿表头失败'
        return result

    try:
        col_index = sheet_title.index(column_name)  # 列下标
    except ValueError:
        result[RESULT_CODE] = -706
        result[RESULT_MSG] = '指定的工作表中没有' + column_name + '列'
        return result

    content = []
    counter_bib = 0  # 成功解析出的行数
    counter_all = sheet_content.nrows - 1  # 总信息行数
    counter_null = 0  # 空白行个数
    for index in range(1, sheet_content.nrows):  # index是行下标
        value = sheet_content.cell_value(index, col_index)
        if value == "":
            print("第" + str(index) + "行文献没有bib信息【" + str(sheet_content.row_values(index)) + "】")
            counter_null += 1
            continue
        try:
            tmp = bibtexparser.loads(value)
        except:
            print("第" + str(index) + "行文献解析bib过程失败【" + str(sheet_content.row_values(index)) + "】")  # 内部错误，不返回错误码
            continue
        if tmp is not None:
            content.append(tmp.entries[0])
            counter_bib += counter_bib
        else:
            print("第" + str(index) + "行文献解析bib过程失败2【" + str(sheet_content.row_values(index)) + "】")  # 内部错误，不返回错误码

    if counter_bib == (counter_all - counter_null):
        result[RESULT_MSG] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + \
                        ">列全部信息(除空白行)均有效解析，共" + str(counter_all) + "行，" + str(counter_null) + "空白行，" + \
                        str(counter_bib) + "成功解析"
        result[RESULT_CODE] = 1102
        result[RESULT_DATA] = content
        return result

    if counter_null == counter_all:
        result[RESULT_MSG] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + ">列全部为空白"
        result[RESULT_CODE] = 1103
        return result

    if (counter_all - counter_null) > counter_bib > 0:
        result[RESULT_MSG] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + \
                        ">列全部信息(除空白行)部分有效解析，共" + str(counter_all) + "行，" + str(counter_null) + "空白行，" + \
                        str(counter_bib) + "成功解析"
        result[RESULT_CODE] = 1104
        result[RESULT_DATA] = content
        return result

    if counter_all > counter_null and counter_bib == 0:
        result[RESULT_MSG] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + ">列（除空白外）全部解析失败"
        result[RESULT_CODE] = -1101
        return result

    result[RESULT_MSG] = "【总结】Excel文件<" + file_name + ">的<" + sheet_name + ">页<" + column_name + ">列。结果未考虑！"
    result[RESULT_CODE] = -1102
    return result