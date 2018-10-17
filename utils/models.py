class Publication:
    author = None
    editor = None
    title = None
    journal = None
    year = None
    volume = None
    number = None
    series = None
    address = None
    pages = None
    month = None
    note = None
    publisher = None
    edition = None
    book_title = None
    organization = None
    chapter = None
    school = None
    type = None
    how_published = None
    keywords = None
    institution = None
    node_type = None
    uuid = None
    added_by = None  # 节点创建人
    added_date = None  # 节点创建时间

    def __init__(self, uuid, node_type, author=None, editor=None, title=None, journal=None, year=None,
                 volume=None, number=None, series=None, address=None, pages=None, month=None,
                 note=None, publisher=None, edition=None, book_title=None, organization=None,
                 chapter=None, school=None, type=None, how_published=None, keywords=None,
                 institution=None, added_by=None, added_date=None):
        self.uuid = uuid
        self.node_type = node_type
        self.author = author
        self.editor = editor
        self.title = title
        self.journal = journal
        self.year = year
        self.volume = volume
        self.number = number
        self.series = series
        self.address = address
        self.pages = pages
        self.month = month
        self.note = note
        self.publisher = publisher
        self.edition = edition
        self.book_title = book_title
        self.organization = organization
        self.chapter = chapter
        self.school = school
        self.type = type
        self.how_published = how_published
        self.keywords = keywords
        self.institution = institution
        self.added_date = added_date
        self.added_by = added_by

    def to_string(self):
        word = "{uuid:'" + ("" if self.uuid is None else self.uuid.hex) + "'," + \
               "node_type:'" + ("" if self.node_type is None else self.node_type) + "'," + \
               "author:'" + ("" if self.author is None else self.author) + "'," + \
               "editor:'" + ("" if self.editor is None else self.editor) + "'," + \
               "title:'" + ("" if self.title is None else self.title) + "'," + \
               "journal:'" + ("" if self.journal is None else self.journal) + "'," + \
               "year:'" + ("" if self.year is None else self.year) + "'," + \
               "volume:'" + ("" if self.volume is None else self.volume) + "'," + \
               "number:'" + ("" if self.number is None else self.number) + "'," + \
               "series:'" + ("" if self.series is None else self.series) + "'," + \
               "address:'" + ("" if self.address is None else self.address) + "'," + \
               "pages:'" + ("" if self.pages is None else self.pages) + "'," + \
               "month:'" + ("" if self.month is None else self.month) + "'," + \
               "note:'" + ("" if self.note is None else self.note) + "'," + \
               "publisher:'" + ("" if self.publisher is None else self.publisher) + "'," + \
               "edition:'" + ("" if self.edition is None else self.edition) + "'," + \
               "book_title:'" + ("" if self.book_title is None else self.book_title) + "'," + \
               "organization:'" + ("" if self.organization is None else self.organization) + "'," + \
               "chapter:'" + ("" if self.chapter is None else self.chapter) + "'," + \
               "school:'" + ("" if self.school is None else self.school) + "'," + \
               "type:'" + ("" if self.type is None else self.type) + "'," + \
               "how_published:'" + ("" if self.how_published is None else self.how_published) + "'," + \
               "keywords:'" + ("" if self.keywords is None else self.keywords) + "'," + \
               "added_date:'" + ("" if self.added_date is None else self.added_date) + "'," + \
               "added_by:'" + ("" if self.added_by is None else self.added_by) + "'," + \
               "institution:'" + ("" if self.institution is None else self.institution) + "'}"
        return word

    def to_string_for_modification(self, node_identifier, field_value):
        """
        修改字段时，需要的where后字符串
        :param node_identifier: cypher中，(n:Publication)中的n
        :param field_value: 要修改的field name 和value
        :return: string
        """
        if node_identifier is None or node_identifier == "" or not isinstance(field_value, dict):
            return ""
        word = ""
        for field, value in field_value.items():
            if value is None or value == '':
                value = ""
            word += node_identifier + "." + field + "='" + value + "',"
        word = word[:-1]
        return word

    def get_create_cypher(self):
        cypher = "CREATE (node:Publication " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self):
        cypher = "MATCH (node:Publication {"
        try:
            if self.node_type is None:
                print("unrecognized entry (type):" + self.to_string())
                return None
            elif self.node_type == "ARTICLE":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', journal:'" + self.journal + "', year:'" + self.year + "'})"
            elif self.node_type == "BOOK":
                if self.author is not None:
                    cypher += "author:'" + self.author + "', title:'" + self.title + \
                             "',publisher:'" + self.publisher + "', year:'" + self.year + "'})"
                elif self.editor is not None:
                    cypher += "editor:'" + self.editor + "', title:'" + self.title + \
                             "',publisher:'" + self.publisher + "', year:'" + self.year + "'})"
                else:
                    return None
            elif self.node_type == "INBOOK":
                if self.author is not None:
                    cypher += "author:'" + self.author + "', title:'" + self.title + \
                              "', year:'" + self.year
                elif self.editor is not None:
                    cypher += "editor:'" + self.editor + "', title:'" + self.title + \
                              "', year:'" + self.year
                else:
                    return None

                if self.chapter is not None:
                    cypher += "', chapter:'" + self.chapter + "'})"
                elif self.pages is not None:
                    cypher += "', pages:'" + self.pages + "'})"
                else:
                    return None
            elif self.node_type == "INPROCEEDINGS" or self.node_type == "CONFERENCE":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', book_title:'" + self.book_title + "', year:'" + self.year + "'})"
            elif self.node_type == "INCOLLECTION":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', book_title:'" + self.book_title + "', year:'" + self.year + "', publisher:'" + \
                          self.publisher + "'})"
            elif self.node_type == "MISC":
                if self.title is not None:
                    cypher += "title:'" + self.title + "'})"
                else:
                    return -1
            elif self.node_type == "PHDTHESIS":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', school:'" + self.school + "', year:'" + self.year + "'})"
            elif self.node_type == "MASTERSTHESIS":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', school:'" + self.school + "', year:'" + self.year + "'})"
            elif self.node_type == "TECHREPORT":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', institution:'" + self.institution + "', year:'" + self.year + "'})"
            else:
                print("unsupported entry (type):" + self.to_string())
                return None
        except:
            print("failed when generating match cypher: " + self.to_string())
            return None
        cypher += " return node"
        return cypher

    def get_revise_cypher(self, field_value_revise, field_value_match):
        if field_value_match is None or not isinstance(field_value_match, dict) or not isinstance(field_value_revise, dict):
            return ""
        cypher = "CREATE (node:Publication {"
        for field, value in field_value_match.items():
            cypher += field + ":'" + str(value) + "',"
        cypher = cypher[:-1] + "}) set " + self.to_string_for_modification("node", field_value_revise) + " return node"
        return cypher


