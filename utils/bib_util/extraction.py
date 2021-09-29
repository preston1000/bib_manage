import os

from model_files.bibModels import Publication, Venue, Person
from utils.file_util.utils import parse_bib_file, parse_bib_file_excel
from utils.nlp.text_utils import capitalize_dict_keys, process_special_character
from utils.initialization import ini_result, RESULT_CODE, RESULT_MSG, RESULT_DATA, PUBLICATION_TYPES, FIELD_NAMES_PUB, \
    FIELD_NAMES_VENUE, FIELD_NAMES_PERSON, FIELD_OF_PUBLICATION_FOR_VENUE, VENUE_TYPE_FOR_NODE_TYPE
from utils.bib_util.utils import check_core_fields, process_author_str


def extract_bib_info_from_file(file_path, sheet_name=None, column_name=None):
    """
    从文件中提取文献信息，并返回dict. checked
    :param column_name: 列名
    :param file_path: 文件路径
    :param sheet_name: 解析excel时需要的参数, 工作表名
    :return:
    """
    result = ini_result()
    # 解析文件后缀
    ext = os.path.splitext(file_path)[-1]
    if ext is None:
        result[RESULT_CODE] = -1004
        result[RESULT_MSG] = "unable to extract he suffix of the file provided."
        return result
    # 按后缀名处理文件，获得文献的字符信息
    if ext == '.bib':
        parse_result = parse_bib_file(file_path)
    elif ext in ['.xls', '.xlsx']:
        if sheet_name is None or column_name is None:
            result[RESULT_CODE] = -707
            result[RESULT_MSG] = "excel未指定sheet and head"
            return result
        parse_result = parse_bib_file_excel(file_path, sheet_name, column_name)
    else:
        result[RESULT_CODE] = -1005
        result[RESULT_MSG] = "无法处理的的文件类型！【" + file_path + "】"
        return result

    if parse_result[RESULT_CODE] not in [1100, 1101, 1103, 1104]:
        result[RESULT_CODE] = -1006
        result[RESULT_MSG] = parse_result[RESULT_MSG]
        return result

    # 解析获得的bib信息
    bib_data = parse_result[RESULT_DATA]

    if bib_data is None or len(bib_data) == 0:
        result[RESULT_CODE] = 1007
        result[RESULT_MSG] = "文件中没有有效的文献数据"
        return result
    result[RESULT_CODE] = 1008
    result[RESULT_MSG] = "success"
    result[RESULT_DATA] = bib_data
    return result


