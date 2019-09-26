
// #1 home 页面的内容检查
layui.use(['form', 'layedit'], function(){
    var form = layui.form
        , layer = layui.layer
        , layedit = layui.layedit;

    // 验证规则
    form.verify({
        search_content_home: function(value){
            if (value.length <= 0){
                return "请输入搜索内容"
            }
        },
        node_type: function(value){
            if (value == ""){
                return "请选择搜索类型"
            }
        }
    });


    form.on('submit(search_btn)', function(data){
        layer.alert(JSON.stringify(data.field), {
            title: "最终提交的信息"
        })
        return false;
    });

});

/*
    #2 搜索结果页面, 高级搜索提交按钮+结果表格的显示，
*/
layui.use(['form', 'element', 'laydate', 'table'], function(){
    var $ = layui.jquery
        , element = layui.element
        , form = layui.form
        , table = layui.table
        , layer = layui.layer;
    //搜索按钮的提交1）高级搜索按钮,及搜索结果
    form.on('submit(adv_search_btn)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field)); // 这里已经转成Json了,data.field也是dict，
        msg = verifySearchCondition(data.field); // 只要不是所有field都是空，就可以搜索
        if (msg["status"]<1) {
            layer.msg(msg["msg"]);
            console.log("结束验证，验证失败");
        }else{
            console.log("结束验证，验证正确");
            // 首先要请求有多少数据满足条件
            retrieveSearchResult(msg["data"]);
        }
        return false;
    });
    //搜索按钮的提交2）结果页面的简化搜索按钮,及搜索结果
    form.on('submit(search_btn_in_result)', function(data){
        console.log("提交的表单数据：" + JSON.stringify(data.field)); // 这里已经转成Json了,data.field也是dict，
        if (!data.field.hasOwnProperty("search_content_in_result") || data.field["search_content_in_result"] == ""){
            layer.alert("搜索条件不能为空！");
        }else{
            var conditions = {"title": data.field["search_content_in_result"]};
            retrieveSearchResult(conditions);
        }
        return false;
    });
});

/*
高级搜索框中起止时间
*/
layui.use(['element', 'laydate'], function(){
    var $ = layui.jquery
        , element = layui.element
        , laydate = layui.laydate;
    var myDate = new Date();
    //高级搜索(1):起始年范围, 限定可选时间
    var ins2 = laydate.render({
        elem: '#startTime1'
        ,type: 'year'
        ,range: false
        ,max: myDate.toLocaleDateString()     //获取当前日期
        ,min: '1900-01-01'
        ,showBottom: true
        ,change: function(value, date, endDate){
            var endTime = document.getElementById('endTime1').value;
            if (endTime != undefined && endTime != ""){
                if (endTime < value){
                    //不能更早
                    ins2.hint('起始时间不可晚于终止时间');
                }else {
                    $("#startTime1").val(value);
                    if($(".layui-laydate").length){
                        $(".layui-laydate").remove();
                    }
                }
            }
        }
    });
    //高级搜索(2):终止年范围, 限定可选时间
    var ins1 = laydate.render({
            elem: '#endTime1'
            ,type: 'year'
            ,range: false
            ,max: myDate.toLocaleDateString()     //获取当前日期
            ,min: '1900-01-01'
            ,showBottom: true
            ,isInitValue: false
            ,value: myDate.getFullYear()
            ,change: function(value, date, endDate){
                var $ = jQuery = layui.$;
                var startTime = document.getElementById('startTime1').value;
                if (startTime != "" && startTime > value){
                    //不能更早
                    ins1.hint('终止时间不可超过起始时间');
                }else {
                    $("#endTime1").val(value);
                    if($(".layui-laydate").length){
                        $(".layui-laydate").remove();
                    }
                }
            }
        });
});

