"""
为d_extraction重构后的临时文件
"""
from utils.models import Venue, Person
from utils.util_operation import get_value_by_key
from utils.util_operation_2 import upperize_dict_keys
from utils.util_text_operation import process_special_character


def extract_venue(entry):
    """
    从节点信息中，提取出venue节点 todo 还没改
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
    从节点信息中，提取出person节点 todo 还没改
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
    node = Person(uuid="", full_name=full_name, first_name=first_name, middle_name=middle_name, last_name=last_name, name_ch=name_ch,
                  first_name_ch=first_name_ch, last_name_ch=last_name_ch, institution=institution, research_interest=research_interest, note=note,
                  added_by=added_by, added_date=added_date)
    return node
