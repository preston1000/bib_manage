
function setEditNodePanel(obj, nodeType, siteUrl, splitNameService, formSettings, contentStringName, enhanceForm){
    var $ = layui.$;
    var data = layui.table.checkStatus(obj.config.id).data;//获取被选节点的内容
    if (data.length < 1){
        layui.layer.msg("未选择项目！", {
            time: 5000, //5s后自动关闭
            btn: ['ok'],
            icon:5
        });
    }else{
        selectedInfo = data[0];
        if (nodeType == "Publication"){
            var panelDivID = "editPub"
                ,panelFormID = 'editPubForm'
                ,authorTableID = 'authorTableEdit';
            $('#' + panelDivID).attr('class', 'collapse in');//显示 编辑节点信息的表单
            //表格2）编辑文献表格中作者信息表格
            layui.table.render({
                elem: '#authorTableEdit'
                ,url: '/demo/table/user/'
                ,cols: [[
                  {field:'firstName', title:'名', width:100, edit: 'text'}
                  ,{field:'middleName', title:'中间名', width:100, edit: 'text'}
                  ,{field:'lastName', title:'姓', width:100, edit: 'text'}
                  ,{field:'ranking', title:'排名', width:100, sort: true}
                  ,{width:150, align:'center', toolbar: '#authorBarsAdd'}
                ]]
                ,id: 'authorTableEdit'
                ,page: false
                ,done: function(res, curr, count){
                    currentAuthors = deepClone(res["data"]);
                }
            });
            currentAuthors = processPubPanel(selectedInfo, formSettings, contentStringName, panelDivID, panelFormID, authorTableID, siteUrl, splitNameService, enhanceForm);
        }else if (nodeType == "Person"){
            var panelDivID = "editPerson"
                ,panelFormID = 'editPersonForm';
            $('#' + panelDivID).attr('class', 'collapse in');//显示 编辑节点信息的表单
            processPersonPanel(selectedInfo, panelFormID, enhanceForm);
        }else if (nodeType == "Venue") {
            var panelDivID = "editVenue"
                ,panelFormID = 'editVenueForm';
            $('#' + panelDivID).attr('class', 'collapse in');//显示 编辑节点信息的表单
            processVenuePanel(selectedInfo, panelFormID, enhanceForm);
        }
    }
    return currentAuthors;
}
function processPubPanel(selectedPubInfo, formSettings, contentStringName, panelDivID, panelFormID, authorTableID, siteUrl, splitNameService, enhanceForm){
    var $ = layui.$;
    //先决定显示的字段都有哪些
    var value = selectedPubInfo.paperTypeEdit;
    if (value == 'Book'.toUpperCase()){
        value = 1;
    }else if (value == 'Booklet'.toUpperCase()){
        value = 2;
    }else if (value == 'Conference'.toUpperCase()){
        value = 3;
    }else if (value == 'InBook'.toUpperCase()){
        value = 4;
    }else if (value == 'InCollection'.toUpperCase()){
        value = 5;
    }else if (value == 'InProceedings'.toUpperCase()){
        value = 6;
    }else if (value == 'Manual'.toUpperCase()){
        value = 7;
    }else if (value == 'MastersThesis'.toUpperCase()){
        value = 8;
    }else if (value == 'Misc'.toUpperCase()){
        value = 9;
    }else if (value == 'PhDThesis'.toUpperCase()){
        value = 10;
    }else if (value == 'Proceedings'.toUpperCase()){
        value = 11;
    }else if (value == 'TechReport'.toUpperCase()){
        value = 12;
    }else if (value == 'Unpublished'.toUpperCase()){
        value = 13;
    }else if (value == 'Article'.toUpperCase()){
        value = 0;
    }
    toggleEditPanel(formSettings, contentStringName, value, panelDivID);
    //处理页码
    var pages1 = "", pages2 = "";
    if (selectedPubInfo.pages.indexOf("-")>-1){
        tmp = selectedPubInfo.pages.split("-");
        pages1 = tmp[0];
        pages2 = tmp[1];
    }
    //更改表单中显示的内容
    var enhance = new enhanceForm({
        elem: '#' + panelFormID //表单选择器
    });
    enhance.setSelectVal('paperTypeEdit', value, true);//设置文献类型下拉框选项(,,是否触发选中事件)
    enhance.setSelectVal('indexing', 0, true);//设置文献索引(,,是否触发选中事件)
    textContent = {title:selectedPubInfo.title,journal:selectedPubInfo.journal,year:selectedPubInfo.year,volume:selectedPubInfo.volume,number:selectedPubInfo.number,
                month:selectedPubInfo.month,note:selectedPubInfo.note,editor:selectedPubInfo.editor,publisher:selectedPubInfo.publisher,series:selectedPubInfo.series,address:selectedPubInfo.address,
                edition:selectedPubInfo.edition,how_published:selectedPubInfo.how_published,book_title:selectedPubInfo.book_title,organization:selectedPubInfo.organization,chapter:selectedPubInfo.chapter,
                type:selectedPubInfo.type,school:selectedPubInfo.school,keywords:selectedPubInfo.keywords,institution:selectedPubInfo.institution,
                pages1:pages1, pages2:pages2};//赋值文本框
    enhance.filling(textContent);
    //处理作者表格
    var analyzedAuthors = [];
    selectedPubInfo.author = $.trim(selectedPubInfo.author);
    if (selectedPubInfo.author == "") {
        console.log("文章缺少作者信息");
    }else{
        var authors = selectedPubInfo.author.split(" AND ");
        for (i=0;i<authors.length;i++){
            var tt = $.trim(authors[i])
                ,author = analyzeNameENForTable(tt, siteUrl, splitNameService);
            author.ranking = i+1;
            analyzedAuthors.push(author);
        }
        layui.table.render({
            elem: '#' + authorTableID
            ,cols: [[
              {field:'firstName', title:'名', width:100, edit: 'text'}
              ,{field:'middleName', title:'中间名', width:100, edit: 'text'}
              ,{field:'lastName', title:'姓', width:100, edit: 'text'}
              ,{field:'ranking', title:'排名', width:100, sort: true}
              ,{width:150, align:'center', toolbar: '#authorBarsAdd'}
            ]]
            ,page: false
            ,data: analyzedAuthors
        });
    }
    //刷新表单
    layui.form.render();
    return analyzedAuthors;
}