/*
监听表格中工具栏 view和bib已实现 todo 修改具体实现方法--details和archive等
*/
layui.use(['table', 'layer'], function(){
    var $ = layui.jquery
        , layer = layui.layer
        , table = layui.table

    table.on('tool(search_result_table)', function(obj){
        var data = obj.data;
        if(obj.event === 'View'){
            layer.msg('ID：'+ data.id + ' 的查看操作');
//            打开新页面显示pdf
            if (data.hasOwnProperty("id")){
                var url = data["id"];
                window.open("show-pdf?id=" + url, '_blank')
            }else{
                layer.alert('本文件缺少id，无法打开文件');
            }
        } else if(obj.event === 'Bib'){
            layer.open({
                type: 1
                ,title: "Export bib" //不显示标题栏
                ,closeBtn: false
                ,area: '400px;'
                ,shade: 0.8
                ,id: 'bib_popup' //设定一个id，防止重复弹出
                ,btn: ['OK']
                ,btnAlign: 'c'
                ,moveType: 1 //拖拽模式，0或者1
                ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">' +
                    wrapToBib(data) + '</div>'
                ,success: function(layero){
                    console.log("弹出bib");
                }
            });
        } else if(obj.event === 'edit'){
            layer.alert('编辑行：<br>'+ JSON.stringify(data))
        }
    });
});

/*
头工具栏事件,导出bib文件 todo 修改头部按钮功能-加入购物车
*/
layui.use(['table', 'element'], function(){
    var $ = layui.jquery
        , layer = layui.layer
        , table = layui.table
    table.on('toolbar(search_result_table)', function(obj){
        var checkStatus = table.checkStatus(obj.config.id);
        switch(obj.event){
            case 'addCart':
                var data = checkStatus.data;
                layer.msg("还没实现");
            break;
            case "exportBibs":
                var data = checkStatus.data;
                var result = "";
                for (var i = 0; i < data.length;i++){
                    result += "<br>  " + wrapToBib(data[i]);
                }
//                layer.open({
//                    type: 1
//                    ,title: "Export bib" //不显示标题栏
//                    ,closeBtn: false
//                    ,area: '400px;'
//                    ,shade: 0.8
//                    ,id: 'bib_popup' //设定一个id，防止重复弹出
//                    ,btn: ['OK']
//                    ,btnAlign: 'c'
//                    ,moveType: 1 //拖拽模式，0或者1
//                    ,content: '<div style="padding: 50px; line-height: 22px; background-color: #393D49; color: #fff; font-weight: 300;">' +
//                        result + '</div>'
//                    ,success: function(layero){
//                        console.log("弹出bib");
//                    }
//                });

                var content = result.replace(/<br>/g, "\n");
                var data = new Blob([content],{type:"text/plain;charset=UTF-8"});
                var downloadUrl = window.URL.createObjectURL(data);
                var anchor = document.createElement("a");
                anchor.href = downloadUrl;
                anchor.download = "bibs.txt";
                anchor.click();
                window.URL.revokeObjectURL(data);
            break;
            //自定义头工具栏右侧图标 - 提示
            case 'LAYTABLE_TIPS':
                layer.alert('这是工具栏右侧自定义的一个图标按钮');
            break;
        };
    });
});

// #3 高级搜索/简单搜索的切换过程
layui.use('form', function(){
    var $ = layui.$;
    $('#adv_search_btn_result').click(function(){
        // 显示高级搜索框
        $('#btn_adv').attr("style", "display:auto");
        $('#paper_type_adv').attr("style", "display:auto");
        $('#index_adv').attr("style", "display:auto");
        $('#author_adv').attr("style", "display:auto");
        $('#year_adv').attr("style", "display:auto");
        $('#keyword_adv').attr("style", "display:auto");
        //隐藏当前按钮
        $('#normal_search').attr("style", "display:none");
        //输入框的值置空
//        document.getElementById('search_content').value = "";
        document.getElementById('search_form_result').reset();
    });
    $('#search_simple').click(function(){
        // 显示高级搜索框
        $('#btn_adv').attr("style", "display:none");
        $('#paper_type_adv').attr("style", "display:none");
        $('#index_adv').attr("style", "display:none");
        $('#author_adv').attr("style", "display:none");
        $('#year_adv').attr("style", "display:none");
        $('#keyword_adv').attr("style", "display:none");
        //隐藏当前按钮
        $('#normal_search').attr("style", "display:auto");
        //触发重置表格
        document.getElementById('search_form_result').reset();
    });
});

