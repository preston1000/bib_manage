
import xlrd
import bibtexparser


def read_from_excel(file, sheet_name, column_specified):
    result = {"code": -1, "msg": "", "data": None}
    try:
        wb = xlrd.open_workbook(filename=None, file_contents=file.read())  # 打开文件
    except xlrd.XLRDError:
        result["code"] = -703
        result["msg"] = '打开Excel文件失败'
        return result

    # 读取工作表
    try:
        sheet_content = wb.sheet_by_name(sheet_name)  # 通过名字获取表格
    except ValueError:
        result["code"] = -704
        result["msg"] = '读取Excel指定工作簿失败'
        return result

    # 读取表头
    try:
        sheet_title = sheet_content.row_values(0)
    except:
        result["code"] = -705
        result["msg"] = '读取Excel工作簿表头失败'
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
    result["msg"] = '读取Excel工作簿成功'
    result["data"] = content


def parse_bib_file(file_name):
    """
    从bib文件中解析出文献信息
    :param file_name:
    :return:
    """
    result = {"data": "", "msg": "", "code": 0}
    with open(file_name, encoding="utf-8") as bib_file:
        try:
            bib_database = bibtexparser.load(bib_file)
        except:
            result["code"] = -101
            result["msg"] = "无法解析bib文件【" + file_name + "】"
            return result
        if bib_database is not None:
            result["code"] = 100
            result["msg"] = "成功解析bib文件【" + file_name + "】"
            result["data"] = bib_database.entries
            return result
        else:
            result["code"] = -102
            result["msg"] = "未从bib文件中解析出结果！【" + file_name + "】"
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
