from django.shortcuts import render

from utils.file_util.utils import read_from_excel
from utils.initialization import ini_result, RESULT_MSG, RESULT_CODE, wrap_result, SHEET_NAME, SHEET_TITLE


def resolve_coordinates(request):
    return render(request, 'coordinates.html')


def parse_excel_stations(request):
    """
    从Excel文件中解析出车站信息，提取的结果是excel表中的各个数据
    :param request:
    :return:
    """
    result = ini_result()
    try:
        file = request.FILES.getlist('file')
    except:
        result[RESULT_MSG] = 'failed to retrieve file in the request'
        result[RESULT_CODE] = -701
        return wrap_result(result)
    if file is None or len(file) == 0:
        result[RESULT_MSG] = 'No file in the request'
        result[RESULT_CODE] = -702
        return wrap_result(result)

    # 打开Excel文件# todo support multiple files
    result = read_from_excel(file[0], SHEET_NAME, SHEET_TITLE)

    return wrap_result(result)