// # 5 鼠标悬停事件
function showBibTips(t){
    layui.use('layer', function(){
        var $ = layui.$, layer = layui.layer;
        layer.tips("导出当前页面选择文献的bib", '#exportBibs', {time: 1000});
    });
}


// 支持函数
    // 依据搜索条件获取数据
function retrieveSearchResult(queryInfo){
    layui.use(['form', 'element', 'laydate', 'table'],function(){
        var $ = layui.jquery
            , form = layui.form
            , table = layui.table
            , layer = layui.layer;
        $.ajax({
            type: 'POST'
            ,url: 'search-count/'
            ,data: JSON.stringify(queryInfo)
            ,dataType : "json"
//                ,headers: {'Content-Type': 'application/json',"X-CSRFToken":csrftoken}
            ,contentType: "application/json"
            ,beforeSend: function(){
                console.log("发送请求获得数据个数");
            }
            ,success: function(result,status,xhr) {
                console.log("ok，个数为：" + JSON.stringify(result));
                var pp = 0;
                if (result["status"] > 0){
                    console.log("验证成功");
                    pp = result["count"];
                }else{
                    console.log("验证失败");
                    return false;
                }

                if (pp <= 0){
                    console.log("没有数据");
                    return false;
                }
                var parameters = queryInfo;
                parameters["count"] = pp;
                //要填充数据表格（搜索结果）
                table.render({ //todo 这里发现排序的功能只能在当前页内进行，需要再研究一下
                    elem: '#search_result_table'
                    ,method: 'post'
                    ,height: 'full'
                    ,url: '/search/result/'
                    ,where: {param: JSON.stringify(parameters)}
                    ,toolbar: '#toolbarSearchResult' //开启头部工具栏，并为其绑定左侧模板
                    ,defaultToolbar: ['filter', 'exports', 'print', { //自定义头部工具栏右侧图标。如无需自定义，去除该参数即可
                        title: '提示'
                        ,layEvent: 'LAYTABLE_TIPS'
                        ,icon: 'layui-icon-tips'
                    }]
                    ,cols: [[
                        {type:'checkbox', width:80}
                        ,{field:'year', title:'Year', width:80, sort: true, edit: 'text'}
                        ,{field:'title', title:'Title', width:300, edit: 'text'}
                        ,{field:'author', title:'Authors', width:200, sort: true, edit: 'text'}
                        ,{field:'journal', title:'Venue', width:200, sort: true, edit: 'text'}
                        ,{field:'paperTypeEdit', title:'Type', width:90, sort: true, edit: 'text'}
                        ,{width:300, align:'center', toolbar: '#bar_search_result'}
                    ]]
                    ,id: 'authorTable'
                    ,page: true
                    ,limit: 10
                    ,done: function(res, curr, count){
                        console.log("result loaded"); // todo 这里要实现表格中元素自动调节高度
//                            var ell = document.getElementsByClassName("layui-table-cell");
//                            for (var i=0;i<ell.length;i++){
//                                ell[i].style.overflow = "visible";
//                                ell[i].style['text-overflow'] = "inherit";
//                                ell[i].style['white-space'] = "normal";
//                                ell[i].style['word-break'] = "break-all";
//                                ell[i].style['height'] = "auto!important";
//                                ell[i].style['line-height'] = "auto!important";
//                            }
//                            console.log("ff");
                    }
                });
            }
            ,error: function(xhr,status,error){
                //如果请求失败要运行的函数
                console.log("发送请求失败。");
                return -2;
            }
            ,complete: function(xhr,status){
                //完成时的操作，success和error之后
                console.log(status)
            }
        });
    });
}
    //检查提交的数据是否有效，并处理数据以满足发送查询请求的要求
