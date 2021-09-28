from utils.models import Publication, Venue, Person
from utils.util_operation import get_value_by_key
from utils.util_operation_2 import upperize_dict_keys
from utils.nlp.text_utils import process_special_character


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


def extract_publication(entry):
    entry_parsed_keys = upperize_dict_keys(entry)
    entry_type = entry.get(entry_parsed_keys["ENTRYTYPE"], None).upper()

    if entry_type is None:
        print("unrecognized entry (type):" + str(entry))
        return None
    elif entry_type == "ARTICLE":
        author = get_value_by_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = get_value_by_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        journal = get_value_by_key(entry_parsed_keys, "journal".upper())
        journal = "" if journal is None else entry.get(journal, None)
        journal = process_special_character(journal)
        year = get_value_by_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = get_value_by_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = get_value_by_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        pages = get_value_by_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        month = get_value_by_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = get_value_by_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if author is None or title is None or journal is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, title=title, journal=journal, year=year,
                           volume=volume, number=number, pages=pages, month=month, note=note)
    elif entry_type == "BOOK":
        author = get_value_by_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = get_value_by_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = get_value_by_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        publisher = get_value_by_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = get_value_by_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = get_value_by_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = get_value_by_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = get_value_by_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        address = get_value_by_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        edition = get_value_by_key(entry_parsed_keys, "edition".upper())
        edition = "" if edition is None else entry.get(edition, None)
        month = get_value_by_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = get_value_by_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if (author is None and editor is None) or title is None or publisher is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title,
                           publisher=publisher,
                           year=year,
                           volume=volume, number=number, series=series, address=address, month=month,
                           edition=edition, note=note)
    elif entry_type == "INBOOK":
        author = get_value_by_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = get_value_by_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = get_value_by_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        chapter = get_value_by_key(entry_parsed_keys, "chapter".upper())
        chapter = "" if chapter is None else entry.get(chapter, None)
        pages = get_value_by_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        publisher = get_value_by_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = get_value_by_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = get_value_by_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = get_value_by_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = get_value_by_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        book_type = get_value_by_key(entry_parsed_keys, "type".upper())
        book_type = "" if book_type is None else entry.get(book_type, None)
        address = get_value_by_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        edition = get_value_by_key(entry_parsed_keys, "edition".upper())
        edition = "" if edition is None else entry.get(edition, None)
        month = get_value_by_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = get_value_by_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if (author is None and editor is None) or title is None or (chapter is None and pages is None) or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, journal=None,
                           year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=edition, book_title=None, organization=None,
                           chapter=chapter, school=None, type=book_type, how_published=None, keywords=None,
                           institution=None)
    elif entry_type == "INPROCEEDINGS" or entry_type == "CONFERENCE":
        author = get_value_by_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = get_value_by_key(entry_parsed_keys, "editor".upper())
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = get_value_by_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        book_title = get_value_by_key(entry_parsed_keys, "booktitle".upper())
        book_title = "" if book_title is None else entry.get(book_title, None)
        book_title = process_special_character(book_title)
        publisher = get_value_by_key(entry_parsed_keys, "publisher".upper())
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = get_value_by_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        volume = get_value_by_key(entry_parsed_keys, "volume".upper())
        volume = "" if volume is None else entry.get(volume, None)
        number = get_value_by_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        series = get_value_by_key(entry_parsed_keys, "series".upper())
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        pages = get_value_by_key(entry_parsed_keys, "pages".upper())
        pages = "" if pages is None else entry.get(pages, None)
        address = get_value_by_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        organization = get_value_by_key(entry_parsed_keys, "organization".upper())
        organization = "" if organization is None else entry.get(organization, None)
        organization = process_special_character(organization)
        month = get_value_by_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = get_value_by_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        if author is None or title is None or book_title is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type=entry_type, author=author, editor=editor, title=title, journal=None,
                           year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=None, book_title=book_title,
                           organization=organization,
                           chapter=None, school=None, type=None, how_published=None, keywords=None, institution=None)
    elif entry_type == "INCOLLECTION":
        author = entry_parsed_keys.get("author".upper(), None)
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        editor = entry_parsed_keys.get("editor".upper(), None)
        editor = "" if editor is None else entry.get(editor, None)
        editor = process_special_character(editor)
        title = entry_parsed_keys.get("title".upper(), None)
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        book_title = entry_parsed_keys.get("booktitle".upper(), None)
        book_title = "" if book_title is None else entry.get(book_title, None)
        book_title = process_special_character(book_title)
        publisher = entry_parsed_keys.get("publisher".upper(), None)
        publisher = "" if publisher is None else entry.get(publisher, None)
        publisher = process_special_character(publisher)
        year = entry_parsed_keys.get("year".upper(), None)
        year = "" if year is None else entry.get(year, None)
        volume = entry_parsed_keys.get("volume".upper(), None)
        volume = "" if volume is None else entry.get(volume, None)
        number = entry_parsed_keys.get("number".upper(), None)
        number = "" if number is None else entry.get(number, None)
        series = entry_parsed_keys.get("series".upper(), None)
        series = "" if series is None else entry.get(series, None)
        series = process_special_character(series)
        pages = entry_parsed_keys.get("pages".upper(), None)
        pages = "" if pages is None else entry.get(pages, None)
        address = entry_parsed_keys.get("address".upper(), None)
        address = "" if address is None else entry.get(address, None)
        edition = entry_parsed_keys.get("edition".upper(), None)
        edition = "" if edition is None else entry.get(edition, None)
        month = entry_parsed_keys.get("month".upper(), None)
        month = "" if month is None else entry.get(month, None)
        note = entry_parsed_keys.get("note".upper(), None)
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        book_type = entry_parsed_keys.get("type".upper(), None)
        book_type = "" if book_type is None else entry.get(book_type, None)
        chapter = entry_parsed_keys.get("chapter".upper(), None)
        chapter = "" if chapter is None else entry.get(chapter, None)
        chapter = process_special_character(chapter)
        if author is None or title is None or book_title is None or year is None or publisher is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="INCOLLECTION", author=author, editor=editor, title=title, journal=None,
                           year=year,
                           volume=volume, number=number, series=series, address=address, pages=pages, month=month,
                           note=note, publisher=publisher, edition=edition, book_title=book_title, organization=None,
                           chapter=chapter, school=None, type=book_type, how_published=None, keywords=None,
                           institution=None)
    elif entry_type == "MISC":
        author = entry_parsed_keys.get("author".upper(), None)
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = entry_parsed_keys.get("title".upper(), None)
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        how_published = entry_parsed_keys.get("howpublished".upper(), None)
        how_published = "" if how_published is None else entry.get(how_published, None)
        year = entry_parsed_keys.get("year".upper(), None)
        year = "" if year is None else entry.get(year, None)
        month = entry_parsed_keys.get("month".upper(), None)
        month = "" if month is None else entry.get(month, None)
        note = entry_parsed_keys.get("note".upper(), None)
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        node = Publication(uuid="", node_type="MISC", author=author, editor=None, title=title, journal=None, year=year,
                           volume=None, number=None, series=None, address=None, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=None, type=None, how_published=how_published, keywords=None,
                           institution=None)
    elif entry_type == "PHDTHESIS":
        author = entry_parsed_keys.get("author".upper(), None)
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = entry_parsed_keys.get("title".upper(), None)
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        school = entry_parsed_keys.get("school".upper(), None)
        school = "" if school is None else entry.get(school, None)
        year = entry_parsed_keys.get("year".upper(), None)
        year = "" if year is None else entry.get(year, None)
        month = entry_parsed_keys.get("month".upper(), None)
        month = "" if month is None else entry.get(month, None)
        note = entry_parsed_keys.get("note".upper(), None)
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = entry_parsed_keys.get("address".upper(), None)
        address = "" if address is None else entry.get(address, None)
        keywords = entry_parsed_keys.get("keywords".upper(), None)
        keywords = "" if keywords is None else entry.get(keywords, None)
        keywords = process_special_character(keywords)
        if author is None or title is None or school is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="PHDTHESIS", author=author, editor=None, title=title, journal=None,
                           year=year,
                           volume=None, number=None, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=school, type=None, how_published=None, keywords=keywords,
                           institution=None)
    elif entry_type == "MASTERSTHESIS":
        author = entry_parsed_keys.get("author".upper(), None)
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = entry_parsed_keys.get("title".upper(), None)
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        school = entry_parsed_keys.get("school".upper(), None)
        school = "" if school is None else entry.get(school, None)
        year = entry_parsed_keys.get("year".upper(), None)
        year = "" if year is None else entry.get(year, None)
        month = entry_parsed_keys.get("month".upper(), None)
        month = "" if month is None else entry.get(month, None)
        note = entry_parsed_keys.get("note".upper(), None)
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = entry_parsed_keys.get("address".upper(), None)
        address = "" if address is None else entry.get(address, None)
        type = entry_parsed_keys.get("type".upper(), None)
        type = "" if type is None else entry.get(type, None)
        type = process_special_character(type)
        if author is None or title is None or school is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="MASTERSTHESIS", author=author, editor=None, title=title, journal=None,
                           year=year,
                           volume=None, number=None, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=school, type=type, how_published=None, keywords=None, institution=None)
    elif entry_type == "TECHREPORT":
        author = get_value_by_key(entry_parsed_keys, "author".upper())
        author = "" if author is None else entry.get(author, None)
        author = process_special_character(author)
        title = get_value_by_key(entry_parsed_keys, "title".upper())
        title = "" if title is None else entry.get(title, None)
        title = process_special_character(title)
        institution = get_value_by_key(entry_parsed_keys, "institution".upper())
        institution = "" if institution is None else entry.get(institution, None)
        institution = process_special_character(institution)
        year = get_value_by_key(entry_parsed_keys, "year".upper())
        year = "" if year is None else entry.get(year, None)
        month = get_value_by_key(entry_parsed_keys, "month".upper())
        month = "" if month is None else entry.get(month, None)
        note = get_value_by_key(entry_parsed_keys, "note".upper())
        note = "" if note is None else entry.get(note, None)
        note = process_special_character(note)
        address = get_value_by_key(entry_parsed_keys, "address".upper())
        address = "" if address is None else entry.get(address, None)
        number = get_value_by_key(entry_parsed_keys, "number".upper())
        number = "" if number is None else entry.get(number, None)
        report_type = get_value_by_key(entry_parsed_keys, "type".upper())
        report_type = "" if report_type is None else entry.get(report_type, None)
        if author is None or title is None or institution is None or year is None:
            print("publication without mandatory fields: " + str(entry))
            return None
        node = Publication(uuid="", node_type="TECHREPORT", author=author, editor=None, title=title, journal=None,
                           year=year,
                           volume=None, number=number, series=None, address=address, pages=None, month=month,
                           note=note, publisher=None, edition=None, book_title=None, organization=None,
                           chapter=None, school=None, type=report_type, how_published=None, keywords=None,
                           institution=institution)
    else:
        print("unsupported entry (type):" + str(entry))
        return None
    return node