def extract_publication_from_bib_info(entry):
    """
    从bib info中构造出PUBLICATION节点. checked
    :param entry: dict of bib info
    :return: PUBLICATION
    """
    result = ini_result()

    if entry is None or not isinstance(entry, dict) or entry.keys() is None:
        result[RESULT_CODE] = -1001
        result[RESULT_MSG] = "输入数据错误！"
        return result

    entry = capitalize_dict_keys(entry)
    node_type = entry.get("ENTRYTYPE", None)

    if node_type is None or node_type not in PUBLICATION_TYPES:
        result[RESULT_CODE] = -1002
        result[RESULT_MSG] = "unrecognized entry type:" + str(entry)
        return result

    entry_processed = {field_name: entry.get(field_name).upper() for field_name in FIELD_NAMES_PUB if field_name in entry.keys()}

    core_field_check = check_core_fields(node_type, entry_processed)

    if not core_field_check:
        result[RESULT_CODE] = -1003
        result[RESULT_MSG] = "缺少必填字段" + str(entry)
        return result

    author = entry_processed.get("AUTHOR", None)
    editor = entry_processed.get("EDITOR", None)
    title = entry_processed.get("TITLE", None)
    journal = entry_processed.get("JOURNAL", None)
    year = entry_processed.get("YEAR", None)
    volume = entry_processed.get("VOLUME", None)
    number = entry_processed.get("NUMBER", None)
    series = entry_processed.get("SERIES", None)
    address = entry_processed.get("ADDRESS", None)
    pages = entry_processed.get("PAGES", None)
    month = entry_processed.get("MONTH", None)
    note = entry_processed.get("NOTE", None)
    publisher = entry_processed.get("PUBLISHER", None)
    edition = entry_processed.get("EDITION", None)
    book_title = entry_processed.get("BOOKTITLE", None)
    organization = entry_processed.get("ORGANIZATION", None)
    chapter = entry_processed.get("CHAPTER", None)
    school = entry_processed.get("SCHOOL", None)
    field_type = entry_processed.get("type", None)
    how_published = entry_processed.get("HOWPUBLISHED", None)
    keywords = entry_processed.get("KEYWORDS", None)
    abstract = entry_processed.get("ABSTRACT", None)
    note_id = entry_processed.get("NOTEID", None)
    institution = entry_processed.get("INSTITUTION", None)
    added_by = entry_processed.get("ADDEDBY", None)
    added_date = entry_processed.get("ADDEDDATE", None)
    sci_index = entry_processed.get("SCIINDEX", None)
    ei_index = entry_processed.get("EIINDEX", None)
    ssci_index = entry_processed.get("SSCIINDEX", None)
    modified_date = entry_processed.get("MODIFIEDDATE", None)
    field_id = entry_processed.get("ID", None)

    node = Publication("", node_type, author=author, editor=editor, title=title, journal=journal, year=year,
                       volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                       note=note, publisher=publisher, edition=edition, book_title=book_title, organization=organization,
                       chapter=chapter, school=school, type=field_type, how_published=how_published, keywords=keywords,
                       abstract=abstract, note_id=note_id, institution=institution, added_by=added_by,
                       added_date=added_date, sci_index=sci_index, ei_index=ei_index, ssci_index=ssci_index,
                       modified_date=modified_date, id=field_id)

    result[RESULT_CODE] = 1001
    result[RESULT_MSG] = "success"
    result[RESULT_DATA] = node
    return result


def extract_venue_from_bib_info(entry):
    """
    从节点信息中，提取出venue节点.checked
    :param entry:
    :return:
    """
    result = ini_result()

    entry = capitalize_dict_keys(entry)

    if "VENUE_NAME" not in entry.keys() or len(entry["VENUE_NAME"]) == 0 or "VENUE_TYPE" not in entry.keys() or len(
            entry["VENUE_TYPE"]) == 0:
        result[RESULT_CODE] = -1007
        result[RESULT_MSG] = "缺少必填字段"
        return result

    info = {field_name: process_special_character(entry.get(field_name, "")) for field_name in FIELD_NAMES_VENUE}

    node = Venue(uuid="", venue_name=info["VENUE_NAME"], abbr=info["ABBR"], venue_type=info["VENUE_TYPE"],
                 publisher=info["PUBLISHER"], year=info["YEAR"], address=info["ADDRESS"], sci_index=info["SCI_INDEX"],
                 ei_index=info["EI_INDEX"], ssci_index=info["SSCI_INDEX"], note=info["NOTE"],
                 start_year=info["START_YEAR"])
    result[RESULT_CODE] = 1005
    result[RESULT_MSG] = "success"
    result[RESULT_DATA] = node
    return result


def extract_person_from_bib_info(entry):
    """
    从节点信息中，提取出Person节点。checked
    :param entry:
    :return:
    """
    result = ini_result()

    entry = capitalize_dict_keys(entry)

    if "FULL_NAME" not in entry.keys() or len(entry["VENUE_NAME"]) == 0:
        result[RESULT_CODE] = -1008
        result[RESULT_MSG] = "缺少必填字段"
        return result

    info = {field_name: process_special_character(entry.get(field_name, "")) for field_name in FIELD_NAMES_PERSON}

    node = Person(uuid="", full_name=info["FULL_NAME"], first_name=info["FIRST_NAME"], middle_name=info["MIDDLE_NAME"],
                  last_name=info["LAST_NAME"], name_ch=info["NAME_CN"], first_name_ch=info["FIRST_NAME_CN"],
                  last_name_ch=info["LAST_NAME_CN"], institution=info["INSTITUTION"],
                  research_interest=info["RESEARCH_INTEREST"], note=info["NOTE"], added_by=info["ADDED_BY"],
                  added_date=info["ADDED_DATE"])
    result[RESULT_CODE] = 1006
    result[RESULT_MSG] = "success"
    result[RESULT_DATA] = node
    return result


