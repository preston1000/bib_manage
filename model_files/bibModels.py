"""
此文件是定义Neo4j中节点类型的，包括publication、venue、person三类节点
"""

from utils.nlp.text_utils import capitalize_dict_keys


class Publication:
    # 共24个，从文献信息中提取出
    node_type = None  # 文献类型
    id = None
    author = None  # 作者
    editor = None  # 编辑
    title = None  # 标题
    journal = None  # 所在期刊名
    publisher = None  # 出版公司
    year = None  # 发表年  数值
    volume = None  # 期
    number = None  # 卷
    pages = None  # 页码
    month = None  # 发表月
    note = None  # 笔记
    series = None  # 系列
    address = None  # 地址
    edition = None  # 书籍版号
    chapter = None  # 章节
    book_title = None  # 所在书籍标题
    organization = None  # 组织
    how_published = None  #
    school = None  # 学校
    keywords = None  # 关键词
    type = None  # 类型
    institution = None  # 组织

    # 7个需要用户指定的新字段
    abstract = None  # 摘要
    note_id = None  # 笔记编号
    ei_index = None  # 是否EI检索
    sci_index = None  # 是否SCI检索
    ssci_index = None  # 是否SSCI检索
    added_by = None  # 节点创建人
    modified_date = None  # 文献阅读时间

    # 2个系统自动生成字段
    uuid = None  # uuid
    added_date = None  # 节点创建时间

    def __init__(self, uuid, node_type, author=None, editor=None, title=None, journal=None, year=None,
                 volume=None, number=None, series=None, address=None, pages=None, month=None,
                 note=None, publisher=None, edition=None, book_title=None, organization=None,
                 chapter=None, school=None, type=None, how_published=None, keywords=None, abstract=None, note_id=None,
                 institution=None, added_by=None, added_date=None, sci_index=None, ei_index=None, ssci_index=None,
                 modified_date=None, id=None):
        self.uuid = uuid
        self.id = id
        self.node_type = node_type
        self.author = author
        self.editor = editor
        self.title = title
        self.journal = journal
        if not isinstance(year, int):
            year = int(year)
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
        self.abstract = abstract
        self.note_id = note_id
        self.institution = institution
        self.added_date = added_date
        self.added_by = added_by
        self.ei_index = ei_index
        self.sci_index = sci_index
        self.ssci_index = ssci_index
        self.modified_date = modified_date

    def to_string(self):
        word = "{uuid:'" + ("" if self.uuid is None or self.uuid == "" else self.uuid.hex) + "'," + \
               "node_type:'" + ("" if self.node_type is None else self.node_type) + "'," + \
               "id:'" + ("" if self.id is None else self.id) + "'," + \
               "author:'" + ("" if self.author is None else self.author) + "'," + \
               "editor:'" + ("" if self.editor is None else self.editor) + "'," + \
               "title:'" + ("" if self.title is None else self.title) + "'," + \
               "journal:'" + ("" if self.journal is None else self.journal) + "'," + \
               "year:" + ("" if self.year is None else str(self.year)) + "," + \
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
               "abstract:'" + ("" if self.abstract is None else self.abstract) + "'," + \
               "note_id:'" + ("" if self.note_id is None else self.note_id) + "'," + \
               "added_date:'" + ("" if self.added_date is None else self.added_date) + "'," + \
               "modified_date:'" + ("" if self.modified_date is None else self.modified_date) + "'," + \
               "added_by:'" + ("" if self.added_by is None else self.added_by) + "'," + \
               "ei_index:'" + ("" if self.ei_index is None else self.ei_index) + "'," + \
               "sci_index:'" + ("" if self.sci_index is None else self.sci_index) + "'," + \
               "ssci_index:'" + ("" if self.ssci_index is None else self.ssci_index) + "'," + \
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
        cypher = "CREATE (node:PUBLICATION " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self):  # todo 可选fields
        cypher = "MATCH (node:PUBLICATION {id:'" + self.id + "', "
        try:
            if self.node_type is None:
                print("unrecognized entry (type):" + self.to_string())
                return None
            elif self.node_type == "ARTICLE":
                cypher += "title:'" + self.title + \
                         "', journal:'" + self.journal + "', year:" + str(self.year) + "})"
            elif self.node_type == "BOOK":
                cypher += "title:'" + self.title + \
                         "',publisher:'" + self.publisher + "', year:" + str(self.year) + "})"
            elif self.node_type == "INBOOK":
                cypher += "year:" + str(self.year) + ", title:'" + self.title + \
                          "', chapter:'" + self.chapter + "', pages:'" + self.pages + "'})"
            elif self.node_type == "INPROCEEDINGS" or self.node_type == "CONFERENCE":
                cypher += "title:'" + self.title + \
                         "', book_title:'" + self.book_title + "', year:" + str(self.year) + "})"
            elif self.node_type == "INCOLLECTION":
                cypher += "title:'" + self.title + "', book_title:'" + self.book_title + \
                          "', year:" + str(self.year) + ", publisher:'" + self.publisher + "'})"
            elif self.node_type == "MISC":
                cypher += "title:'" + self.title + "'})"
            elif self.node_type == "PHDTHESIS":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', school:'" + self.school + "', year:" + str(self.year) + "})"
            elif self.node_type == "MASTERSTHESIS":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', school:'" + self.school + "', year:" + str(self.year) + "})"
            elif self.node_type == "TECHREPORT":
                cypher += "author:'" + self.author + "', title:'" + self.title + \
                         "', institution:'" + self.institution + "', year:" + str(self.year) + "})"
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
        cypher = "MATCH (node:PUBLICATION {"
        for field, value in field_value_match.items():
            cypher += field + ":'" + str(value) + "',"
        cypher = cypher[:-1] + "}) set " + self.to_string_for_modification("node", field_value_revise) + " return node"
        return cypher


