# bib_manage

接口字段说明：
1. 高级搜索后台接收并能处理的字段包括：
    对PUBLICATION：title, node_type, page, limit,（startTime, endTime, author, paperIndex未实现）
    对Venue: venue_name
2. 高级搜索后台查询后"返回"的数据包括以下字段：见（views.search_publication_new）/search/result/
    data, code, count, msg
    其中data包括的字段有：(见query_data.query_pub_by_multiple_field)
    ID(views.search_publication_new新增), pages(views.search_publication_new中将原有的pages1和pages2整合在一起),
    paperTypeEdit, title, booktitle, author, editor, keywords,
    edition, year, month, journal, volume, type, chapter, number, publisher, organization, institution, school, address,
    series, howpublished, indexing, uuid, note, pages1, pages2
    其中code的含义：
    -3：没有提供/未解析出搜索条件；   -2：提供的数据不是json格式；   -4：接口请求方式错误，非post
    兼容（query_pub_by_multiple_field同query_by_multiple_field）中的错误码：
        -1：未有有效的筛选条件；       0：无记录；      1： 有一条记录；       2：有多条记录
3. 页面文献表单中的字段名称：manage.html
    1) paperTypeEdit, title, booktitle, editor, keywords, edition, year, journal, volume, type, chapter, number,
    publisher, organization,institution, school, address, series, howpublished, indexing, note,pages1, pages2
    2) author, pubMonth
4. 页面venue表单中字段名称+table字段(括号中5个+ID--数字编号1开始):manage.html
    note, startYear, scope,( address, publisher, type, name,website, )
5. 数据库中数据字段（venue）:
    note, address, added_date, year, start_year, ei_index, ssci_index, uuid, sci_index,
    added_by, venue_type, publisher,venue_name
6. 后台创建Publication节点接收字段（/add-pub/， views.add_publication）
    ENTRYTYPE（为前台form中的数字，后续要改为前台处理）, author(接收的可以是：str或dict，其中包括first_name, middle_name, last_name)
    to_create(若无记录，是否创建节点),return_type(返回值类型，dict或class）

7. 后台创建Publication节点返回信息（views.add_publication）
    data, code, count, msg
    其中data包括的字段有：
    其中code的含义：
    -3：接口没有参数数据；    -4：接口参数不是json，  -5：不支持的文献类型     -6:查询数据接口无返回值；  -7：请求方式非post
    （兼容create_or_match_publications的错误码,见第9项）

8. 从bib或Excel解析出的数据字段包括：
    ENTRYTYPE， ID,
    author,editor, title,journal,publisher , year, volume,number,pages ,month, note ,series, address,edition ,
    chapter, type, booktitle, organization, howpublished, school, keywords, type, institution

9. create_or_match_nodes的返回数据（创建/查询节点，由Publication/VENUE、PERSON类数据生成）
    code, msg, data
    其中code包括：
        -1：文献数据无效；  -2：数据库信息无效；  0：未查询到或未创建任何节点；    2：不是所有节点都写进数据库；
        1：全部节点都写进数据库了
    data包括：
        uuid
10. create_or_match_nodes的输入数据：
    当Publication时：与extract_publication（即第8项内容）的字段相同，

11. 根据文献的必填字段查找数据库---用add_publication
    前台表单中的所有字段（见第3项）