function processPersonPanel(selectedPersonInfo, panelFormID, enhanceForm){
    var $ = layui.$;
    //更改表单中显示的内容
    var enhance = new enhanceForm({
        elem: '#' + panelFormID //表单选择器
    });
    textContent = {full_name:selectedPersonInfo.full_name, first_name:selectedPersonInfo.first_name,  middle_name:selectedPersonInfo.middle_name,
                    last_name:selectedPersonInfo.last_name,name_ch:selectedPersonInfo.name_ch,last_name_ch:selectedPersonInfo.last_name_ch,
                    first_name_ch:selectedPersonInfo.first_name_ch,institution:selectedPersonInfo.institution,research_interest:selectedPersonInfo.research_interest,
                    note:selectedPersonInfo.note};//赋值文本框
    enhance.filling(textContent);
    //刷新表单
    layui.form.render();
}

function processVenuePanel(selectedVenueInfo, panelFormID, enhanceForm){
    var $ = layui.$;
    //更改表单中显示的内容
    var enhance = new enhanceForm({
        elem: '#' + panelFormID //表单选择器
    });
    var value = selectedVenueInfo.venue_type;
    if (value == 'Book'.toUpperCase()){
        value = 1;
    }else if (value == 'Booklet'.toUpperCase()){
        value = 2;
    }else if (value == 'Conference'.toUpperCase()){
        value = 3;
    }else if (value == 'InBook'.toUpperCase()){
        value = 4;
    }else if (value == 'InCollection'.toUpperCase()){
        value = 5;
    }else if (value == 'InProceedings'.toUpperCase()){
        value = 6;
    }else if (value == 'Manual'.toUpperCase()){
        value = 7;
    }else if (value == 'MastersThesis'.toUpperCase()){
        value = 8;
    }else if (value == 'Misc'.toUpperCase()){
        value = 9;
    }else if (value == 'PhDThesis'.toUpperCase()){
        value = 10;
    }else if (value == 'Proceedings'.toUpperCase()){
        value = 11;
    }else if (value == 'TechReport'.toUpperCase()){
        value = 12;
    }else if (value == 'Unpublished'.toUpperCase()){
        value = 13;
    }else if (value == 'Article'.toUpperCase()){
        value = 0;
    }else{
        value = ""
    }
    enhance.setSelectVal('venue_type', value, true);//设置文献类型下拉框选项(,,是否触发选中事件)
    //indexing
    enhance.setSelectVal('indexing', 1, true);//设置文献索引,,是否触发选中事件)
    //文本填充
    textContent = {venue_name:selectedVenueInfo.venue_name, abbr:selectedVenueInfo.abbr,  publisher:selectedVenueInfo.publisher,
                    start_year:selectedVenueInfo.start_year,
                    note:selectedVenueInfo.note, address:selectedVenueInfo.address};//赋值文本框
    enhance.filling(textContent);
    //刷新表单
    layui.form.render();
}

 //(4)解析英文名字的函数:
