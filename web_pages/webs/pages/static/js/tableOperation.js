//表格（1）"增加文献表格"中的"作者列表表格"
//重载
function reloadAuthorTable(currentAuthors, tableId, table){
    var $ = layui.$
        ,demoReload = $('#' + tableId);

    //执行重载
    table.reload(tableId, {
        where: {
            currentData: JSON.stringify(currentAuthors)
        }
    });
}
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
                reloadAuthorTable(currentAuthors, tableId, table);
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
        ,rowIndex = obj.data.LAY_TABLE_INDEX //所在行LAY_TABLE_INDEX下标
        ,field = obj.field; //得到字段
    //获取在currentAuthors中下标
    for (i=0;i<currentAuthors.length;i++) {
        if (currentAuthors[i]["LAY_TABLE_INDEX"]==rowIndex) {
            rowIndex = i;
            break;
        }
    }
    if (field == "ranking") {
        var tmpAuthors = deepClone(currentAuthors);
        tmpAuthors.splice(rowIndex);
        if (tmpAuthors == false) {
            value = validRanking(value);
            if (isNaN(value)) {
                layer.msg("作者排名需为非负整数。");
                resetRanking(rowIndex, currentAuthors[rowIndex]);
            }else {
                if (currentRankings.indexOf(value)) {
                    later.msg("作者排名不能重复");
                    resetRanking(rowIndex, currentAuthors[rowIndex]);
                }else {
                    currentAuthors[rowIndex][field] = value;
                }
            }
        }else {
            var currentRankings = extractRankings(tmpAuthors);
            if (currentRankings == false) {
                console.log("解析表格中排名信息错误");
            }else {
                value = validRanking(value);
                if (isNaN(value )) {
                    layer.msg("作者排名需为非负整数。");
                    resetRanking(rowIndex, currentAuthors[rowIndex]);
                }else {
                    if (currentRankings.indexOf(value)) {
                        later.msg("作者排名不能重复");
                        resetRanking(rowIndex, currentAuthors[rowIndex]);
                    }else {
                        currentAuthors[rowIndex][field] = value;
                    }
                }
            }
        }
    }else {
        currentAuthors[rowIndex][field] = value;
    }
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


