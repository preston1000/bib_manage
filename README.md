# bib_manage

接口字段说明：
1. 高级搜索后台接收并能处理的字段包括：
    title, node_type, page, limit,
    startTime, endTime, author, paperIndex,
2. 高级搜索后台查询后"返回"的数据包括以下字段：见（views.search_publication_new）
    data, code, count, msg
    其中data包括的字段有：(见query_data.query_pub_by_multiple_field)
    ID(views.search_publication_new新增), pages(views.search_publication_new中将原有的pages1和pages2整合在一起),
    paperTypeEdit, title, booktitle, author, editor, keywords,
    edition, year, month, journal, volume, type, chapter, number, publisher, organization, institution, school, address,
    series, howpublished, indexing, uuid, note, id
3.