class Venue:
    uuid = None
    venue_type = None  # 会议、期刊
    venue_name = None  # 名称
    abbr = None  # 简称
    start_year = None  # 创刊年、第一届会议年
    year = None  # 会议年
    address = None  # 会议地址、期刊地址
    note = None  # 注释
    publisher = None  # 会议主办者、期刊出版社
    ei_index = None  # 是否EI检索
    sci_index = None  # 是否SCI检索
    ssci_index = None  # 是否SSCI检索
    added_by = None  # 节点创建人
    added_date = None  # 节点创建时间

    def __init__(self, uuid, venue_type, venue_name, abbr=None, start_year=None, year=None,
                 address=None, note=None, publisher=None, ei_index=None, sci_index=None, ssci_index=None):
        self.uuid = uuid
        self.venue_type = venue_type
        self.venue_name = venue_name
        self.abbr = abbr
        self.start_year = start_year
        self.year = year
        self.address = address
        self.note = note
        self.publisher = publisher
        self.ei_index = ei_index
        self.sci_index = sci_index
        self.ssci_index = ssci_index

    def to_string(self):
        word = "{uuid:'" + ("" if self.uuid is None else self.uuid.hex) + "'," + \
               "venue_type:'" + ("" if self.venue_type is None else self.venue_type) + "'," + \
               "venue_name:'" + ("" if self.venue_name is None else self.venue_name) + "'," + \
               "abbr:'" + ("" if self.abbr is None else self.abbr) + "'," + \
               "start_year:'" + ("" if self.start_year is None else self.start_year) + "'," + \
               "year:'" + ("" if self.year is None else self.year) + "'," + \
               "address:'" + ("" if self.address is None else self.address) + "'," + \
               "note:'" + ("" if self.note is None else self.note) + "'," + \
               "publisher:'" + ("" if self.publisher is None else self.publisher) + "'," + \
               "ei_index:'" + ("" if self.ei_index is None else self.ei_index) + "'," + \
               "sci_index:'" + ("" if self.sci_index is None else self.sci_index) + "'," + \
               "added_date:'" + ("" if self.added_date is None else self.added_date) + "'," + \
               "added_by:'" + ("" if self.added_by is None else self.added_by) + "'," + \
               "ssci_index:'" + ("" if self.ssci_index is None else self.ssci_index) + "'}"
        return word

    def get_create_cypher(self):
        cypher = "CREATE (node:Venue " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self):
        cypher = "MATCH (node:Venue { venue_name:'" + self.venue_name + "'})  return node"
        return cypher


