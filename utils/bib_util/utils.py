from utils.initialization import MANDATORY_FIELDS


def process_search_condition(pub_info):
    """
    从网页中提取的搜索条件构造搜索参数dict
    :param pub_info: dict of information obtained from webpages
    :return: dict of parameters
    """
    parameters = {}
    # 标题关键字
    title = pub_info.get("title", None)
    if not(title is None or title == ""):
        parameters["title"] = title
    # 起止时间
    start_time = pub_info.get("startTime", None)
    end_time = pub_info.get("endTime", None)
    if not (start_time is None or start_time == ""):
        parameters["startTime"] = start_time
    if not (end_time is None or end_time == ""):
        parameters["endTime"] = end_time
    # 作者
    author = pub_info.get("author", None)
    if not (author is None or author == ""):
        parameters["author"] = author
    # 文章索引
    paper_index = pub_info.get("paperIndex", None)
    if not (paper_index is None or paper_index == ""):
        parameters["paperIndex"] = paper_index
    # 文献类型
    node_type = pub_info.get("node_type", None)
    if node_type is not None and node_type != "":
        parameters["node_type"] = node_type.upper()
    # 检查是否有效条件
    if parameters == {}:
        parameters = None
    return parameters


def split_pages(pages):
    page1 = None
    page2 = None

    # 处理页码
    if pages is not None and pages != "null" and pages != "":
        pages = str.split(pages, "-")
        tmp = [page.strip() for page in pages if page.strip() != ""]
        if len(tmp) == 2:
            page1 = tmp[0]
            page2 = tmp[1]
    return page1, page2


def split_name(name, authors):
    """
    把作者名字分开，且要提取作者的排名。 todo 可优化
    :param name:
    :param authors:
    :return:
    """
    if name is None or name == "" or name == "null":
        return None
    else:
        index = authors.index(name)
        name = [item.strip() for item in name.split(" ")]
        if len(name) < 1:
            print("姓名解析错误:" + name)
            return None
        elif len(name) == 1:
            result = {"firstName": "", "middleName": "", "lastName": name[0], "ranking": index}
        elif len(name) == 2:
            result = {"firstName": name[0], "middleName": "", "lastName": name[0], "ranking": index}
        else:
            result = {"firstName": name[0], "middleName": " ".join(name[1:len(name)-1]), "lastName": name[-1],
                      "ranking": index}
        return result


def check_core_fields(node_type, keys_in_bib):

    if keys_in_bib is None:
        return False
    for field in MANDATORY_FIELDS[node_type]:
        if isinstance(field, str) and field in keys_in_bib:
            continue
        if isinstance(field, list):
            tmp = [tmp_f in keys_in_bib for tmp_f in field]
            if any(tmp):
                continue
        return False
    return True


def process_author_str(authors):
    """
    解析字符串表示的作者列表，如“A and B and C",得到作者列表，包括[{first_name:, middle_name, last_name, full_name}]
    :param authors: str
    :return:
    """
    if authors is None or not isinstance(authors, str) or len(authors) < 1:
        return None
    authors = [author.strip() for author in authors.split(" AND ")]

    author_info = []
    strange_names = []
    for index, author in enumerate(authors):
        info = {"first_name": None, "middle_name": None, "last_name": None, "full_name": author, "index": index + 1}
        if "," in author:
            parts = [part.strip() for part in author.split(",")]
            info["last_name"] = parts[-1]

            if len(parts) < 2:
                strange_names.append(author)
                continue
            parts = [part.strip() for part in parts[0].split(" ")]
            info["first_name"] = parts[0]

            if len(parts) > 1:
                info["middle_name"] = " ".join(parts[1:])

        else:
            parts = [part.strip() for part in author.split(" ")]
            if len(parts) < 2:
                strange_names.append(author)
                continue
            info["first_name"] = parts[0]
            info["last_name"] = parts[-1]
            if len(parts) > 2:
                info["middle_name"] = " ".join(info[1:-1])
        author_info.append(info)

    return