function analyzeNameENForTable(name, siteUrl, splitNameService){
    var $ = layui.$
        ,params = {textTo:name, lang:"EN"}
        ,csrftoken = Cookies.get('csrftoken')
        ,names = {firstName:"", middleName:"", lastName:""};
    $.ajax({
        type: 'POST'
        ,url: siteUrl + splitNameService
        ,data:  JSON.stringify(params)
        ,dataType : "json"
        ,async: false
        ,headers: {'Content-Type': 'application/json',"X-CSRFToken":csrftoken}
        //,contentType: "application/json"
        ,success: function(result,status,xhr) {
            names.firstName = result.first_name;
            names.middleName = result.middle_name;
            names.lastName = result.last_name;
            return false;
        }
        ,error: function(xhr,status,error){
            console.log("数据传输失败后：");
            //如果请求失败要运行的函数
            layer.msg("拆分人名失败，与服务器断开连接，请稍后再试。", {
                time: 10000, //20s后自动关闭
                btn: ['ok'],
                icon:5
            });
            console.log(error);
        }
    });
    return names;
}

//(4)解析英文名字的函数:
function analyzeNameEN(sourceID, targetIDs, siteUrl, splitNameService){
    var $ = layui.$;
    if (targetIDs.length != 3){
        console.log("目标节点数量不等于3！");
        return -1;
    }
    var name = $("#" + sourceID).val()
        ,params = {textTo:name, lang:"EN"}
        ,csrftoken = Cookies.get('csrftoken');
    $.ajax({
        type: 'POST'
        ,url: siteUrl + splitNameService
        ,data:  JSON.stringify(params)
        ,dataType : "json"
        ,headers: {'Content-Type': 'application/json',"X-CSRFToken":csrftoken}
        //,contentType: "application/json"
        ,success: function(result,status,xhr) {  //分配到相应的表单中
            console.log("数据传输成功后：");
            if (result.status == -1) {
                layui.layer.msg('解析人名失败，请手动填写！<br>' + JSON.stringify(result), {
                    time: 20000, //20s后自动关闭
                    btn: ['ok'],
                    icon:1
                });
            }else{
                $('#' + targetIDs[0]).val(result.first_name);
                $('#' + targetIDs[1]).val(result.middle_name);
                $('#' + targetIDs[2]).val(result.last_name);
            }
            layui.form.render();
            return false;
        }
        ,error: function(xhr,status,error){
            console.log("数据传输失败后：");
            //如果请求失败要运行的函数
            layui.layer.msg("拆分人名失败，与服务器断开连接，请稍后再试。", {
                time: 10000, //20s后自动关闭
                btn: ['ok'],
                icon:5
            });
            console.log(error);
        }
        ,complete: function(xhr,status){
            console.log("数据传输complete");
            //完成时的操作，success和error之后
        }

    });
}

//(5)解析中文名字的函数:
function analyzeNameCH(sourceID, targetIDs, siteUrl, splitNameService){
    var $ = layui.$;
    if (targetIDs.length != 2){
        console.log("目标节点数量不等于2！");
        return -1;
    }
    var name = $("#" + sourceID).val()
        ,params = {textTo:name, lang:"CH"};
    var csrftoken = Cookies.get('csrftoken');
    $.ajax({
        type: 'POST'
        ,url: siteUrl + splitNameService
        ,data:  JSON.stringify(params)
        ,dataType : "json"
        ,headers: {'Content-Type': 'application/json',"X-CSRFToken":csrftoken}
        //,contentType: "application/json"
        ,success: function(result,status,xhr) {  //分配到相应的表单中
            console.log("数据传输成功后：");
            if (result.status == -1) {
                layui.layer.msg('解析人名失败，请手动填写！<br>' + JSON.stringify(result), {
                    time: 20000, //20s后自动关闭
                    btn: ['ok'],
                    icon:1
                });
            }else{
                $('#' + targetIDs[0]).val(result.first_name);
                $('#' + targetIDs[1]).val(result.last_name);
            }
            layui.form.render();
            return false;
        }
        ,error: function(xhr,status,error){
            console.log("数据传输失败后：");
            //如果请求失败要运行的函数
            layui.layer.msg("拆分人名失败，与服务器断开连接，请稍后再试。", {
                time: 10000, //20s后自动关闭
                btn: ['ok'],
                icon:5
            });
            console.log(error);
        }
        ,complete: function(xhr,status){
            console.log("数据传输complete");
            //完成时的操作，success和error之后
        }
    });
}