function verifySearchCondition(data, data_type){
    msg = {"status": 0, "msg":"no fields are given", "data":{}};
    if (data.length != undefined){
        msg["status"] = -1;
        msg["msg"] = "变量不是dict";
    }else{
        var data_new = {};
        var title = data["title"]
            , startTime = data["startTime1"]
            , endTime = data["endTime1"]
            , author = data["author"]
            , paperIndex = data["paperIndexing1"]
            , paperType = data["node_type"];
        var myDate = new Date();
        myDate = myDate.getFullYear();
        if (!(title == undefined || title == "")){
            data_new["title"] = title;
        }
        if (!(startTime == undefined || startTime == "")){
            data_new["startTime"] = startTime;
        }
        if (!(endTime == undefined || endTime == "")){
            data_new["endTime"] = endTime;
        }
        if (!(author == undefined || author == "")){
            data_new["author"] = author;
        }
        if (!(paperIndex == undefined || paperIndex == "")){
            data_new["paperIndex"] = paperIndex;
        }
        if (!(paperType == undefined || paperType == "")){
            data_new["node_type"] = paperType;
        }
        for (var i in data_new){
            msg["status"] = 1;
            msg["msg"] = "done";
            msg["data"] = data_new;
            break;
        }
    }
    return msg;
}

    // 将搜索结果数据json，转化为字符串，以显示或供下载
function wrapToBib(data){

    var bib = "@";
    if (data.hasOwnProperty("paperTypeEdit")) {
        bib = bib + data["paperTypeEdit"] + "{";
    }else{
        bib = "";
        return bib; // 不能缺少文章类型
    }
    if (data.hasOwnProperty("id")) {
        bib = bib + data["id"] + ",<br>    ";
    }else{
        bib = bib + ",<br>    ";
    }

    if (data.hasOwnProperty("title")) {
        bib = bib + "title={" + data["title"] + "},<br>    ";
    }
    if (data.hasOwnProperty("journal")) {
        bib = bib + "journal={" + data["journal"] + "},<br>    ";
    }

    if (data.hasOwnProperty("year")) {
        bib = bib + "year={" + data["year"] + "},<br>    ";
    }
    if (data.hasOwnProperty("author")) {
        bib = bib + "author={" + data["author"] + "},<br>    ";
    }
    if (data.hasOwnProperty("month")) {
        bib = bib + "month={" + data["month"] + "},<br>    ";
    }
    if (data.hasOwnProperty("volume")) {
        bib = bib + "volume={" + data["volume"] + "},<br>    ";
    }
    if (data.hasOwnProperty("number")) {
        bib = bib + "number={" + data["number"] + "},<br>    ";
    }

    if (data.hasOwnProperty("booktitle")) {
        bib = bib + "booktitle={" + data["booktitle"] + "},<br>    ";
    }
    if (data.hasOwnProperty("pages")) {
        bib = bib + "pages={" + data["pages"] + "},<br>    ";
    }
    if (data.hasOwnProperty("editor")) {
        bib = bib + "editor={" + data["editor"] + "},<br>    ";
    }
    if (data.hasOwnProperty("edition")) {
        bib = bib + "edition={" + data["edition"] + "},<br>    ";
    }
    if (data.hasOwnProperty("chapter")) {
        bib = bib + "chapter={" + data["chapter"] + "},<br>    ";
    }

    if (data.hasOwnProperty("series")) {
        bib = bib + "series={" + data["series"] + "},<br>    ";
    }
    if (data.hasOwnProperty("school")) {
        bib = bib + "school={" + data["school"] + "},<br>    ";
    }
    if (data.hasOwnProperty("address")) {
        bib = bib + "address={" + data["address"] + "},<br>    ";
    }

    if (data.hasOwnProperty("publisher")) {
        bib = bib + "publisher={" + data["publisher"] + "},<br>    ";
    }
    if (data.hasOwnProperty("organization")) {
        bib = bib + "organization={" + data["organization"] + "},<br>    ";
    }
    if (data.hasOwnProperty("institution")) {
        bib = bib + "institution={" + data["institution"] + "},<br>    ";
    }

    if (data.hasOwnProperty("howpublished")) {
        bib = bib + "howpublished={" + data["howpublished"] + "},<br>    ";
    }
    if (data.hasOwnProperty("note")) {
        bib = bib + "note={" + data["note"] + "},<br>    ";
    }
    bib =
    bib = bib + "}"
    return bib;

}