class Person:
    """
    name是first_name middle_name last_name格式
    """
    full_name = None
    first_name = None
    middle_name = None
    last_name = None
    name_ch = None
    first_name_ch = None
    last_name_ch = None
    affiliation = None
    research_interest = None
    note = None
    added_by = None  # 节点创建人
    added_date = None  # 节点创建时间
    uuid = None

    def __init__(self, uuid, full_name=None, first_name=None, middle_name=None, last_name=None, name_ch=None,
                 first_name_ch=None, last_name_ch=None, institution=None, research_interest=None, note=None,
                 added_by=None, added_date=None):
        self.uuid = uuid
        self.first_name = first_name
        self.middle_name = middle_name
        self.last_name = last_name
        self.full_name = full_name
        self.name_ch = name_ch
        self.last_name_ch = last_name_ch
        self.first_name_ch = first_name_ch
        self.affiliation = institution
        self.research_interest = research_interest
        self.note = note
        self.added_by = added_by
        self.added_date = added_date

    def to_string(self):
        word = "{uuid:'" + ("" if self.uuid is None else self.uuid.hex) + "'," + \
               "full_name:'" + ("" if self.full_name is None else self.full_name) + "'," + \
               "first_name:'" + ("" if self.first_name is None else self.first_name) + "'," + \
               "middle_name:'" + ("" if self.middle_name is None else self.middle_name) + "'," + \
               "last_name:'" + ("" if self.last_name is None else self.last_name) + "'," + \
               "name_ch:'" + ("" if self.name_ch is None else self.name_ch) + "'," + \
               "first_name_ch:'" + ("" if self.first_name_ch is None else self.first_name_ch) + "'," + \
               "last_name_ch:'" + ("" if self.last_name_ch is None else self.last_name_ch) + "'," + \
               "affiliation:'" + ("" if self.affiliation is None else self.affiliation) + "'," + \
               "note:'" + ("" if self.note is None else self.note) + "'," + \
               "added_by:'" + ("" if self.added_by is None else self.added_by) + "'," + \
               "added_date:'" + ("" if self.affiliation is None else self.added_date) + "'," + \
               "research_interest:'" + ("" if self.research_interest is None else self.research_interest) + "'}"
        return word

    def get_create_cypher(self):
        cypher = "CREATE (node:Person " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self, field="full_name"):
        if field == "full_name":
            cypher = "MATCH (node:Person {" + field + ":'" + self.full_name + "'}) return node"
        elif field == "name_ch":
            cypher = "MATCH (node:Person {" + field + ":'" + self.name_ch + "'}) return node"
        return cypher