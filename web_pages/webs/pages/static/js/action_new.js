
var sideBarItemIds = ['1-1', '1-2', '2-1', '2-2', '3-1', '3-2', '4-1', '4-2'];
var titleLength = 4;
var charSharp = '#';
var collapse = 'collapse';

function clickSideBar(argId){
    var ele = argId;
    if (ele != undefined) {
        ele = ele.replace(collapse, "");
        var index = sideBarItemIds.indexOf(ele); // 点击的标签在sideBarItemIds中的序号
        if (index > -1) {
            if (index%2 == 0) { //点击每组的第一个时，标题上的active变化
                var idd = index / 2;
                var theId = collapse + sideBarItemIds[index] + "-title";
                for (var i=0;i<titleLength;i++) {
                    var theOtherId = collapse + (i+1) + "-1-title";
                    if (document.getElementById(theId) != null) {
                        var act = document.getElementById(theOtherId).className;

                        if (idd == i) { // 置为active
                            if (act.indexOf('active') == -1) {
                                act = act + ' active';
                                document.getElementById(theOtherId).className = act;
                            }
                        }else { //取消active
                            if (act.indexOf('active') > -1) {
                                act = act.replace('active','');
                                document.getElementById(theOtherId).className = act;
                            }
                        }
                    }
                }
            }
            for (var i=0;i<sideBarItemIds.length;i++) {
                 var theId = collapse + sideBarItemIds[i];
                 if (index != i) {
                    if (document.getElementById(theId)!=null) {
                        var act = document.getElementById(theId).className;
                        if (act.indexOf('active')>-1) {
                            act = act.replace('active','');
                            document.getElementById(theId).className =  act;
                        }
                        if (document.getElementById(theId + '-content') != null ) {
                            document.getElementById(theId + '-content').style = 'display:none';
                        }
                    }
                 }else {
                    if (document.getElementById(theId)!=null) {
                        var act = document.getElementById(theId).className;
                        if (act.indexOf('active')==-1) {
                            document.getElementById(theId).className =  act + ' active';
                        }
                        if (document.getElementById(theId + '-content') != null ) {
                            document.getElementById(theId + '-content').style = 'display:auto';
                        }
                    }
                 }
            }
        }
    }
}


function collapseSideBar(argId){
    for (var i=1;i<=sideBarListLength;i++) {
        var theVar = charSharp + collapse + i;
        if (argId==theVar) {
            $(argId).collapse('show');
        }else {
            $(theVar).collapse('hide');
        }
    }
}
