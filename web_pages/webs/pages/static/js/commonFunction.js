
//1. 将长句子分成多行
var yourSplit = function(N,string){
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

//4.作者表格中提取排名值
function extractRankings(info) {
    if (info!=undefined && info!=null) {
        var rankings = [];
        var counter = 0;
        if (isArray(info)) {
            info.forEach(function(item){
                ranking = validRanking(item["ranking"]);
                if (isNaN(ranking)) {
                    console.log("当前输入的ranking值不是数字:" + JSON.stringify(item));
                }else {
                    rankings[counter] = ranking;
                    counter++;
                }
            });
        }else {
            ranking = validRanking(info["ranking"]);
            if (isNaN(ranking)) {
                console.log("当前输入的ranking值不是数字:" + JSON.stringify(info));
            }else {
                rankings[counter] = ranking;
                counter++;
            }
        }
        return rankings;
    }else {
        return false;
    }
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