def extract_rel_publish_in_from_pub_info(publications):
    """
    从数据库中读取到的Publication信息的journal或booktitle字段，提取venue信息，然后构建Publication-Published_in-Venue关系。checked
    :param publications: list of publication
    :return:
    """
    result = ini_result()
    if publications is None or not isinstance(publications, list):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "the given data is not valid"
        return result

    flag = [isinstance(publication, Publication) for publication in publications]
    if not all(flag):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "the given data is not valid"
        return result

    unprocessed_pub_uuid = []
    processed = []
    for publication in publications:
        if publication.node_type not in FIELD_OF_PUBLICATION_FOR_VENUE.keys():
            unprocessed_pub_uuid.append(publication.uuid)
            continue

        field = FIELD_OF_PUBLICATION_FOR_VENUE.get(publication.node_type)
        venue_name = publication.__dict__[field]
        venue_type = VENUE_TYPE_FOR_NODE_TYPE.get(publication.node_type)
        venue = Venue("", venue_type, venue_name)
        processed.append({"pub": publication, "venue": venue})

    unprocessed_pub_uuid = None if unprocessed_pub_uuid == [] else unprocessed_pub_uuid
    processed = None if processed == [] else processed

    if unprocessed_pub_uuid is not None:
        result[RESULT_CODE] = 1010
        result[RESULT_MSG] = "partially filtered"
    else:
        result[RESULT_CODE] = 1009
        result[RESULT_MSG] = "success"

    result[RESULT_DATA] = {"failed": unprocessed_pub_uuid, "success": processed}

    return result


def extract_rel_author_by_from_pub_info(publications):
    """
    从数据库中读取到的Publication信息的author字段，提取person信息，然后构建Publication-Authored_by-Person关系。checked
    :param publications: list of publication
    :return:
    """
    result = ini_result()
    if publications is None or not isinstance(publications, list):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "the given data is not valid"
        return result

    flag = [isinstance(publication, Publication) for publication in publications]
    if not all(flag):
        result[RESULT_CODE] = -901
        result[RESULT_MSG] = "the given data is not valid"
        return result

    unprocessed_pub_uuid = []
    processed = []
    for publication in publications:
        author_names = process_author_str(publication.author)
        if author_names is None:
            unprocessed_pub_uuid.append(publication)
            continue
        for author_name in author_names:
            person = Person("", author_name["full_name"], author_name["first_name"], author_name["middle_name"], author_name["last_name"])

            processed.append({"pub": publication, "venue": person, "index": author_name["index"]})

    unprocessed_pub_uuid = None if unprocessed_pub_uuid == [] else unprocessed_pub_uuid
    processed = None if processed == [] else processed

    if unprocessed_pub_uuid is not None:
        result[RESULT_CODE] = 1010
        result[RESULT_MSG] = "partially filtered"
    else:
        result[RESULT_CODE] = 1009
        result[RESULT_MSG] = "success"

    result[RESULT_DATA] = {"failed": unprocessed_pub_uuid, "success": processed}

    return result


if __name__ == "__main__":
    # parse_excel('C:\\Users\\G314\\AppData\\Local\\kingsoft\\WPS Cloud Files\\userdata\\qing\\filecache\\独'
    #             '自行走的猪的云文档\\我的文档\\文献总结.xlsx')

    extract_result = extract_bib_info_from_file('file.xlsx')
    # extract_result = do_extract('reference.bib')
    # extract_result = do_extract('bibtex.bib')
    print(str(extract_result))