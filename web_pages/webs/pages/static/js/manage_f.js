//这个是管理文献的页面的脚本

/*
    全局变量
*/
var formSettings = [{"field":"0", "mandatory":[0,1,2,3,22], "others":[4,5,6,7,8]}
                    ,{"field":"1", "mandatory":[0,1,3,9,10,22], "others":[4,5,7,8,11,12,13]}
                    ,{"field":"2", "mandatory":[1,22], "others":[0,3,7,8,12,14]}
                    ,{"field":"3", "mandatory":[0,1,3,15,22], "others":[4,5,6,7,8,9,10,11,12,16]}
                    ,{"field":"4", "mandatory":[0,1,3,6,9,10,17,22], "others":[4,5,7,8,11,12,13,18]}
                    ,{"field":"5", "mandatory":[0,1,3,10,15,22], "others":[4,5,6,7,8,9,11,12,13,17,18]}
                    ,{"field":"6", "mandatory":[0,1,3,15,22], "others":[4,5,6,7,8,9,10,11,12,16]}
                    ,{"field":"7", "mandatory":[1,22], "others":[0,3,7,8,12,13,16]}
                    ,{"field":"8", "mandatory":[0,1,3,19,22], "others":[7,8,12,18]}
                    ,{"field":"9", "mandatory":[22], "others":[0,1,3,7,8,14]}
                    ,{"field":"10", "mandatory":[0,1,3,19,22], "others":[7,8,12,20]}
                    ,{"field":"11", "mandatory":[1,3,22], "others":[4,5,7,8,9,10,11,12,16]}
                    ,{"field":"12", "mandatory":[0,1,3,21,22], "others":[5,7,8,9,18]}
                    ,{"field":"13", "mandatory":[0,1,8,22], "others":[3,7]}
                    ];
var contentStringName = ["author","title","journal","year","volume","number",
                        "pages","month","note","editor","publisher","series","address",
                        "edition","howpublished","booktitle","organization","chapter",
                        "type","school","keywords","institution","indexing"];
var pubTypes = ["ARTICLE", "BOOK","BOOKLET","CONFERENCE","INBOOK","INCOLLECTION","INPROCEEDINGS",
                 "MANUAL","MASTERSTHESIS","MISC","PHDTHESIS","PROCEEDINGS","TECHREPORT","UNPUBLISHED"];
var currentPubType = 0;

var currentAuthors; //起点-作者信息
var currentAuthors2; //终点-作者信息
/*
    信息表格面板内容栏的监控
*/
layui.use(['form', 'element', 'laydate', 'table'], function(){
    var $ = layui.jquery
        , element = layui.element
        , form = layui.form
        , table = layui.table
        , layer = layui.layer;
    form.render();
    //起点，重置按钮
    form.on('submit(resetPubPanel1)', function(){
        //文献类型自动重置了
        toggleEditPanel(0, 'addOrEditPub1');
        form.render();
    });
    //终点，重置按钮
    form.on('submit(resetPubPanel2)', function(){
        //文献类型自动重置了
        toggleEditPanel(0, 'addOrEditPub2');
        form.render();
    });
    //关系信息，重置按钮
    form.on('submit(resetRelPanel)', function(){
        form.render();
    });
    //起点文献编辑面板显示的内容
    form.on('select(paperTypeEdit1)', function(data){
        var value = data.value;
        value = new Number(value);
        if (value.valueOf() != currentPubType.valueOf()) {
            toggleEditPanel(value, "addOrEditPub1");
            form.render();
        }
    });
    //终点文献编辑面板显示的内容
    form.on('select(paperTypeEdit2)', function(data){
        var value = data.value;
        value = new Number(value);
        if (value.valueOf() != currentPubType.valueOf()) {
            toggleEditPanel(value, "addOrEditPub2");
            form.render();
        }
    });
});

/*
    新增节点or关系
*/
layui.use(['element', 'form'], function(){
    var $ = layui.$
        ,element = layui.element
        ,form = layui.form;
    element.on('tab(tab-type)', function(data){
        console.log(data);
        if (data.index == 1){//边
            $("#edge_info").css('display', '');
            $("#node_info_2").css('display', "");
        }else if (data.index == 0){
            $("#edge_info").css('display', 'none');
            $("#node_info_2").css('display', 'none');
            document.getElementById('target-node-form').reset();
        }else{
            console.log("错误");
        }
    });
});
/*
    文献详情表单中的年份、边信息中的修改日期
*/
layui.use('laydate', function(){
    var laydate = layui.laydate;
    var myDate = new Date();
    var $ = layui.$;
    //表单1:
    var ins1 = laydate.render({
        elem: '#pubYear'
        ,type: 'year'
        ,range: false
        ,max: myDate.toLocaleDateString()     //获取当前日期
        ,min: '1900-01-01'
        ,showBottom: true
        ,change: function(value, date, endDate){
            $("#pubYear").val(value);
            if($(".layui-laydate").length){
                $(".layui-laydate").remove();
            }
        }
    });
    var ins2 = laydate.render({
        elem: '#pubYear2'
        ,type: 'year'
        ,range: false
        ,max: myDate.toLocaleDateString()     //获取当前日期
        ,min: '1900-01-01'
        ,showBottom: true
        ,change: function(value, date, endDate){
            $("#pubYear2").val(value);
            if($(".layui-laydate").length){
                $(".layui-laydate").remove();
            }
        }
    });
    var ins3 = laydate.render({
        elem: '#modifyDate'
        ,type: 'date'
        ,range: false
        ,max: myDate.toLocaleDateString()     //获取当前日期
        ,min: '1900-01-01'
        ,showBottom: true
        ,change: function(value, date, endDate){

        }
    });
});


