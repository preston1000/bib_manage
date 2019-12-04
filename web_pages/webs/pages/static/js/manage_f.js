//这个是管理文献的页面的脚本

/*
    全局变量
*/
var formSettings = [{"field":"0", "mandatory":[0,1,2,3,22,23], "others":[4,5,6,7,8]}
                    ,{"field":"1", "mandatory":[0,1,3,9,10,22,23], "others":[4,5,7,8,11,12,13]}
                    ,{"field":"2", "mandatory":[1,22,23], "others":[0,3,7,8,12,14]}
                    ,{"field":"3", "mandatory":[0,1,3,15,22,23], "others":[4,5,6,7,8,9,10,11,12,16]}
                    ,{"field":"4", "mandatory":[0,1,3,6,9,10,17,22,23], "others":[4,5,7,8,11,12,13,18]}
                    ,{"field":"5", "mandatory":[0,1,3,10,15,22,23], "others":[4,5,6,7,8,9,11,12,13,17,18]}
                    ,{"field":"6", "mandatory":[0,1,3,15,22,23], "others":[4,5,6,7,8,9,10,11,12,16]}
                    ,{"field":"7", "mandatory":[1,22,23], "others":[0,3,7,8,12,13,16]}
                    ,{"field":"8", "mandatory":[0,1,3,19,22,23], "others":[7,8,12,18]}
                    ,{"field":"9", "mandatory":[22,23], "others":[0,1,3,7,8,14]}
                    ,{"field":"10", "mandatory":[0,1,3,19,22,23], "others":[7,8,12,20]}
                    ,{"field":"11", "mandatory":[1,3,22,23], "others":[4,5,7,8,9,10,11,12,16]}
                    ,{"field":"12", "mandatory":[0,1,3,21,22,23], "others":[5,7,8,9,18]}
                    ,{"field":"13", "mandatory":[0,1,8,22,23], "others":[3,7]}
                    ];
var contentStringName = ["author","title","journal","year","volume","number",
                        "pages","month","note","editor","publisher","series","address",
                        "edition","how_published","book_title","organization","chapter",
                        "type","school","keywords","institution","indexing", "id"];
var pubTypes = ["ARTICLE", "BOOK","BOOKLET","CONFERENCE","INBOOK","INCOLLECTION","INPROCEEDINGS",
                 "MANUAL","MASTERSTHESIS","MISC","PHDTHESIS","PROCEEDINGS","TECHREPORT","UNPUBLISHED"];
var currentPubType = 0;

var currentAuthors; //起点-作者信息
var currentAuthors2; //终点-作者信息


var colSet1 = [[ //标题栏
    {field: 'ID', title: 'ID', width: 40, sort: true}
    ,{field: 'title', title: 'Title', width: 200}
    ,{field: 'author', title: 'Author', minWidth: 150}
    ,{field: 'journal', title: 'Journal', minWidth: 150}
    ,{field: 'volume', title: 'Volume', width: 80}
    ,{field: 'number', title: 'Number', width: 80}
    ,{field: 'node_type', title: 'Type', width: 80, sort: true}
]];
var colSet2 = [[ //标题栏
    {type: 'radio'}
    ,{field: 'ID', title: 'ID', width: 40, sort: true}
    ,{field: 'title', title: 'Title', width: 200}
    ,{field: 'author', title: 'Author', minWidth: 150}
    ,{field: 'journal', title: 'Journal', minWidth: 150}
    ,{field: 'volume', title: 'Volume', width: 80}
    ,{field: 'number', title: 'Number', width: 80}
    ,{field: 'node_type', title: 'Type', width: 80, sort: true}
]];
var colSetVenueMany = [[ //for venue
    {type: 'radio'}
    ,{field: 'ID', title: 'ID', width: 60, sort: true}
    ,{field: 'name', title: 'Title', width: 200}
    ,{field: 'publisher', title: 'Publisher', minWidth: 150}
    ,{field: 'type', title: 'Type', minWidth: 100}
    ,{field: 'address', title: 'Address', width: 80}
    ,{field: 'website', title: 'Website', width: 100}
]];

var addPubService = "/add-pub/"

