import re
from utils.util_operation import get_value_by_key


def string_util(string):
    if string is None or string is "":
        return False
    return True


def process_person_names(names):
    """
    将文献字段中的author，映射为处理过的author list，list中每个是一个字典，name&index
    :param names:list of strings
    :return:dict, key是原author字段，value是list of dict，每个dict={"name", "index"}
    """
    if names is None:
        return None
    names_mapping = {}
    for name in names:
        #  去除前后空格，转成大写 name是包含了很多作者 用and连接的
        tmp = name.strip().upper()
        #  去掉重复空格
        tmp = " ".join(tmp.split())
        # 转换单引号
        # tmp = tmp.replace("'", '\\\'')
        # 转换特殊字符
        tmp = process_special_character(tmp)
        # 分开多个作者
        author_list = tmp.split(" AND ")
        # 将姓名格式统一为first_name last_name格式
        tmp_list = []
        for i in range(0, len(author_list)):
            author = author_list[i].strip()
            if author.find(",") > -1:
                tmp_l = author.split(",")
                tmp_l = [iii.strip() for iii in tmp_l]
                tmp_l = " ".join(tmp_l[::-1])
                tt = {"name": tmp_l, "index": (i+1)}
                tmp_list.append(tt)
            else:
                tt = {"name": author, "index": (i+1)}
                tmp_list.append(tt)

        names_mapping[name] = tmp_list
    return names_mapping


def check_special(entries, field):
    txt = entries.get(field.upper(), None)
    txt = "" if txt is None else txt.upper()
    txt = process_special_character(txt)
    return txt


def check_special2(entries, field):
    txt = get_value_by_key(entries, field.upper())
    txt = "" if txt is None else txt
    txt = process_special_character(txt)
    return txt


def check_number(entries, field):
    txt = get_value_by_key(entries, field)
    txt = "" if txt is None else int(txt)
    return txt


def check_ordinary(entries, field):
    txt = get_value_by_key(entries, field)
    txt = "" if txt is None else txt.upper()
    return txt


def process_special_character(word):
    """
    处理了特殊转义字符、全部转成大写，去掉中间多余的空格 todo: 题目中的公式怎么搞？大小写变换时有点复杂
    :param word:
    :return:
    """
    if word is None or word == "":
        return ""
    if word.find("AMICO") >= 0:
        print(word)
    # 转换latex特殊字符
    # if word.find("\\URL") >= 0:
    #     print("rul")
    mappings = {"\\`{a}": 'à',
                "\\'{a}": 'á',
                "\^{a}": 'â',
                "\\\"{a}": 'ä',
                "\\'{c}": 'ć',
                "\\c{c}": 'ç',
                "\\v{c}": 'č',
                "\\`{e}": 'è',
                "\\'{e}": 'é',
                "\\^{e}": 'ê',
                "\\\"{e}": 'ë',
                "\\={e}": 'ē',
                "\\.{e}": 'ė',
                "\\c{e}": 'ę',
                "\\^{i}": 'î',
                "\\\"{i}": 'ï',
                "\\'{i}": 'í',
                "\\={i}": 'ī',
                "\\c{i}": 'į',
                "\\`{i}": 'ì',
                "\\v{n}": 'ñ',
                "\\'{n}": 'ń',
                "\\^{o}": 'ô',
                "\\\"{o}": 'ö',
                "\\`{o}": 'ò',
                "\\'{o}": 'ó',
                '\\ae': 'œ',
                '\\o': 'ø',
                "\\={o}": 'ō',
                "\\~{o}": 'õ',
                "\\ss": 'ß',
                "\\'{s}": 'ś',
                "\\v{s}": 'š',
                "\\^{u}": 'û',
                "\\\"{u}": 'ü',
                "\\`{u}": 'ù',
                "\\'{u}": 'ú',
                "\\={u}": 'ū',
                "\\\"{y}": 'ÿ',
                "\\v{z}": 'ž',
                "\\'{z}": 'ź',
                "\\.{z}": 'ż',
                "{\\l}": "ł",
                "\\url": "url",
                "\\a{a}": "å",
                "\\infty": "infty"}  # 带上下标的字母
    for (special, replace) in mappings.items():
        try:
            word = word.replace(special, replace)
        except:
            print("failed: " + str(word))
    # 转单引号
    word = word.replace("'", '\\\'')
    # 转&
    word = word.replace("\&", '&')
    # 转$
    # word = word.replace("$", '\$')
    # 转url
    word = word.replace("\\URL", '\\\\URL')
    # 转希腊字母
    greek_letters = {
        "{\\aa}": "å",
        "{\\AA}": "å",
        "\\alpha": "\\\\alpha",
        "\\beta": "\\\\beta",
        "\\chi": "\\\\chi",
        "\\delta": "\\\\delta",
        "\\Delta": "\\\\Delta",
        "\\epsilon": "\\\\epsilon",
        "\\eta": "\\\\eta",
        "\\gamma": "\\\\gamma",
        "\\Gamma": "\\\\Gamma",
        "\\iota": "\\\\iota",
        "\\kappa": "\\\\kappa",
        "\\lambda": "\\\\lambda",
        "\\Lambda": "\\\\Lambda",
        "\\mu": "\\\\mu",
        "\\nu": "\\\\nu",
        "\\omega": "\\\\omega",
        "\\Omega": "\\\\Omega",
        "\\phi": "\\\\phi",
        "\\Phi": "\\\\Phi",
        "\\pi": "\\\\pi",
        "\\Pi": "\\\\Pi",
        "\\psi": "\\\\psi",
        "\\Psi": "\\\\Psi",
        "\\rho": "\\\\rho",
        "\\sigma": "\\\\sigma",
        "\\Sigma": "\\\\Sigma",
        "\\tau": "\\\\tau",
        "\\theta": "\\\\theta",
        "\\Theta": "\\\\Theta",
        "\\upsilon": "\\\\upsilon",
        "\\Upsilon": "\\\\Upsilon",
        "\\xi": "\\\\xi",
        "\\Xi": "\\\\Xi",
        "\\zeta": "\\\\zeta",
        "\\digamma": "\\\\digamma",
        "\\varepsilon": "\\\\varepsilon",
        "\\varkappa": "\\\\varkappa",
        "\\varphi": "\\\\varphi",
        "\\varpi": "\\\\varpi",
        "\\varrho": "\\\\varrho",
        "\\varsigma": "\\\\varsigma",
        "\\vartheta": "\\\\vartheta",
    }
    for (letter, letter_new) in greek_letters.items():
        word = word.replace(letter, letter_new)
    # 全部转大写
    word = word.upper()
    # 去除多余空格
    word = word.split(" ")
    word = [item.strip() for item in word]
    word = " ".join(word)
    return word