def extract_venue(entry):
    """
    从节点信息中，提取出venue节点
    :param entry:
    :return:
    """
    entry_parsed_keys = upperize_dict_keys(entry)
    # venue name
    venue_name = get_value_by_key(entry_parsed_keys, "venue_name".upper())
    venue_name = "" if venue_name is None else entry.get(venue_name, None)
    venue_name = process_special_character(venue_name)  # 包括了转大写、去除空格、转换特殊字符等操作
    # abbr
    abbr = get_value_by_key(entry_parsed_keys, "abbr".upper())
    abbr = "" if abbr is None else entry.get(abbr, None)
    abbr = process_special_character(abbr)  # 包括了转大写、去除空格、转换特殊字符等操作
    # venue type
    venue_type = get_value_by_key(entry_parsed_keys, "venue_type".upper())
    venue_type = "" if venue_type is None else entry.get(venue_type, None)
    venue_type = process_special_character(venue_type)
    # publisher
    publisher = get_value_by_key(entry_parsed_keys, "publisher".upper())
    publisher = "" if publisher is None else entry.get(publisher, None)
    publisher = process_special_character(publisher)
    # address
    address = get_value_by_key(entry_parsed_keys, "address".upper())
    address = "" if address is None else entry.get(address, None)
    address = process_special_character(address)
    # sci_index
    sci_index = get_value_by_key(entry_parsed_keys, "sci_index".upper())
    sci_index = "" if sci_index is None else entry.get(sci_index, None)
    # ei_index
    ei_index = get_value_by_key(entry_parsed_keys, "ei_index".upper())
    ei_index = "" if ei_index is None else entry.get(ei_index, None)
    # ssci_index
    ssci_index = get_value_by_key(entry_parsed_keys, "ssci_index".upper())
    ssci_index = "" if ssci_index is None else entry.get(ssci_index, None)
    # start year
    start_year = get_value_by_key(entry_parsed_keys, "start_year".upper())
    start_year = "" if start_year is None else entry.get(start_year, None)
    # year
    year = get_value_by_key(entry_parsed_keys, "year".upper())
    year = "" if year is None else entry.get(year, None)
    # note
    note = get_value_by_key(entry_parsed_keys, "note".upper())
    note = "" if note is None else entry.get(note, None)
    note = process_special_character(note)
    if venue_name is "" or venue_type is "":
        print("No valid node! venue name and venue type are mandatory fields: " + str(entry))
        return None
    node = Venue(uuid="", venue_name=venue_name, abbr=abbr, venue_type=venue_type, publisher=publisher, year=year,
                 address=address, sci_index=sci_index, ei_index=ei_index, ssci_index=ssci_index, note=note,
                 start_year=start_year)
    return node