var sourceFormData;
var targetFormData;
var edgeFormData;
/*
    信息表格面板内容栏的监控--重置按钮、表单内容框决策
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
    //终点1-文献，重置按钮
    form.on('submit(resetPubPanel2)', function(){
        //文献类型自动重置了
        toggleEditPanel(0, 'addOrEditPub2');
        form.render();
    });
    //终点2-人，重置按钮
    form.on('submit(resetPersonPanel)', function(){
        form.render();
    });
    //终点3-venue，重置按钮
    form.on('submit(resetVenuePanel)', function(){
        form.render();
    });
    //关系信息，重置按钮
    form.on('submit(resetRelPanel)', function(){
        $("#node_info_2").css('display', 'none');// pub
        document.getElementById('target-node-form').reset();
        $("#node_info_3").css('display', 'none'); // person
        document.getElementById('target-node-form-person').reset();
        $("#node_info_4").css('display', 'none');// venue
        document.getElementById('target-node-form-venue').reset();
        form.render();
    });
    //起点文献编辑面板显示的内容
    form.on('select(node_type1)', function(data){
        var value = data.value;
        value = new Number(value);
        if (value.valueOf() != currentPubType.valueOf()) {
            toggleEditPanel(value, "addOrEditPub1");
            form.render();
        }
    });
    //终点文献编辑面板显示的内容
    form.on('select(node_type2)', function(data){
        var value = data.value;
        value = new Number(value);
        if (value.valueOf() != currentPubType.valueOf()) {
            toggleEditPanel(value, "addOrEditPub2");
            form.render();
        }
    });
    //表单回车无功能
    $(document).keydown(function (e) {
        if (e.keyCode === 13) {
            return false;
        }
    });
});

/*
    新增节点or关系 tab选项+隐藏面板的选择监听
*/
layui.use(['element', 'form', 'layer'], function(){
    var $ = layui.$
        ,element = layui.element
        ,layer = layui.layer
        ,form = layui.form;
    // tab按钮的监听，开关Relation窗口
    element.on('tab(tab-type)', function(data){
        console.log(data);
        if (data.index == 1){//边
            $("#edge_info").css('display', '');
//            $("#node_info_2").css('display', "");
        }else if (data.index == 0){
            $("#edge_info").css('display', 'none');
        }else{
            console.log("错误");
        }
    });
    // relation窗口中关系类型的监听，开关终点详情面板
    form.on('select(edgeTypeEdit)', function(data){
        var value = data.value;
        if (value == ""){//终点面板全关闭，并重置
            $("#node_info_2").css('display', 'none');// pub
            document.getElementById('target-node-form').reset();
            $("#node_info_3").css('display', 'none'); // person
            document.getElementById('target-node-form-person').reset();
            $("#node_info_4").css('display', 'none');// venue
            document.getElementById('target-node-form-venue').reset();
            $("#author_rank").css('display', 'none'); // 作者排名
        }else{
            value = new Number(value);
            if (value == 1){// published in
                $("#node_info_2").css('display', 'none');// pub
                document.getElementById('target-node-form').reset();
                $("#node_info_3").css('display', 'none'); // person
                document.getElementById('target-node-form-person').reset();
                $("#node_info_4").css('display', '');// venue
                $("#author_rank").css('display', 'none'); // 作者排名
            }else if (value == 2){//cite
                $("#node_info_2").css('display', '');
                $("#node_info_3").css('display', 'none');
                document.getElementById('target-node-form-person').reset();
                $("#node_info_4").css('display', 'none');
                document.getElementById('target-node-form-venue').reset();
                $("#author_rank").css('display', 'none'); // 作者排名
            }else if (value == 3){// author
                $("#node_info_2").css('display', 'none');// pub
                document.getElementById('target-node-form').reset();
                $("#node_info_3").css('display', ''); // person
                $("#node_info_4").css('display', 'none');// venue
                document.getElementById('target-node-form-venue').reset();
                $("#author_rank").css('display', ''); // 作者排名
            }else{
                layer.error("边类型选择出错，未知编号")
            }
        }
        return false;
    });
});
/*
    文献详情表单中的年份、边信息中的修改日期--- 时间相关
*/
layui.use('laydate', function(){
    var laydate = layui.laydate;
    var myDate = new Date();
    var $ = layui.$;
    //表单1:起点，文献年
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
    //表单2：终点，文献年
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
    //表单3：关系，日期
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
    //表单4，终点，期刊起始年
    var ins3 = laydate.render({
        elem: '#venue-start-year'
        ,type: 'year'
        ,range: false
        ,max: myDate.toLocaleDateString()     //获取当前日期
        ,min: '1900-01-01'
        ,showBottom: true
        ,change: function(value, date, endDate){

        }
    });
});