//ajax接口：1）将文献写入数据库
function writeToDatabase(siteUrl, service, msg, divPanelID){
    var $ = layui.$
        ,csrftoken = Cookies.get('csrftoken');
    $.ajax({
        type: 'POST'
        ,url: siteUrl + service
        ,data:  JSON.stringify(msg)
        ,dataType : "json"
        ,headers: {'Content-Type': 'application/json',"X-CSRFToken":csrftoken}
        //,contentType: "application/json"
        ,beforeSend: function(){
            console.log("数据传输前：");
            console.log(msg);
        }
        ,success: function(result,status,xhr) {
            console.log("数据传输成功后：");
            //配置一个透明的询问框
            if (result.status != 1 ){
                layer.msg('失败！<br>' + JSON.stringify(result), {
                    time: 20000, //20s后自动关闭
                    btn: ['ok'],
                    icon:1
                });
            }else{
                layer.msg('成功！<br>' + JSON.stringify(result), {
                    time: 20000, //20s后自动关闭
                    btn: ['ok'],
                    icon:1
                });
                //隐藏编辑面板
                if (divPanelID != ""){
                    var state = $("#" + divPanelID).attr("class");
                    $("#" + divPanelID).attr("class", state.replace('collapse in', "collapse"));
                }
            }
            console.log("ok" + result);
        }
        ,error: function(xhr,status,error){
            console.log("数据传输失败后：");
            //如果请求失败要运行的函数
            layer.msg("添加数据失败，与数据库服务器断开连接，请稍后再试。", {
                time: 20000, //20s后自动关闭
                btn: ['ok'],
                icon:5
            });
            console.log(error);
        }
        ,complete: function(xhr,status){
            console.log("数据传输complete后：");
            //完成时的操作，success和error之后
        }

    });
}

//3)新增/编辑文献表单：验证入口函数:参数是name：value形式
function verifyPubInfo(data, contentStringName, currentAuthors) {
    var pubType = new Number(data["paperTypeEdit"])
        ,mandatory = formSettings[pubType]["mandatory"]
        ,others = formSettings[pubType]["others"];
    var msg = {"status": 2, "msg":""};
    var processedData = {};

    for (indexI=0;indexI<contentStringName.length;indexI++) {
        var valueNames = [];
        if (indexI == 0) {//作者单独判断
            if (mandatory.indexOf(indexI) > -1 | others.indexOf(indexI) > -1) {//必填字段
                var tmpMsg = verifyAuthor(currentAuthors);
                if (tmpMsg["status"]<0) {
                    console.log("必/选填：作者验证失败");
                    msg["status"] = tmpMsg["status"];
                    msg["msg"] = tmpMsg["msg"];
                    break;
                }else{
                    console.log("必/选填：作者验证成功");
                    processedData["author"] = currentAuthors;
                    continue;
                }
            }else {//未分类字段，要抛出提示
                console.log(contentStringName[indexI] + "不是选填或必填字段！")
                break;
            }
        }else if (indexI==6) { //pages
            console.log("验证pages");
            valueNames = ["pages1","pages2"];
        }else {
            console.log("验证：" + contentStringName[indexI]);
            valueNames = [contentStringName[indexI]];
        }

        var validFlag = true;
        for (j=0;j<valueNames.length;j++) {
            console.log("开始验证字段：" + valueNames[j]);
            if (data.hasOwnProperty(valueNames[j])) {//判断表单中是否有字段
                console.log("开始验证表单内容：" + valueNames[j] + ",值：" + data[valueNames[j]]);
                msg = verifyFieldValue(valueNames[j], data[valueNames[j]], contentStringName); // 判断是否为空及数字字段验证
                if (msg["status"] == -1 ) {//表单填写错误
                    console.log("表单填写错误");
                    validFlag = false;
                    msg["status"] = -1;
                    break;
                }else if (msg["status"]==0) {
                    console.log("空字段：" + valueNames[j]);
                    if (mandatory.indexOf(indexI) > -1){
                        msg["msg"] += "\n Field [" + valueNames[j] + "] 不存在";
                        validFlag = false;
                        break;
                    }else{
                        console.log("此为选填");
                    }
                }else if (msg["status"]==0){
                    console.log("不存在字段：" + valueNames[j]);
                    msg["msg"] += "\n Field [" + valueNames[j] + "] 不存在";
                    validFlag = false;
                    break;
                }else {//填写正确
                    console.log("填写正确");
                    processedData[valueNames[j]] = data[valueNames[j]];
                }
            }else {
                console.log("缺少此字段：" + valueNames[j]);
                msg = {"msg":"Missing field name[" + valueNames[j] + "]", "status": -1};
                validFlag = false;
                break;
            }
        }
        if (validFlag == false) {
            console.log("必填字段验证失败，退出验证（outer）");
            break;
        }
    }
    if (validFlag == false) {
        console.log("字段验证失败，退出验证");
        return msg;
    }
    processedData["ENTRYTYPE"] = data["paperTypeEdit"];
    msg["processedData"] = processedData;

    console.log("退出验证");
    return msg;
}