def extract_person(entry):
    """
    从节点信息中，提取出Person节点
    :param entry:
    :return:
    """
    entry_parsed_keys = upperize_dict_keys(entry)
    # full name
    full_name = get_value_by_key(entry_parsed_keys, "full_name".upper())
    full_name = "" if full_name is None else entry.get(full_name, None)
    full_name = process_special_character(full_name)  # 包括了转大写、去除空格、转换特殊字符等操作
    # last_name
    last_name = get_value_by_key(entry_parsed_keys, "last_name".upper())
    last_name = "" if last_name is None else entry.get(last_name, None)
    last_name = process_special_character(last_name)  # 包括了转大写、去除空格、转换特殊字符等操作
    # middle_name
    middle_name = get_value_by_key(entry_parsed_keys, "middle_name".upper())
    middle_name = "" if middle_name is None else entry.get(middle_name, None)
    middle_name = process_special_character(middle_name)
    # first_name
    first_name = get_value_by_key(entry_parsed_keys, "first_name".upper())
    first_name = "" if first_name is None else entry.get(first_name, None)
    first_name = process_special_character(first_name)
    # name_ch
    name_ch = get_value_by_key(entry_parsed_keys, "name_ch".upper())
    name_ch = "" if name_ch is None else entry.get(name_ch, None)
    name_ch = process_special_character(name_ch)
    # first_name_ch
    first_name_ch = get_value_by_key(entry_parsed_keys, "first_name_ch".upper())
    first_name_ch = "" if first_name_ch is None else entry.get(first_name_ch, None)
    first_name_ch = process_special_character(first_name_ch)
    # last_name_ch
    last_name_ch = get_value_by_key(entry_parsed_keys, "last_name_ch".upper())
    last_name_ch = "" if last_name_ch is None else entry.get(last_name_ch, None)
    last_name_ch = process_special_character(last_name_ch)
    # research_interest
    research_interest = get_value_by_key(entry_parsed_keys, "research_interest".upper())
    research_interest = "" if research_interest is None else entry.get(research_interest, None)
    research_interest = process_special_character(research_interest)
    # institution
    institution = get_value_by_key(entry_parsed_keys, "institution".upper())
    institution = "" if institution is None else entry.get(institution, None)
    institution = process_special_character(institution)
    # added_by
    added_by = get_value_by_key(entry_parsed_keys, "added_by".upper())
    added_by = "" if added_by is None else entry.get(added_by, None)
    added_by = process_special_character(added_by)
    # added_date
    added_date = get_value_by_key(entry_parsed_keys, "added_date".upper())
    added_date = "" if added_date is None else entry.get(added_date, None)
    # note
    note = get_value_by_key(entry_parsed_keys, "note".upper())
    note = "" if note is None else entry.get(note, None)
    note = process_special_character(note)
    if full_name is "" and name_ch is "":
        print("No valid node! full name or name_ch is mandatory fields: " + str(entry))
        return None
    node = Person(uuid="", full_name=full_name, first_name=first_name, middle_name=middle_name, last_name=last_name,
                  name_ch=name_ch,
                  first_name_ch=first_name_ch, last_name_ch=last_name_ch, institution=institution,
                  research_interest=research_interest, note=note,
                  added_by=added_by, added_date=added_date)
    return node


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