def process_venue_names(names):
    """
    将文献字段中的venue，映射为处理过的venue
    :param names:
    :return:
    """
    if names is None:
        return None
    names_mapping = {}
    for name in names:
        #  去除前后空格，转成大写
        tmp = name.strip().upper()
        #  去掉重复空格
        tmp = " ".join(tmp.split())
        #  替换某些简写等 todo: 未实现
        tmp = tmp
        names_mapping[name] = tmp
    return names_mapping


def analyze_person_name(params):
    processed_name = {"first_name": "", "middle_name": "", "last_name": "", "msg": "", "status": -1}
    name = params.get("textTo", None)
    lang = params.get("lang", None)
    if name is None or lang is None or not isinstance(name, str) or not isinstance(lang, str) or \
       not (lang == "CH" or lang == "EN"):
            processed_name["status"] = -1
            processed_name["msg"] = "输入参数不对"
            return processed_name
    first_name, middle_name, last_name = ["", "", ""]
    if lang == "EN":
        name = name.strip()
        if name is None or name == "":
            return processed_name
        if name.find(",") > -1:  # 姓 名
            names = name.split(",")
            names = [tmp.strip() for tmp in names]
            if len(names) == 2:
                last_name = names[0]
            else:
                processed_name["status"] = -1
                processed_name["msg"] = "名字中不能多于1个逗号"
                print("名字中不能多于1个逗号")
                return processed_name
            if names[1].find(" ") > -1:
                sub_names = names[1].split()
                sub_names = [tmp.strip() for tmp in sub_names]
                first_name = sub_names[0]
                if len(sub_names) == 2:
                    middle_name = sub_names[1]
                elif len(sub_names) > 2:
                    middle_name = " ".join(sub_names[1:])
                else:
                    processed_name["status"] = -1
                    processed_name["msg"] = "带逗号格式的名字解析中间名过程错误"
                    print("带逗号格式的名字解析中间名过程错误")
                    return processed_name
            else:
                first_name = names[1]
        else:  # 名 姓
            names = name.split()
            names = [tmp.strip() for tmp in names]
            if len(names) == 1:
                last_name = names[0]
            elif len(names) == 2:
                first_name = names[0]
                last_name = names[1]
            elif len(names) == 3:
                first_name = names[0]
                last_name = names[-1]
                middle_name = names[1]
            else:
                first_name = names[0]
                last_name = names[-1]
                middle_name = " ".join(names[1:-1])
    else:
        name = name.strip()
        p = re.compile('([\u4e00-\u9fa5])')
        name = p.split(name)
        name = [item.strip() for item in name if item != ""]
        if len(name) == 1:
            last_name = name[0]
        else:
            first_name = "".join(name[1:])
            last_name = name[0]
    processed_name["first_name"] = first_name
    processed_name["middle_name"] = middle_name
    processed_name["last_name"] = last_name
    processed_name["status"] = 1
    processed_name["msg"] = "success"
    return processed_name


def null_string(string):
    if not isinstance(string, str):
        return ""
    if string is None or string.strip() == "" or string == "null":
        return ""
    else:
        return string.strip()


def null_int(value):
    if value is None:
        return 0
    else:
        return value


def process_pages(data):
    if data is None or not isinstance(data, str):
        return None
    data = data.split()
    if len(data) == 1:
        data = data[0]
    elif len(data) == 3:
        data = data[0] + '-' + data[2]
    else:
        print(data)
        data = data[0] + '-' + data[-1]
    return data


def capitalize_dict_keys(entry):
    """
    将每个文献中的字段名称转成大写，并对应其在entry中的key
    :param entry:
    :return:
    """
    mapping = {}
    for (key, value) in entry.items():
        mapping[key.upper()] = value
    return mapping