//1)新增文献表单函数1：验证作者信息格式是否正确
function verifyAuthor(currentAuthors){
    msg = {"status": 1, "msg": "OK"};
    if (currentAuthors.length==0) {
        msg["status"] = -1;
        msg["msg"] = "没有作者信息";
    }else {
        for (var i=0;i<currentAuthors.length;i++) {
            if (currentAuthors[i]["firstName"]=="" || currentAuthors[i]["lastName"]=="" || currentAuthors[i]["ranking"]=="") {
                msg["status"] = -1;
                msg["msg"] = "第" + new Number(i).toString() + "作者信息不全";
                break;
            }
        }
    }
    return msg;
}

//2)判断表单中字段:0 字段空；-1 应为数字的字段值非数字；1正常;-2 字段名不存在
function verifyFieldValue(fieldName, valueInForm, contentStringName) {
    if (fieldName == 'pages1' || fieldName == 'pages2' ) {
        fieldName = 'pages' ;
    }
    var index = contentStringName.indexOf(fieldName);
    var numberFieldIndices = [3,4,5,6,7,13,17];
    if (index<0) {// non-existing field
        return {"msg":"Unrecognized field name.", "status": -2};
    }else if (numberFieldIndices.indexOf(index)>-1) { // number field
        var tmp = new Number(valueInForm);
        if (isNaN(tmp)) {//非数字
            return {"msg":"Field [" + fieldName + "] should be Number.", "status": -1};
        }else if (tmp==0) { //空字符或0
            if (valueInForm==""){
                return {"msg":"Empty string or number 0", "status": 0};
            }
        }
    }else { // string field
        if (valueInForm == "") {
            return {"msg":"Field [" + fieldName + "] is empty", "status": 0};
        }
    }
    return {"msg":"OK.", "status": 1};
}

//新增/编辑人信息时，验证数据是否正确. -1:缺少名字；1：成功
function verifyPersonInfo(data) {
    var msg = {"status": 2, "msg":"", "processedData":""};
    var fullName = data["full_name"]
        ,firstName = data["first_name"]
        ,middleName = data["middleName"]
        ,lastName = data["last_name"]
        ,name_ch = data["name_ch"]
        ,firstNameCH = data["first_name_ch"]
        ,lastName = data["last_name_ch"]
        ,institution = data["institution"]
        ,researchInterest = data["research_interest"]
        ,note = data["note"];
    //验证英文名+名字拆分
    if ((fullName == "" | fullName == undefined)&( name_ch == "" | name_ch == undefined)){
        msg["msg"] = "At least one field 【full name】 or 【中文名】 should be filled.";
        msg["status"] = -1;
        return msg;
    }
    //todo 验证名字拆分是否正确
    msg["msg"] = "验证成功.";
    msg["status"] = 1;
    msg["processedData"] = data;
    console.log(msg);
    return msg;
}