/*
    数据表格相关----起、终点的作者信息
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

/*
    表单提交相关------信息表格面板内容check功能
*/
layui.use(['form', 'layer', 'element', 'laydate', 'table'], function(){
    var $ = layui.jquery
        , element = layui.element
        , form = layui.form
        , table = layui.table
        , layer = layui.layer;
    form.render();
    //起点，check按钮
    form.on('submit(checkPaper1)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field));
        var formValue = data.field;
        if (!formValue.hasOwnProperty("title") || formValue["title"] == "") {
            layer.msg("请输入文献名以供检查");
            return false;
        }
        //这里只需要title就可以了
        $.ajax({
            type: 'POST'
            ,url: '/search/result/'
            ,data: JSON.stringify(formValue)
            ,dataType : "json"
//            ,headers: {'Content-Type': 'application/json'}
            ,contentType: "application/json"
            ,async:false
            ,beforeSend: function(){
                console.log(formValue);
            }
            ,success: function(result,status,xhr) {
//                //配置一个透明的确认框，显示搜索结果
                if (result["code"] < 0){
                    layer.msg("后台查询错误！<br>" + result["msg"]);
                    return false;
                }else if (result["code"] == 0){
                    layer.msg(result["msg"]);
                    return false;
                }else{
                    var queryResult = result["data"];
                    if (queryResult.length == 1){ // 当只有一条数据的时候，将信息显示出来，并提供选项是否写入表单
                        layer.open({
                            type: 1
                            ,title: "只有一篇文献符合条件" //显示标题栏
                            ,closeBtn: 2
//                            ,area: '500px;'
                            ,shade: 0.8
                            ,id: 'lay_popup_1' //设定一个id，防止重复弹出
                            ,btn: ['确认', '取消']
                            ,btnAlign: 'c'
                            ,moveType: 1 //拖拽模式，0或者1
                            ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">'
                                + '<table class="layui-hide" id="popupTable1" lay-filter="popupTable1"></table>' + '</div>'
                            ,success: function(layero){
                                //展示已知数据
                                table.render({
                                    elem: '#popupTable1'
                                    ,cols: colSet1
                                    ,data:queryResult
                                    ,even: true
                                });
                            }
                            ,yes: function(index, layero){
                                //填入数据表格中
                                var indexT = pubTypes.indexOf(queryResult[0]["node_type"]);
//                                indexT = 2;
                                toggleEditPanel(indexT, 'addOrEditPub1');
//                                return false;
                                var formData = queryResult[0];
                                formData["pubMonth"] = queryResult[0]["month"];
                                formData["node_type"] = indexT;
                                form.val('addOrEditPubPanel1', formData);
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                            ,btn2: function(index, layero){
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                        });
                    }else if (queryResult.length > 1){
                        layer.open({
                            type: 1
                            ,title: "有多篇文献符合条件，请选择至多一项" //显示标题栏
                            ,closeBtn: 2
                            ,shade: 0.8
                            ,maxHeight: 500
                            ,maxWidth: 400
                            ,id: 'lay_popup_2' //设定一个id，防止重复弹出
                            ,btn: ['确认', '取消']
                            ,btnAlign: 'c'
                            ,moveType: 1 //拖拽模式，0或者1
                            ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">'
                                + '<table class="layui-hide" id="popupTable2" lay-filter="popupTable2"></table>' + '</div>'
                            ,success: function(layero, index){
                                //展示已知数据
                                table.render({
                                    elem: '#popupTable2'
                                    ,cols: colSet2
                                    ,data: queryResult
                                    ,toolbar: '#popup'
                                    ,even: true
                                    ,page: true //是否显示分页
                                    ,scrollbar: true
                                });
                                layer.full(index);
                            }
                            ,yes: function(index, layero){
                                //填入数据表格中
                                $('#checkData1').click();
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                            ,btn2: function(index, layero){
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                        });
                        return false;
                    }else{
                        layer.msg("查询成功但没有结果？？");
                        return false;
                    }
                }
            }
            ,error: function(xhr,status,error){
                //如果请求失败要运行的函数
                layer.msg("请求查询失败，与数据库服务器断开连接，请稍后再试。", {
                    time: 20000, //20s后自动关闭
                    btn: ['ok'],
                    icon:5
                });
                console.log(error);
            }
            ,complete: function(xhr,status){
                //完成时的操作，success和error之后
                console.log(status);
            }
        });
        return false;



    });
    //终点，check按钮--pub的
    form.on('submit(checkPaper2)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field));
        var formValue = data.field;
        if (!formValue.hasOwnProperty("title") || formValue["title"] == "") {
            layer.msg("请输入文献名以供检查");
            return false;
        }
        //这里只需要title就可以了
        $.ajax({
            type: 'POST'
            ,url: '/search/result/'
            ,data: JSON.stringify(formValue)
            ,dataType : "json"
//            ,headers: {'Content-Type': 'application/json'}
            ,contentType: "application/json"
            ,async:false
            ,beforeSend: function(){
                console.log(formValue);
            }
            ,success: function(result,status,xhr) {
//                //配置一个透明的确认框，显示搜索结果
                if (result["code"] < 0){
                    layer.msg("后台查询错误！<br>" + result["msg"]);
                    return false;
                }else if (result["code"] == 0){
                    layer.msg(result["msg"]);
                    return false;
                }else{
                    var queryResult = result["data"];
                    if (queryResult.length == 1){ // 当只有一条数据的时候，将信息显示出来，并提供选项是否写入表单
                        layer.open({
                            type: 1
                            ,title: "只有一篇文献符合条件" //显示标题栏
                            ,closeBtn: 2
//                            ,area: '500px;'
                            ,shade: 0.8
                            ,id: 'lay_popup_terminal1' //设定一个id，防止重复弹出
                            ,btn: ['确认', '取消']
                            ,btnAlign: 'c'
                            ,moveType: 1 //拖拽模式，0或者1
                            ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">'
                                + '<table class="layui-hide" id="popupTableTerminal1" lay-filter="popupTableTerminal1"></table>' + '</div>'
                            ,success: function(layero){
                                //展示已知数据
                                table.render({
                                    elem: '#popupTableTerminal1'
                                    ,cols: colSet1
                                    ,data:queryResult
                                    ,even: true
                                });
                            }
                            ,yes: function(index, layero){
                                //填入数据表格中
                                var indexT = pubTypes.indexOf(queryResult[0]["node_type"]);
                                toggleEditPanel(indexT, 'addOrEditPub2');//distinguish
                                var formData = queryResult[0];
                                formData["pubMonth"] = queryResult[0]["month"];
                                formData["node_type"] = indexT;
                                form.val('addOrEditPubPanel2', formData); // distinguish
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                            ,btn2: function(index, layero){
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                        });
                    }else if (queryResult.length > 1){
                        layer.open({
                            type: 1
                            ,title: "有多篇文献符合条件，请选择至多一项" //显示标题栏
                            ,closeBtn: 2
                            ,shade: 0.8
                            ,maxHeight: 500
                            ,maxWidth: 400
                            ,id: 'lay_popup_terminal2' //设定一个id，防止重复弹出
                            ,btn: ['确认', '取消']
                            ,btnAlign: 'c'
                            ,moveType: 1 //拖拽模式，0或者1
                            ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">'
                                + '<table class="layui-hide" id="popupTableTerminal2" lay-filter="popupTableTerminal2"></table>' + '</div>'
                            ,success: function(layero, index){
                                //展示已知数据
                                table.render({
                                    elem: '#popupTableTerminal2'
                                    ,cols: colSet2
                                    ,data: queryResult
                                    ,toolbar: '#popupTerminal'
                                    ,even: true
                                    ,page: true //是否显示分页
                                    ,scrollbar: true
                                });
                                layer.full(index);
                            }
                            ,yes: function(index, layero){
                                //填入数据表格中
                                $('#checkDataTerminalPub').click();
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                            ,btn2: function(index, layero){
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                        });
                        return false;
                    }else{
                        layer.msg("查询成功但没有结果？？");
                        return false;
                    }
                }
            }
            ,error: function(xhr,status,error){
                //如果请求失败要运行的函数
                layer.msg("请求查询失败，与数据库服务器断开连接，请稍后再试。", {
                    time: 20000, //20s后自动关闭
                    btn: ['ok'],
                    icon:5
                });
                console.log(error);
            }
            ,complete: function(xhr,status){
                //完成时的操作，success和error之后
                console.log(status);
            }
        });
        return false;



    });
    //终点，check按钮--venue的
    form.on('submit(checkVenue)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field));
        var formValue = data.field;
        var tmp = formValue["name"]
        if (tmp == undefined) {
            layer.msg("请输入期刊名以供检查");
            return false;
        }
        tmp = tmp.replace(/\s+/g, ' ');
        tmp = $.trim(tmp);
        if (tmp == "") {
            layer.msg("请输入有效期刊名以供检查");
            return false;
        }
        var passData = {venue_name: tmp}
        //这里只需要title就可以了
        $.ajax({
            type: 'POST'
            ,url: '/search-venue/'
            ,data: JSON.stringify(passData)
            ,dataType : "json"
//            ,headers: {'Content-Type': 'application/json'}
            ,contentType: "application/json"
            ,async:false
            ,beforeSend: function(){
                console.log(passData);
            }
            ,success: function(result,status,xhr) {
//                //配置一个透明的确认框，显示搜索结果
                if (result["code"] < 0){
                    layer.msg("后台查询错误！<br>" + result["msg"]);
                    return false;
                }else if (result["code"] == 0){
                    layer.msg(result["msg"]);
                    return false;
                }else{
                    var queryResult = result["data"];
                    //整理字段
                    var processedResult = new Array(queryResult.length);
                    for (var i = 0; i<queryResult.length; i++){
                        var tmp1 = "", tmp2 = "", tmp3 = "", tmp4 = "", tmp5 = "", tmp6 = "";
                        if (queryResult[i].hasOwnProperty("address")){
                            tmp1 = queryResult[i]["address"];
                        }
                        if (queryResult[i].hasOwnProperty("publisher")){
                            tmp2 = queryResult[i]["publisher"];
                        }
                        if (queryResult[i].hasOwnProperty("type")){
                            if (queryResult[i]["type"] == "ARTICLE")
                                tmp3 = "0";
                            else if (queryResult[i]["type"] == "BOOK" || queryResult[i]["type"] == "INBOOK")
                                tmp3 = "1";
                            else if (queryResult[i]["type"] == "BOOKLET")
                                tmp3 = "2";
                            else if (queryResult[i]["type"] == "CONFERENCE" || queryResult[i]["type"] == "INCOLLECTION" || queryResult[i]["type"] == "INPROCEEDINGS" || queryResult[i]["type"] == "PROCEEDINGS")
                                tmp3 = "3";
                            else if (queryResult[i]["type"] == "MANUAL")
                                tmp3 = "4";
                            else
                                tmp3 = "5";
                        }
                        if (queryResult[i].hasOwnProperty("venue_name")){
                            tmp4 = queryResult[i]["venue_name"];
                        }
                        if (queryResult[i].hasOwnProperty("website")){
                            tmp5 = queryResult[i]["website"];
                        }
                        if (queryResult[i].hasOwnProperty("ID")){
                            tmp6 = queryResult[i]["ID"];
                        }
                        processedResult[i] = {address: tmp1, publisher: tmp2, type: tmp3, name: tmp4, website: tmp5, ID: tmp6};
                    }
                    queryResult = processedResult;
                    if (queryResult.length == 1){ // 当只有一条数据的时候，将信息显示出来，并提供选项是否写入表单
                        layer.open({
                            type: 1
                            ,title: "只有一个期刊符合条件" //显示标题栏
                            ,closeBtn: 2
//                            ,area: '500px;'
                            ,shade: 0.8
                            ,id: 'lay_popup_terminal3' //设定一个id，防止重复弹出++2
                            ,btn: ['确认', '取消']
                            ,btnAlign: 'c'
                            ,moveType: 1 //拖拽模式，0或者1
                            ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">'
                                + '<table class="layui-hide" id="popupTableTerminal3" lay-filter="popupTableTerminal3"></table>' + '</div>'
                            ,success: function(layero){
                                //展示已知数据
                                table.render({
                                    elem: '#popupTableTerminal3'
                                    ,cols: colSetVenue
                                    ,data: queryResult
                                    ,even: true
                                });
                            }
                            ,yes: function(index, layero){
                                //填入数据表格中
                                form.val('addOrEditVenuePanel', queryResult[0]); // distinguish
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                            ,btn2: function(index, layero){
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                        });
                    }else if (queryResult.length > 1){
                        layer.open({
                            type: 1
                            ,title: "有多篇期刊符合条件，请选择至多一项" //显示标题栏
                            ,closeBtn: 2
                            ,shade: 0.8
                            ,maxHeight: 500
                            ,maxWidth: 400
                            ,id: 'lay_popup_terminal4' //设定一个id，防止重复弹出
                            ,btn: ['确认', '取消']
                            ,btnAlign: 'c'
                            ,moveType: 1 //拖拽模式，0或者1
                            ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">'
                                + '<table class="layui-hide" id="popupTableTerminal4" lay-filter="popupTableTerminal4"></table>' + '</div>'
                            ,success: function(layero, index){
                                //展示已知数据
                                table.render({
                                    elem: '#popupTableTerminal4'
                                    ,cols: colSetVenueMany
                                    ,data: queryResult
                                    ,toolbar: '#popupTerminalVenue'
                                    ,even: true
                                    ,page: true //是否显示分页
                                    ,scrollbar: true
                                });
                                layer.full(index);
                            }
                            ,yes: function(index, layero){
                                //填入数据表格中
                                $('#checkDataTerminalVenue').click();
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                            ,btn2: function(index, layero){
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                        });
                        return false;
                    }else{
                        layer.msg("查询成功但没有结果？？");
                        return false;
                    }
                }
            }
            ,error: function(xhr,status,error){
                //如果请求失败要运行的函数
                layer.msg("请求查询失败，与数据库服务器断开连接，请稍后再试。", {
                    time: 20000, //20s后自动关闭
                    btn: ['ok'],
                    icon:5
                });
                console.log(error);
            }
            ,complete: function(xhr,status){
                //完成时的操作，success和error之后
                console.log(status);
            }
        });
        return false;



    });
});

/*
    弹出窗口（表格数据）写入表单中（check写入表单的功能实现）
*/
layui.use(['table', 'form'], function(){
    var table = layui.table
        ,form = layui.form;
    //check起点表单--数据写入表单
    table.on('toolbar(popupTable2)', function(obj){
        var checkStatus = table.checkStatus(obj.config.id);
        switch(obj.event){
            case 'getCheckData':
                var data = checkStatus.data;
                var indexT = pubTypes.indexOf(data[0]["node_type"]);
                toggleEditPanel(indexT, 'addOrEditPub1');
                var formData = data[0];
                formData["pubMonth"] = data[0]["month"];
                formData["node_type"] = indexT;
                form.val('addOrEditPubPanel1', formData);
            break;
        };
    });
    //check终点文献表单--数据写入表单
    table.on('toolbar(popupTableTerminal2)', function(obj){
        var checkStatus = table.checkStatus(obj.config.id);
        switch(obj.event){
            case 'getCheckData':
                var data = checkStatus.data;
                var indexT = pubTypes.indexOf(data[0]["node_type"]);
                toggleEditPanel(indexT, 'addOrEditPub2');//dis
                var formData = data[0];
                formData["pubMonth"] = data[0]["month"];
                formData["node_type"] = indexT;
                form.val('addOrEditPubPanel2', formData);//dis
            break;
        };
    });
    //check终点期刊表单--数据写入表单
    table.on('toolbar(popupTableTerminal4)', function(obj){
        var checkStatus = table.checkStatus(obj.config.id);
        switch(obj.event){
            case 'getCheckData':
                var data = checkStatus.data;
                form.val('addOrEditVenuePanel', data[0]); // distinguish
            break;
        };
    });
});

/*
    信息完成后提交按钮事件
*/

layui.use(['form', 'layer', 'element', 'laydate', 'table'], function(){
    var $ = layui.jquery
        , element = layui.element
        , form = layui.form
        , table = layui.table
        , layer = layui.layer;
    $('#submit-info').click(function(data){
        //首先检查选项卡状态
        var tabId = $('.layui-this').attr("id");
        //检查起点数据是否完整
        if (tabId == "tab-node" || tabId == "tab-rel"){
            $('#submitDataHiddenSource').click();
            if (sourceFormData == undefined || sourceFormData["code"] != 1){
                layer.msg('起点（文献）面板数据检验未通过！<br>');
                resetPanelVerifyData();
                return false;
            }else{
                layer.msg('起点（文献）面板数据检验通过！' + JSON.stringify(sourceFormData["data"]));
            }
        }else{
            layer.msg("未知的选项卡！")
            resetPanelVerifyData();
            return false;
        }
        //检查edge表单和终点表单
        if (tabId == "tab-rel"){
            //检查边表单
            $('#submitDataHiddenSource').click();
            if (edgeFormData == undefined || edgeFormData["code"] != 1){
                layer.msg('关系信息面板数据检验未通过！<br>' + edgeFormData["msg"]);
                resetPanelVerifyData();
                return false;
            }
            //检查终点表单
            if (edgeFormData["edge-type"] == "1"){//published_in: venue
                $('#targetPanelSubmitVenue').click();
            }else if (edgeFormData["edge-type"] == "2"){//cite: pub
                $('#targetPanelSubmitPub').click();
            }else if (edgeFormData["edge-type"] == "3"){//authored: person
                $('#targetPanelSubmitPerson').click();
            }else{
                layer.msg('未知的关系类型！<br>');
                resetPanelVerifyData();
                return false;
            }
            if (targetFormData == undefined || targetFormData["code"] != 1){
                layer.msg('终点信息面板数据检验未通过！<br>' + targetFormData["msg"]);
                resetPanelVerifyData();
                return false;
            }
            // 根据提交的三个表单，查询数据，todo
        }else{//只查询并创建文献节点
            //整理数据格式，以传入接口，还要有to_create，return_type传入，决定是否要新建+中间数据格式
            var tmpVar = deepClone(sourceFormData["data"]);
            tmpVar["to_create"] = 0
            tmpVar["return_type"] = 'dict'
            //先查询，检查是否有相同节点（按照check的功能执行） todo 需要根据各paperType的必填字段来决定搜索的条件，在后台执行，前台发送所有字段信息

            $.ajax({
                type: 'POST'
                ,url: addPubService
                ,data: JSON.stringify(tmpVar)
                ,dataType : "json"
        //            ,headers: {'Content-Type': 'application/json'}
                ,contentType: "application/json"
                ,async:false
                ,beforeSend: function(){
                    console.log(tmpVar);
                }
                ,success: function(result,status,xhr) {
                    if (result["code"] < 0){
                        layer.msg("后台查询错误！<br>" + result["msg"]);
                    }else if (result["code"] == 0){
                        layer.confirm('确定写入数据库？', function(index){//这里要询问是否将输入信息写入数据库
                            tmpVar["to_create"] = 1;
                            $.ajax({
                                type: 'POST'
                                ,url: addPubService
                                ,data: JSON.stringify(tmpVar)
                                ,dataType : "json"
                        //            ,headers: {'Content-Type': 'application/json'}
                                ,contentType: "application/json"
                                ,async:false
                                ,beforeSend: function(){
                                    console.log(tmpVar);
                                }
                                ,success: function(result,status,xhr) {
                                    if (result['code'] > 0){
                                        layer.msg('写入成功');
                                    }else{
                                        layer.msg('写入失败');
                                    }
                                    return false;
                                }
                            });
                            layer.close(index);
                        });
                    }else{//有一条或多条相关数据，
                        var queryResult = result["data"]; //这里的字段和数据库中一致
                        //数据整理，字段要匹配 todo
                        queryResult['node_type'] = queryResult["node_type"];
                        layer.open({
                            type: 1
                            ,title: "数据库中有文献与输入数据匹配，请选择下一步操作" //
                            ,closeBtn: 2
                            ,shade: 0.8
                            ,maxHeight: 500
                            ,maxWidth: 400
                            ,id: 'lay_popup_confirm_pub_only' //设定一个id，防止重复弹出
                            ,btn: ["确认输入", '取消']//这里的想法是，只有两种结果，一是将输入数据写入数据库，二是取消写入，返回编辑窗口，
                            ,btnAlign: 'c'
                            ,moveType: 1 //拖拽模式，0或者1
                            ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">'
                                + '<div><table class="layui-hide" id="confirm_pub_input" lay-filter="confirm_pub_input"></table></div>'
                                + '<div><table class="layui-hide" id="confirm_pub_db" lay-filter="confirm_pub_db"></table>'
                                + '</div>' + '</div>'
                            ,success: function(layero, index){
                                table.render({//展示输入数据
                                    elem: '#confirm_pub_input'
                                    ,cols: colSet1
                                    ,data: sourceFormData
//                                    ,toolbar: '#confirm_pub_input_toolbar'
                                    ,even: true
                                    ,page: false //是否显示分页
                                    ,scrollbar: true
                                });
                                table.render({
                                    elem: '#confirm_pub_db'
                                    ,cols: colSet1
                                    ,data: queryResult
                                    ,even: true
                                    ,page: true //是否显示分页
                                    ,scrollbar: true
                                });
                                layer.full(index);
                            }
                            ,yes: function(index, layero){//重新调用接口，写入数据库 todo 应该用revise pub的接口
                                tmpVar["to_create"] = 1;
                                $.ajax({
                                    type: 'POST'
                                    ,url: addPubService
                                    ,data: JSON.stringify(tmpVar)
                                    ,dataType : "json"
                            //            ,headers: {'Content-Type': 'application/json'}
                                    ,contentType: "application/json"
                                    ,async:false
                                    ,beforeSend: function(){
                                        console.log(tmpVar);
                                    }
                                    ,success: function(result,status,xhr) {
                                        if (result['code'] > 0){//
                                            layer.msg('写入成功');
                                        }else{
                                            layer.msg('写入失败');
                                        }
                                        return false;
                                    }
                                });
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                            ,btn2: function(index, layero){
                                layer.close(index); //如果设定了yes回调，需进行手工关闭
                            }
                        });
                    }
                    return false;
                }
                ,error: function(xhr,status,error){
                    //如果请求失败要运行的函数
                    layer.msg("请求查询失败，与数据库服务器断开连接，请稍后再试。", {
                        time: 20000, //20s后自动关闭
                        btn: ['ok'],
                        icon:5
                    });
                    console.log(error);
                }
                ,complete: function(xhr,status){
                    //完成时的操作，success和error之后
                    console.log(status);
                }
            });
        }
        return false;
    });
});

function resetPanelVerifyData(){
    sourceFormData = undefined;
    targetFormData = undefined;
    edgeFormData = undefined
}


//提交文献信息
layui.use(['form','layer'], function(){
    var $ = layui.jquery
        , element = layui.element
        , form = layui.form
        , table = layui.table
        , layer = layui.layer;
    //隐藏节点：起点面板数据提取
    form.on('submit(submitDataHiddenSource)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field));
        msg = verifyPubInfo(data.field, currentAuthors);
        if (msg["status"]<1) {
            layer.msg(msg["msg"]);
            console.log("结束验证，验证失败");
        }else{
            console.log("结束验证，验证正确");
            sourceFormData = {};
            sourceFormData["code"] = 1;
            sourceFormData["data"] = msg["data"];
            sourceFormData["msg"] = msg["msg"];
        }
        return false;
    });
    //隐藏节点：边表单
    form.on('submit(edgePanelSubmit)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field));
        edgeFormData = {};
        edgeFormData["code"] = 1;
        edgeFormData["data"] = data.field;
        edgeFormData["msg"] = "OK";
        return false;
    });
    //隐藏节点：终点pub表单
    form.on('submit(targetPanelSubmitPub)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field));
        msg = verifyPubInfo(data.field, currentAuthors2);
        if (msg["status"]<1) {
            layer.msg(msg["msg"]);
            console.log("结束验证，验证失败");

        }else{
            console.log("结束验证，验证正确");
            targetFormData = {};
            targetFormData["code"] = 1;
            targetFormData["data"] = msg["data"];
            targetFormData["msg"] = msg["msg"];
        }
        return false;
    });
    //隐藏节点：终点person表单
    form.on('submit(targetPanelSubmitPerson)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field));
        targetFormData = {};
        targetFormData["code"] = 1;
        targetFormData["data"] = data.field;
        targetFormData["msg"] = "OK";
        return false;
    });
    //隐藏节点：终点venue表单
    form.on('submit(targetPanelSubmitVenue)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field));
        targetFormData = {};
        targetFormData["code"] = 1;
        targetFormData["data"] = data.field;
        targetFormData["msg"] = "OK";
        return false;
    });
});

//            //先调用查询功能，检查数据库中是否有相同的记录，todo 需要设计用那些字段来进行匹配搜索（在后台选择用那些数据，前台返回的是form中的所有name）
//            var formValue = msg["data"];
//            var foundRecords;
//            $.ajax({
//                type: 'POST'
//                ,url: '/search/result/'
//                ,data: JSON.stringify(formValue)
//                ,dataType : "json"
//    //            ,headers: {'Content-Type': 'application/json'}
//                ,contentType: "application/json"
//                ,async:false
//                ,beforeSend: function(){
//                    console.log(formValue);
//                }
//                ,success: function(result,status,xhr) {//配置一个透明的确认框，显示搜索结果
//                    if (result["code"] < 0){
//                        layer.msg("后台查询错误！<br>" + result["msg"]);
//                    }else{
//                        foundRecords = result;
//                    }
//                    return false;
//                }
//                ,error: function(xhr,status,error){//如果请求失败要运行的函数
//                    layer.msg("请求查询失败，与数据库服务器断开连接，请稍后再试。", {
//                        time: 20000, //20s后自动关闭
//                        btn: ['ok'],
//                        icon:5
//                    });
//                    console.log(error);
//                }
//                ,complete: function(xhr,status){//完成时的操作，success和error之后
//                    console.log(status);
//                }
//            });
//            if (foundRecords == undefined){
//                return false;
//            }
//            // 若有匹配记录，则弹出窗口对比各条记录的差异，提供选项：创建记录、替换现有记录、取消
//
//            // 若无匹配，则写入数据库，并根据写入结果显示信息
//            if (foundRecords["code"] == 0){

//            }


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

    //表单验证:参数是name：value形式,todo 这里先假设所返回数据的key和form中的name一致
function verifyPubInfo(data, currentAuthors) {
    var msg = {status: -1, msg: "", data: ""};
    var pubType = new Number(data["node_type"])
        ,mandatory = formSettings[pubType]["mandatory"]
        ,others = formSettings[pubType]["others"];
    var msg = {"status": 2, "msg":""};
    var processedData = {};
    console.log("开始验证必填字段");
    for (i=0;i<mandatory.length;i++) {//判断必填字段
        var valueNames = [];
        if (mandatory[i]==0) { //作者单独判断
            var tmpMsg = verifyAuthor(currentAuthors);
            if (tmpMsg["status"]<0) {
                console.log("必填：作者验证失败");
                msg["status"] = tmpMsg["status"];
                msg["msg"] = tmpMsg["msg"];
                break;
            }else{
                console.log("必填：作者验证成功");
                processedData["author"] = currentAuthors;
                continue;
            }
        }else if (mandatory[i]==6) { //pages
            console.log("验证pages");
            valueNames = ["pages1","pages2"];
        }else {
            console.log("验证：" + contentStringName[mandatory[i]]);
            valueNames = [contentStringName[mandatory[i]]];
        }
        var validFlag = true;
        for (j=0;j<valueNames.length;j++) {
            console.log("开始验证必填字段：" + valueNames[j]);
            if (data.hasOwnProperty(valueNames[j])) {//判断表单中是否有字段
                console.log("开始验证表单内容：" + valueNames[j] + ",值：" + data[valueNames[j]]);
                msg = verifyFieldValue(valueNames[j], data[valueNames[j]]); // 判断是否为空及数字字段验证
                if (msg["status"] < 1) {//表单填写错误
                    console.log("表单填写错误");
                    validFlag = false;
                    break;
                }else if (msg["status"]==-2) {
                    console.log("不存在此字段");
                    msg["msg"] += " 不存在此字段";
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
    if (msg["status"]<1) {
        console.log("必填字段验证失败，退出验证");
        return msg;
    }
    console.log("开始验证选填字段");
    for (i=0;i<others.length;i++) {//判断选填字段
        if (others[i]==0) { //作者单独判断
            var tmpMsg = verifyAuthor(currentAuthors);
            if (tmpMsg["status"]<0) {
                console.log("选填：作者验证失败");
                msg["status"] = tmpMsg["status"];
                msg["msg"] = tmpMsg["msg"];
                break;
            }else{
                console.log("必填：作者验证成功");
                processedData["author"] = currentAuthors;
                continue;
            }
        }else if (others[i]==6) { //pages
            console.log("选：pages");
            valueNames = ["pages1","pages2"];
        }else {
            console.log("选：" + contentStringName[others[i]]);
            valueNames = [contentStringName[others[i]]];
        }
        for (j=0;j<valueNames.length;j++) {
            if (data.hasOwnProperty(valueNames[j])) {//判断表单中是否有字段
                console.log("选：开始验证：" + valueNames[j] + ",值：" + data[valueNames[j]]);
                msgMsg = verifyFieldValue(valueNames[j], data[valueNames[j]]); // 判断是否为空及数字字段验证
                if (msgMsg["status"]==-1) {//表单填写错误
                    console.log("选：表单填写错误");
                    msg["msg"] += "\n Field [" + valueNames[j] + "] should be number.";
                    msg["status"] = -1;
                }else if (msgMsg["status"]==-2) {
                    console.log("选：字段名不存在");
                    msg["msg"] += "\n Field [" + valueNames[j] + "] 不存在";
                    msg["status"] = -1;
                }else {//填写正确 或 为空
                    console.log("选：验证正确");
                    processedData[valueNames[j]] = data[valueNames[j]];
                }
            }else {
                console.log("选：字段名不存在");
                msg["msg"] += "\n Missing field [" + valueNames[j] + "]";
            }
            if ( msg["status"] < 0) {
                console.log("选：验证失败");
                break;
            }
        }

        if ( msg["status"] < 0) {
            break;
        }
    }
    processedData["node_type"] = data["node_type"];
    msg["data"] = processedData;

    console.log("退出验证");
    return msg;
}

    //判断表单中字段:0 字段空；-1 应为数字的字段值非数字；1正常;-2 字段名不存在
function verifyFieldValue(fieldName, valueInForm) {
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
                return {"msg":fieldName + ":Empty string or number 0", "status": 0};
            }
        }
    }else { // string field
        if (valueInForm == "") {
            return {"msg":"Field [" + fieldName + "] is empty", "status": 0};
        }
    }
    return {"msg":"OK.", "status": 1};
}