/*
    起、终点的作者信息
*/

layui.use('table', function(){
    var table = layui.table
        ,$ = layui.$;

    //监听作者表格中增加/删除按钮
    table.on('tool(demo)', function(obj){
        addOrDeleteAuthor(currentAuthors, 'authorTable', layui, obj);
    });
    table.on('tool(demo2)', function(obj){
        addOrDeleteAuthor(currentAuthors2, 'authorTable2', layui, obj);
    });

    //监听作者表格中作者信息编辑
    table.on('edit(demo)', function(obj){
        editAuthor(currentAuthors, 'authorTable', layui, obj);
        reloadAuthorTable(currentAuthors, 'authorTable', table, 2);
    });
    table.on('edit(demo2)', function(obj){
        editAuthor(currentAuthors2, 'authorTable2', layui, obj);
        reloadAuthorTable(currentAuthors2, 'authorTable2', table, 2);
    });

    table.render({
        elem: '#idTest'
        ,url: '/demo/table/user/'
        ,cols: [[
          {field:'firstName', title:'名', width:80, edit: 'text'}
          ,{field:'middleName', title:'中间名', width:70, edit: 'text'}
          ,{field:'lastName', title:'姓', width:80, edit: 'text'}
          ,{field:'ranking', title:'排名', width:70, sort: true, edit: 'text'}
          ,{width:150, align:'center', toolbar: '#barDemo'}
        ]]
        ,id: 'authorTable'
        ,page: false
        ,done: function(res, curr, count){
            currentAuthors = deepClone(res["data"]);
        }
    });
    table.render({
        elem: '#idTest2'
        ,url: '/demo/table/user/'
        ,cols: [[
          {field:'firstName', title:'名', width:100, edit: 'text'}
          ,{field:'middleName', title:'中间名', width:100, edit: 'text'}
          ,{field:'lastName', title:'姓', width:100, edit: 'text'}
          ,{field:'ranking', title:'排名', width:100, sort: true, edit: 'text'}
          ,{width:150, align:'center', toolbar: '#barDemo2'}
        ]]
        ,id: 'authorTable2'
        ,page: false
        ,done: function(res, curr, count){
            currentAuthors2 = deepClone(res["data"]);
        }
    });

});






//##################################################################
/*
    common functions
*/

    //增加、删除作者
function addOrDeleteAuthor(currentAuthors, tableId, layui, obj){
    var data = obj.data
        ,table = layui.table
        ,layer = layui.layer
    if(obj.event === 'addAuthor'){
        if (validAuthor(data.firstName, data.lastName) == false) {
            layer.msg("请填写完整一位作者的信息再添加下一位作者");
        }else {
            if (isNaN(validRanking(data["ranking"]))) {
                layer.msg("作者排名应为非负整数");
            }else {
                reloadAuthorTable(currentAuthors, tableId, table, 1);
            }
        }
    } else if(obj.event === 'delAuthor'){
        layer.confirm('确认删除数据行(' + obj.data["ranking"]+ ')？', function(index){
            if (currentAuthors.length==1) {
                layer.msg("最少需要制定一位作者。");
                return
            }
            var emptyRows = []
                ,counter = 0;

            for (i=0;i<currentAuthors.length;i++) {
                if (identicalAuthorInfo(currentAuthors[i], obj.data)){
                    emptyRows[counter] = i;
                    counter++;
                }
            }
            for (i=emptyRows.length-1;i>-1;i--) {
                currentAuthors.splice(emptyRows[i],1);
            }

            obj.del();
            layer.close(index);
        });
    }
}
    //编辑作者