//新增/编辑venue信息时，验证数据是否正确. -1:缺少名字；1：成功
function verifyVenueInfo(data) {
    var msg = {"status": 2, "msg":"", "processedData":""};
    var venueName = data["venue_name"]
        ,address = data["address"]
        ,startYear = data["start_year"]
        ,venueType = data["venue_type"]
        ,publisher = data["publisher"]
        ,abbr = data["abbr"]
        ,note = data["note"];
    //验证英文名+名字拆分
    if ((venueName == "" | venueName == undefined)|( venueType == "" | venueType == undefined)){
        msg["msg"] = "At least one field 【full name】 or 【中文名】 should be filled.";
        msg["status"] = -1;
        layui.layer.msg("venue name and venue type are mandatory fields！", {
            time: 5000, //5s后自动关闭
            btn: ['ok'],
            icon:5
        });
        return msg;
    }
    if (venueType == "1"){
        venueType = 'Book'.toUpperCase();
    }else if (venueType == "2"){
        venueType = 'Booklet'.toUpperCase();
    }else if (venueType == "3"){
        venueType = 'Conference'.toUpperCase();
    }else if (venueType == "4"){
        venueType = 'InBook'.toUpperCase();
    }else if (venueType == "5"){
        venueType = 'InCollection'.toUpperCase();
    }else if (venueType == "6"){
        venueType = 'InProceedings'.toUpperCase();
    }else if (venueType == "7"){
        venueType = 'InProceedings'.toUpperCase();
    }else if (venueType == "8"){
        venueType = 'MastersThesis'.toUpperCase();
    }else if (venueType == "9"){
        venueType = 'Misc'.toUpperCase();
    }else if (venueType == "10"){
        venueType = 'PhDThesis'.toUpperCase();
    }else if (venueType == "11"){
        venueType = 'Proceedings'.toUpperCase();
    }else if (venueType == "12"){
        venueType = 'TechReport'.toUpperCase();
    }else if (venueType == "13"){
        venueType = 'Unpublished'.toUpperCase();
    }else if (venueType == "0"){
        venueType = 'Article'.toUpperCase();
    }else{
        msg["msg"] = "Not valid venue type is chosen.";
        msg["status"] = -1;
        layui.layer.msg("Not valid venue type is chosen.", {
            time: 5000, //5s后自动关闭
            btn: ['ok'],
            icon:5
        });
        return msg;
    }
    data["venue_type"] = venueType;
    //todo 验证名字拆分是否正确
    msg["msg"] = "验证成功.";
    msg["status"] = 1;
    msg["processedData"] = data;
    console.log(msg);
    return msg;
}

//（6）新增关系面板中，点击起讫点之后，向底下的显示框中增加节点信息--------searchPub.html&person中需要同步修改
function showRelNodeDetail(infoDicID, addedInfo){
    var text = document.getElementById(infoDicID).innerText;
    if (text==""){
        text = {};
    }else{
        text = JSON.parse(text);
    }

    for (var tmpKey in addedInfo){
        text[tmpKey] = addedInfo[tmpKey];
    }
    text  = JSON.stringify(text, null, 2);
    document.getElementById(infoDicID).innerText = text;
    layui.code();
    layui.form.render();
}

