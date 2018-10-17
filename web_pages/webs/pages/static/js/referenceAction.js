
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
    enhance.setSelectVal('indexing', 0, true);//设置文献类型下拉框选项(,,是否触发选中事件)
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
              ,{field:'ranking', title:'排名', width:100, sort: true, edit: 'text'}
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
    //indexing
    enhance.setSelectVal('indexing', 1, true);//设置文献类型下拉框选项(,,是否触发选中事件)
    //文本填充
    textContent = {venue_name:selectedVenueInfo.venue_name, abbr:selectedVenueInfo.abbr,  publisher:selectedVenueInfo.publisher,
                    start_year:selectedVenueInfo.start_year,venue_type:selectedVenueInfo.venue_type,
                    note:selectedVenueInfo.note};//赋值文本框
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