function editAuthor(currentAuthors, tableId, layui, obj){
    var value = obj.value //得到修改后的值
        ,data = obj.data //得到所在行所有键值
        ,rowIndex//所在行下标
        ,$ = layui.$
        ,field = obj.field; //字段
    //首先得到编辑单元格所在的行号，即获取在currentAuthors中下标
    for (i=0;i<currentAuthors.length;i++) {
        if (currentAuthors[i]["ranking"]==data["ranking"]) {
            rowIndex = i;
            break;
        }
    }
    if (rowIndex == undefined){// 系统错误
        layui.layer.msg("修改行所在下标查找失败，已取消所做修改，请联系管理员处理。" , {
            time: 5000, //5s后自动关闭
            btn: ['ok'],
            icon:5
        });
        layui.table.render({
            elem: '#' + tableID
            ,cols: [[
              {field:'firstName', title:'名', width:100, edit: 'text'}
              ,{field:'middleName', title:'中间名', width:100, edit: 'text'}
              ,{field:'lastName', title:'姓', width:100, edit: 'text'}
              ,{field:'ranking', title:'排名', width:100, sort: true}
              ,{width:150, align:'center', toolbar: '#authorBarsAdd'}
            ]]
            ,page: false
            ,data: currentAuthors
        });
        return currentAuthors;
    }
    // 处理数据
    var tmp = value.toUpperCase();
    tmp = tmp.replace(/\s+/g, ' ');
    tmp = $.trim(tmp);
    // 检查该条作者数据是否完整,需要判断firstName， lastName，ranking是否都填好了
    var firstName, lastName, ranking;
    if (field == "firstName"){
        firstName  = tmp;
        lastName = currentAuthors[rowIndex]["lastName"];
        ranking = currentAuthors[rowIndex]["ranking"];
    }else if (field == "lastName"){
        lastName  = tmp;
        firstName = currentAuthors[rowIndex]["firstName"];
        ranking = currentAuthors[rowIndex]["ranking"];
    }else if (field == "ranking"){
        ranking  = tmp;
        firstName = currentAuthors[rowIndex]["firstName"];
        lastName = currentAuthors[rowIndex]["lastName"];
    }else{
        ranking  = currentAuthors[rowIndex]["ranking"];
        firstName = currentAuthors[rowIndex]["firstName"];
        lastName = currentAuthors[rowIndex]["lastName"];
    }
    if (validAuthor(firstName, lastName) && validRanking(ranking)){// 信息完整，要判断作者信息是否重复
        var tt = {firstName: firstName, lastName: lastName, ranking: ranking};
        findSameFlag = false;
        for (i=0;i<currentAuthors.length;i++) {
            if (i == rowIndex){
                continue;
            }

            if (identicalAuthorInfo(currentAuthors[i], tt)){
                findSameFlag = true;
                break;
            }
        }
        if (findSameFlag){
            layer.msg("输入作者信息重复，请重新输入");
        }else{
            currentAuthors[rowIndex][field] = tmp;
        }
    }else{//信息不完整，继续填写
        currentAuthors[rowIndex][field] = tmp;
    }
    return currentAuthors;
}

    //2.判断是否有效姓名
function validAuthor(firstName, lastName) {
    if (firstName == "" && lastName == "") {
        return false;
    }else {
        return true;
    }
}
    //3.是否有效数字排名
function validRanking(ranking) {
    rankings = new Number(ranking);
    return rankings;
}
    // 5.判断arr是否为一个数组，返回一个bool值
function isArray (arr) {
    return Object.prototype.toString.call(arr) === '[object Array]';
}
    // 6.深度克隆
function deepClone (obj) {
    if(typeof obj !== "object" && typeof obj !== 'function') {
        return obj;        //原始类型直接返回
    }
    var o = isArray(obj) ? [] : {};
    for(i in obj) {
        if(obj.hasOwnProperty(i)){
            o[i] = typeof obj[i] === "object" ? deepClone(obj[i]) : obj[i];
        }
    }
    return o;
}

    //表格（1）"增加文献表格"中的"作者列表表格" 重载
function reloadAuthorTable(currentAuthors, tableId, table, mode){
    var $ = layui.$
        ,demoReload = $('#' + tableId);

    //执行重载
    table.reload(tableId, {
        where: {
            currentData: JSON.stringify(currentAuthors)
            , mode: mode
        }
    });
}

    //7.判断两条作者信息是否相同
function identicalAuthorInfo(item1, item2) {
    var fields = ["firstName", 'middleName', 'lastName','ranking'];
    var identical = true;
    fields.forEach(function(field) {
        if (item1.hasOwnProperty(field) && item2.hasOwnProperty(field)) {
            if (item1[field] != item2[field]) {
                identical = false;
            }
        }else{
            identical = false;
        }
    });
    return identical;
}

    //"新增/编辑文献"表格--关闭/开启文献编辑面板中各Item
function toggleEditPanel(value, formPrefix) {
    var $ = layui.jquery
    if (formSettings==undefined || contentStringName==undefined) {

    }else {
        var mandatory = formSettings[value]["mandatory"],
            others = formSettings[value]["others"];
        for (i=0;i<contentStringName.length;i++) {
            var element = $("#" + formPrefix + "-" + contentStringName[i])
                ,subInput = element.find('input');
            if (mandatory.includes(i)) {
                element.attr("style", "display:auto");
                if (subInput.length>0) {
                    for (j=0;j<subInput.length;j++) {
                        subInput[j].placeholder = "必填";
                    }
                }
            }else if (others.includes(i)){
                element.attr("style", "display:auto");
                if (subInput.length>0) {
                    for (j=0;j<subInput.length;j++) {
                        subInput[j].placeholder = "选填";
                    }
                }
            }else {
                element.attr("style", "display:none");
            }
        }
        currentPubType = value.valueOf();
    }
}