//(7)查看数据&新增关系面板中，高级搜索（文献）的div处理过程,--------searchPub.html中需要同步修改
//advSearchDivID:高级搜索框div，editPubDivID：编辑文献框div，resultTableFilter：搜索结果表格过滤器（定位）
//resultTableID：搜索结果表格ID，没用，toolbarID：搜索结果确认按钮ID， data：高级搜索传入的数据
function advanceSearchHandler(advSearchDivID, editPubDivID, resultTableFilter, resultTableID, toolbarID, data, searchPubService){
    var $ = layui.$;
    // todo 处理搜索条件
    //parameters = {"title":data.field.title
        //, "startTime":data["startTime"]
        //, "endTime": data["endTime"]
    //    , "paperType": data["paperType"]}
    $('#' + advSearchDivID).attr("class", "collapse in");
    if (editPubDivID != "") {
        $('#' + editPubDivID).attr("class", "collapse");
    }
    layui.table.render(
        {
            elem: '#' + resultTableFilter
            ,id: resultTableID
            ,url: searchPubService
            ,toolbar: '#' + toolbarID
            ,method: 'post'
            ,where: {"title":data.field.title
                //, "startTime":data["startTime"]
                //, "endTime": data["endTime"]
                , "paperType": data.field.paperType}
            //,cellMinWidth: 80 //全局定义常规单元格的最小宽度，layui 2.2.1 新增
            ,page: { //支持传入 laypage 组件的所有参数（某些参数除外，如：jump/elem） - 详见文档
                layout: ['limit', 'count', 'prev', 'page', 'next', 'skip'] //自定义分页布局
                //,curr: 5 //设定初始在第 5 页
                ,groups: 5 //只显示 1 个连续页码
                ,first: false //不显示首页
                ,last: false //不显示尾页
            }
            ,limit: 10
            ,cols: [[{type:'radio'}
                ,{field:"ID", width:60, title: 'ID', sort: true}
                ,{field:'title', width:300, title: '标题', sort: false}
                ,{field:'author', width:200, title: '作者', sort: false}
                ,{field:'journal', width:200, title: '期刊/会议'}
                ,{field:'year', title: '年', width: '70', minWidth: 10} //minWidth：局部定义当前单元格的最小宽度，layui 2.2.1 新增
                ,{field:'month', title: '月', width: '70', minWidth: 10} //minWidth：局部定义当前单元格的最小宽度，layui 2.2.1 新增
                ,{field:'paperTypeEdit', width: '100', title: '类型', sort: true}
                ,{field:'booktitle', width: '100', title: '书名', sort: false}
                ,{field:'editor', width: '100', title: '编辑', sort: false}
                ,{field:'edition', width: '100', title: '版本', sort: false}
                ,{field:'volume', width: '100', title: '卷', sort: false}
                ,{field:'number', width: '100', title: '期', sort: false}
                ,{field:'note', width: '100', title: '备注', sort: true}
                ,{field:'keywords', width: '100', title: '关键词', sort: false}
                ,{field:'pages', width: '100', title: '页码', sort: false}
            ]]
            ,done: function(res, curr, count){;
                console.log(res);
            }
        }
    );
    return false;
}

//(8)查看数据&新增关系面板中，高级搜索（人）的div处理过程,--------searchPerson.html中需要同步修改
//advSearchDivID:高级搜索框div，editPubDivID：编辑文献框div，resultTableFilter：搜索结果表格过滤器（定位）
//resultTableID：搜索结果表格ID，没用，toolbarID：搜索结果确认按钮ID， data：高级搜索传入的数据
function advanceSearchPersonHandler(advSearchDivID, editDivID, resultTableFilter, resultTableID, toolbarID, data, searchService){
    var $ = layui.$;
    // todo 处理搜索条件
    //parameters = {"full_name":data.field.full_name
        //, "startTime":data["startTime"]
        //, "endTime": data["endTime"]
    //    , "paperType": data["paperType"]}
    $('#' + advSearchDivID).attr("class", "collapse in");
    if (editDivID != "") {
        $('#' + editDivID).attr("class", "collapse");
    }
    layui.table.render(
        {
            elem: '#' + resultTableFilter
            ,id: resultTableID
            ,url: searchService
            ,toolbar: '#' + toolbarID
            ,method: 'post'
            ,where: {"full_name":data.field.full_name}
            //,cellMinWidth: 80 //全局定义常规单元格的最小宽度，layui 2.2.1 新增
            ,page: { //支持传入 laypage 组件的所有参数（某些参数除外，如：jump/elem） - 详见文档
                layout: ['limit', 'count', 'prev', 'page', 'next', 'skip'] //自定义分页布局
                //,curr: 5 //设定初始在第 5 页
                ,groups: 5 //只显示 1 个连续页码
                ,first: false //不显示首页
                ,last: false //不显示尾页
            }
            ,limit: 10
            ,cols: [[{type:'radio'}
                ,{field:"ID", width:60, title: 'ID', sort: true}
                ,{field:'full_name', width:200, title: 'Full Name', sort: false}
                ,{field:'first_name', width:200, title: 'First Name', sort: false}
                ,{field:'middle_name', width:200, title: 'Middle Name'}
                ,{field:'last_name', title: 'Last Name', width: '200', minWidth: 10} //minWidth：局部定义当前单元格的最小宽度，layui 2.2.1 新增
                ,{field:'name_ch', title: '中文名', width: '70', minWidth: 10} //minWidth：局部定义当前单元格的最小宽度，layui 2.2.1 新增
                ,{field:'last_name_ch', width: '100', title: '姓', sort: true}
                ,{field:'first_name_ch', width: '100', title: '名', sort: false}
                ,{field:'institution', width: '100', title: 'Institution', sort: false}
                ,{field:'research_interest', width: '100', title: 'Research Interest', sort: false}
                ,{field:'note', width: '200', title: 'Note', sort: false}
            ]]
            ,done: function(res, curr, count){;
                console.log(res);
            }
        }
    );
    return false;
}

