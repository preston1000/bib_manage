// 新增文献面板

layui.use(['form','table', 'layer'], function(){
    var table = layui.table
        ,$ = layui.jquery
        ,layer = layui.layer
        ,form = layui.form;
    form.on("submit(verifyFormSubmit)", function(data){
        var params = {"username": data.field["editUser"], "pwd": data.field["editPwd"]};
        var pp = active["sendAuth"].call(params);
        return false;
    });



    var collapseState = $("#addOrEditPub").attr("class");
    if (collapseState == undefined) {
    }else{
        if (collapseState.indexOf("collapse in")>-1) {//展开时：1）编辑模式：清空内容，不折叠；新增模式：关闭，可不清空内容
            if (addOrEditPanelState==1) {//add
                $("#addOrEditPub").attr("class", collapseState.replace('collapse in', "collapse"));
            }else if (addOrEditPanelState==2){//edit
                toggleEditPanel(0);
                form.render();
                addOrEditPanelState = 1;
            }else {
                console.log("未知文献详情面板状态");
            }
        }else{//关闭时，展开，清空内容
            toggleEditPanel(0);
            form.render();
            $("#addOrEditPub").attr("class", collapseState.replace('collapse', "collapse in"));
        }
    }
});


// 点击高级搜索按钮：显示/关闭搜索框，关闭操作文献按钮
function clickAdvanceSearchButton(){
    var currentState = toggleAdvanceSearch(document.getElementById("advanceSearchButton").innerHTML, -1);
    if (currentState == 1) {//强制另一个关闭
        togglePubOperation("取消操作", 1);//-1
        foldEditPanel();
    }
}
// 点击高级搜索按钮：显示/关闭搜索框，关闭操作文献按钮
function clickEditPubButton(){
    var currentState = togglePubOperation(document.getElementById("addPublicationButton").innerHTML, -1);
    if (currentState == 1) {//强制另一个关闭
        toggleAdvanceSearch("收起", 1);//-1
    }
}

// 转换展开/收起状态，forceCollapse>0强制关闭，<0不强制关闭
function changeCollapseState(itemId, forceCollapse){
    var operatePub = document.getElementById(itemId);
    if (operatePub.className.includes("collapse in"))  {//展开->收起
        operatePub.className = "collapse";
    }else{//收起->展开
        if (forceCollapse < 0) {
            operatePub.className = "collapse in";
        }
    }
}
// "新增/编辑文献"表格--按钮（高级搜索）文字+展开/收起(givenHtml:指定要变换状态之前的内容)
function toggleAdvanceSearch(givenHtml, forceCollapse){
    var currentState = -1; //点击后状态：-1：未定义；0：未展开；1：展开
    if (givenHtml<0) {
        givenHtml = document.getElementById("advanceSearchButton").innerHTML;
    }
    if (givenHtml == "高级搜索") { // 收起状态，显示：高级搜索
        document.getElementById("advanceSearchButton").innerHTML = "收起";
        currentState = 1;
    }else { //展开状态，显示：收起
        document.getElementById("advanceSearchButton").innerHTML = "高级搜索";
        currentState = 0;
    }
    changeCollapseState("operatePubs", forceCollapse);
    return currentState;
}
// "新增/编辑文献"表格--按钮（操作文献）文字+展开/收起
function togglePubOperation(givenHtml, forceCollapse){
    var currentState = -1; //点击后状态：-1：未定义；0：未展开；1：展开
    if (givenHtml<0) {
        givenHtml = document.getElementById("addPublicationButton").innerHTML;
    }
    if (givenHtml == "操作文献") {//显示：（未展开）
        document.getElementById("addPublicationButton").innerHTML = "取消操作";
        currentState = 1;
    }else {//显示：（展开）
        document.getElementById("addPublicationButton").innerHTML = "操作文献";
        currentState = 0;
    }
    changeCollapseState("advanceSearch", forceCollapse);
    return currentState;
}
// "新增/编辑文献"表格--关闭文献编辑面板并重置
function foldEditPanel() {
    var operatePub = document.getElementById("addOrEditPub");
    if (operatePub.className.includes("collapse in"))  {
        operatePub.className = "collapse";
    }
    toggleEditPanel(0);
    //重置文献类型下拉框
    $("button[lay-filter='resetPubPanel']").trigger("click");
}
//"新增/编辑文献"表格--关闭/开启文献编辑面板中各Item
function toggleEditPanel(formSettings, contentStringName, value, formPrefix) {
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