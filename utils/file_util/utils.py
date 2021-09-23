
import xlrd


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