//(9)查看数据&新增关系面板中，高级搜索（venue）的div处理过程,--------searchVenue.html中需要同步修改
//advSearchDivID:高级搜索框div，editPubDivID：编辑文献框div，resultTableFilter：搜索结果表格过滤器（定位）
//resultTableID：搜索结果表格ID，没用，toolbarID：搜索结果确认按钮ID， data：高级搜索传入的数据
function advanceSearchVenueHandler(advSearchDivID, editDivID, resultTableFilter, resultTableID, toolbarID, data, searchService){
    var $ = layui.$;
    // todo 处理搜索条件
    //parameters = {"venue_name":data.field.venue_name
        //, "startTime":data["startTime"]
        //, "endTime": data["endTime"]
    //    , "paperType": data["paperType"]}
    $('#' + advSearchDivID).attr("class", "collapse in");
    if (editDivID != "") {
        $('#' + editDivID).attr("class", "collapse");
    }
    layui.table.render(
        {
            elem: '#' + resultTableFilter
            ,id: resultTableID
            ,url: searchService
            ,toolbar: '#' + toolbarID
            ,method: 'post'
            ,where: {"venue_name":data.field.venue_name}
            //,cellMinWidth: 80 //全局定义常规单元格的最小宽度，layui 2.2.1 新增
            ,page: { //支持传入 laypage 组件的所有参数（某些参数除外，如：jump/elem） - 详见文档
                layout: ['limit', 'count', 'prev', 'page', 'next', 'skip'] //自定义分页布局
                //,curr: 5 //设定初始在第 5 页
                ,groups: 5 //只显示 1 个连续页码
                ,first: false //不显示首页
                ,last: false //不显示尾页
            }
            ,limit: 10
            ,cols: [[{type:'radio'}
                ,{field:"ID", width:60, title: 'ID', sort: true}
                ,{field:'venue_name', width:200, title: 'Venue Name', sort: false}
                ,{field:'abbr', width:200, title: 'Abbr.', sort: false}
                ,{field:'publisher', width:200, title: 'Publisher'}
                ,{field:'start_year', title: 'Start Year', width: '200', minWidth: 10} //minWidth：局部定义当前单元格的最小宽度，layui 2.2.1 新增
                ,{field:'indexing', title: 'Indexing', width: '70', minWidth: 10} //minWidth：局部定义当前单元格的最小宽度，layui 2.2.1 新增
                ,{field:'venue_type', width: '100', title: 'Venue Type', sort: true}
                ,{field:'note', width: '200', title: 'Note', sort: false}
            ]]
            ,done: function(res, curr, count){;
                console.log(res);
            }
        }
    );
    return false;
}

//10)新增关系面板，点击按钮后，先显示弹出窗口，搜索节点
function processPopupWindow(buttonID, addRelInfoDiv){
    var $ = layui.$;
    var frameID;
    var nodeType = $('#' + buttonID).text();
    if (nodeType == undefined){
        return -1;
    }
    var popupUrl;
    if (nodeType == "Person"){
        popupUrl = '/search-person-popup';
    }else if (nodeType == "Venue"){
        popupUrl = '/search-venue-popup';
    }else if (nodeType == "Publication"){
        popupUrl = '/search-pub-popup';
    }else{
        console.log("未知的文献类型");
        return -1;
    }
    layui.layer.open({
        type: 2,
        title: '节点选择确认',
        maxmin: true,
        area: '700px',
        scrollbar: true,
        fixed: false,
        offset:'30px',
        //btn:['确定','取消'],
        //btnAlign: 'c',
        //yes: function(){//按钮【确定】的回调
        //    return false;
        //},
        //btn2: function(){//按钮【取消】的回调
        //    return false;
        //},
        content:popupUrl,
        success: function(layero, index){
            frameID = index;
            layer.iframeAuto(index);
        }
    });

    //显示选择的节点信息：
    var infoDivStatus = $('#' + addRelInfoDiv).attr('class');
    if (infoDivStatus.indexOf('collapse in') == -1){
        $('#' + addRelInfoDiv).attr('class', infoDivStatus.replace('collapse', 'collapse in'));
    }
    layui.form.render();
    return false;
}
