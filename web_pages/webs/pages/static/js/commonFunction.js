
//1. 将长句子分成多行
function yourSplit(N,string){
    var app = string.split(' '),
        arrayApp = [],
        stringApp = "";
    app.forEach(function(sentence,index){
        stringApp += sentence+' ';

        if ( (index+1)%N === 0){
            arrayApp.push(stringApp);
            stringApp='';
        }else if(app.length===index+1 && stringApp!==''){
            arrayApp.push(stringApp);
            stringApp='';
        }
    });
    var result = "";
    for (j=0; j<arrayApp.length-1;j++) {
        result += arrayApp[j] + "\n";
    }
    result += arrayApp[arrayApp.length-1];
    return result;

};

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
//8.取消作者表格中ranking值输入
function resetRanking(ranking, value) {
    var tr = $("[data-index='" + new Number(ranking).toString() + "']").children("[data-field='ranking']").children("input").val(value["ranking"]);
    var tr = $("[data-index='" + new Number(ranking).toString() + "']").children("[data-field='ranking']").children("div").text(value["ranking"]);
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