class Venue:
    # todo Venue和Person类还要加一个类似Publication的id的属性
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
               "year:'" + ("" if self.year is None else str(self.year)) + "'," + \
               "address:'" + ("" if self.address is None else self.address) + "'," + \
               "note:'" + ("" if self.note is None else self.note) + "'," + \
               "publisher:'" + ("" if self.publisher is None else self.publisher) + "'," + \
               "ei_index:'" + ("" if self.ei_index is None else self.ei_index) + "'," + \
               "sci_index:'" + ("" if self.sci_index is None else self.sci_index) + "'," + \
               "added_date:'" + ("" if self.added_date is None else self.added_date) + "'," + \
               "added_by:'" + ("" if self.added_by is None else self.added_by) + "'," + \
               "ssci_index:'" + ("" if self.ssci_index is None else self.ssci_index) + "'}"
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
        cypher = "CREATE (node:VENUE " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self):
        cypher = "MATCH (node:VENUE { venue_name:'" + self.venue_name + "'})  return node"
        return cypher

    def get_revise_cypher(self, field_value_revise, field_value_match):
        if field_value_match is None or not isinstance(field_value_match, dict) or not isinstance(field_value_revise, dict):
            return ""
        cypher = "MATCH (node:VENUE {"
        for field, value in field_value_match.items():
            cypher += field + ":'" + str(value) + "',"
        cypher = cypher[:-1] + "}) set " + self.to_string_for_modification("node", field_value_revise) + " return node"
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
    institution = None
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
        self.institution = institution
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
               "institution:'" + ("" if self.institution is None else self.institution) + "'," + \
               "note:'" + ("" if self.note is None else self.note) + "'," + \
               "added_by:'" + ("" if self.added_by is None else self.added_by) + "'," + \
               "added_date:'" + ("" if self.institution is None else self.added_date) + "'," + \
               "research_interest:'" + ("" if self.research_interest is None else self.research_interest) + "'}"
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
        cypher = "CREATE (node:PERSON " + self.to_string() + ") return node"
        return cypher

    def get_match_cypher(self, field="full_name"):
        if field == "full_name":
            cypher = "MATCH (node:PERSON {" + field + ":'" + self.full_name + "'}) return node"
        elif field == "name_ch":
            cypher = "MATCH (node:PERSON {" + field + ":'" + self.name_ch + "'}) return node"
        return cypher

    def get_revise_cypher(self, field_value_revise, field_value_match):
        if field_value_match is None or not isinstance(field_value_match, dict) or not isinstance(field_value_revise, dict):
            return ""
        cypher = "MATCH (node:PERSON {"
        for field, value in field_value_match.items():
            cypher += field + ":'" + str(value) + "',"
        cypher = cypher[:-1] + "}) set " + self.to_string_for_modification("node", field_value_revise) + " return node"
        return cypher


class Pub:
    entry_type = None  # 1.文献类型
    title = None  # 标题
    book_title = None  # 所在书籍标题
    editor = None  # 编辑
    keywords = None  # 关键词
    edition = None  # 6.书籍版号
    author = None  # 作者
    year = None  # 发表年
    month = None  # 发表月
    journal = None  # 所在期刊名
    volume = None  # 11.期
    type = None  # 类型
    chapter = None  # 章节
    number = None  # 卷
    pages = None  # 页码
    publisher = None  # 16. 出版公司
    organization = None  # 组织
    institution = None  # 组织
    school = None  # 学校
    address = None  # 地址
    series = None  # 21 系列
    how_published = None  #
    note = None  # 笔记

    abstract = None  # 摘要
    note_id = None  # 笔记编号
    modified_date = None  # 26. 文献阅读时间

    def create_node(self, info):
        if info is None or not isinstance(info, dict):
            return
        info = capitalize_dict_keys(info)

        entry_type = info.get("ENTRYTYPE", None)
        self.entry_type = entry_type.upper() if entry_type is not None else None
        title = info.get("title".upper(), None)
        self.title = title.upper() if title is not None else None
        book_title = info.get("book_title".upper(), None)
        self.book_title = book_title.upper() if book_title is not None else None
        editor = info.get("editor".upper(), None)
        self.editor = editor.upper() if editor is not None else None
        keywords = info.get("keywords".upper(), None)
        self.keywords = keywords.upper() if keywords is not None else None
        edition = info.get("edition".upper(), None)
        self.edition = edition.upper() if edition is not None else None
        author = info.get("author".upper(), None)
        self.author = author.upper() if author is not None else None
        self.year = info.get("year", None)
        month = info.get("month".upper(), None)
        self.month = month.upper() if month is not None else None
        journal = info.get("journal".upper(), None)
        self.journal = journal.upper() if journal is not None else None
        volume = info.get("volume".upper(), None)
        self.volume = volume.upper() if volume is not None else None
        type = info.get("type".upper(), None)
        self.type = type.upper() if type is not None else None
        chapter = info.get("chapter".upper(), None)
        self.chapter = chapter.upper() if chapter is not None else None
        number = info.get("number".upper(), None)
        self.number = number.upper() if number is not None else None
        pages = info.get("pages".upper(), None)
        self.pages = pages.upper() if pages is not None else None
        publisher = info.get("publisher".upper(), None)
        self.publisher = publisher.upper() if publisher is not None else None
        organization = info.get("organization".upper(), None)
        self.organization = organization.upper() if organization is not None else None
        institution = info.get("institution".upper(), None)
        self.institution = institution.upper() if institution is not None else None
        school = info.get("school".upper(), None)
        self.school = school.upper() if school is not None else None
        address = info.get("address".upper(), None)
        self.address = address.upper() if address is not None else None
        series = info.get("series".upper(), None)
        self.series = series.upper() if series is not None else None
        how_published = info.get("how_published".upper(), None)
        self.how_published = how_published.upper() if how_published is not None else None
        note = info.get("note".upper(), None)
        self.note = note.upper() if note is not None else None

    def to_dict(self):
        mapping = {"entry_type", self.entry_type,
                   "title", self.title,
                   "book_title", self.book_title,
                   "editor", self.editor,
                   "keywords", self.keywords,
                   "edition", self.edition,
                   "author", self.author,
                   "year", self.year,
                   "month", self.month,
                   "journal", self.journal,
                   "volume", self.volume,
                   "type", self.type,
                   "chapter", self.chapter,
                   "number", self.number,
                   "pages", self.pages,
                   "publisher", self.publisher,
                   "organization", self.organization,
                   "institution", self.institution,
                   "school", self.school,
                   "address", self.address,
                   "series", self.series,
                   "how_published", self.how_published,
                   "note", self.note,

                   "abstract", self.abstract,
                   "note_id", self.note_id,
                   "modified_date", self.modified_date}
        return mapping
