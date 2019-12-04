
var tableData = [],
    tableIndex = [];
var tableProcessed = [],
    tableProcessedIndex = [];
var tableProcessedWords = [],
    tableProcessedWordsIndex = [];
var counterToReload = 0
    ,counterToReloadLimit = 0;;
var stationTable;



layui.use(['table', 'upload'], function(){
  var table = layui.table
        ,upload = layui.upload;

  stationTable = table.render({
        elem: '#placeDetails'
//        ,url:'/test/table/demo1.json'
        ,data: []
        ,toolbar: '#toolbarMap' //开启头部工具栏，并为其绑定左侧模板
        ,defaultToolbar: ['filter', 'exports', 'print', { //自定义头部工具栏右侧图标。如无需自定义，去除该参数即可
            title: '提示'
            ,layEvent: 'LAYTABLE_TIPS'
            ,icon: 'layui-icon-tips'
        }]
        ,title: 'detailsOfPlaces'
        ,cols: [[
            {type: 'checkbox', fixed: 'left'}
            ,{field:'index', title:'ID', width:60, fixed: 'left', unresize: true, sort: true}
            ,{field:'address', title:'地点', width:200, edit: 'text'}
            ,{field:'province', title:'省份', width:100, edit: 'text', sort: true}
            ,{field:'city', title:'城市', width:100, edit: 'text', sort: true}
            ,{field:'district', title:'区县', width:100, edit: 'text', sort: true}
            ,{field:'street', title:'街道', width:100, edit: 'text', sort: true}
            ,{field:'roomNum', title:'门牌号', width:100, edit: 'text', sort: true}
            ,{field:'line', title:'线路', width:100, edit: 'text', sort: true}
            ,{field:'next', title:'下一站', width:100}
            ,{field:'coordinates', title:'坐标', width:200, edit: 'text', sort: true}
        ]]
        ,page: true
        ,limit:10
    });
    upload.render({
        elem: '#upload'
        ,url: '/parseExcelStations/'
        ,accept: 'file' //普通文件
        ,exts: 'xls|xlsx'
        ,done: function(res){
            console.log(res);
            tableData = res["data"];
            for (var i = 0; i < tableData.length; i++){
                tableIndex.push(tableData[i]["index"]);
            }
            stationTable.reload({
                data: res["data"]
            });
            tableProcessedIndex = [];
            tableProcessed = [];
        }
    });
    //头工具栏事件
    table.on('toolbar(placeDetails)', function(obj){
        var checkStatus = table.checkStatus(obj.config.id);
        switch(obj.event){
            case 'download':
                var data = checkStatus.data;
                table.exportFile(stationTable.config.id, data, 'xls');
                break;
            case 'resolve':
                var data = checkStatus.data;
                counterToReloadLimit = data.length;
                if (counterToReloadLimit > 0){
                    // 创建地址解析器实例
                    var myGeo = new BMap.Geocoder();
                    for (var index = 0;index<data.length;index++){
                        getPlaceCoordinates(myGeo, data[index]);
                    }
                }
                break;
            case 'getWords':
//                var data = checkStatus.data;
                var data = tableProcessed;
                counterToReloadLimit = data.length;
                if (counterToReloadLimit > 0){
                // 创建地址解析器实例
                    var myGeo = new BMap.Geocoder();
                    for (var index = 0;index < counterToReloadLimit;index++){
                        getPlaceInfo(myGeo, data[index]);
                    }
                }
                break;

            //自定义头工具栏右侧图标 - 提示
            case 'LAYTABLE_TIPS':
                layer.alert('这是工具栏右侧自定义的一个图标按钮');
                break;
        };
    });
});

//获取坐标
function getPlaceCoordinates(geo, info){
    var place = info["address"]
        ,city = info["city"];

    geo.getPoint(place, function(point){
        if (point) {
            counterToReload += 1;
            console.log("解析后地点：" );
            console.log(point);
            var tmpIndex = tableProcessedIndex.indexOf(info["index"]);
            if (tmpIndex == -1){
                var tmpInfo = info;
                tmpInfo["coordinates"] = JSON.stringify(point); //{index: info["index"], address: place, coordinates: JSON.stringify(point), city: info["city"]};
                tableProcessed.push(tmpInfo);
                tableProcessedIndex.push(info["index"]);
            }else{
                tableProcessed[tmpIndex]["coordinates"] = JSON.stringify(point);
            }
            if (counterToReload == counterToReloadLimit & counterToReloadLimit > 0){//所有选择的地点全都解析完了
                // 将解析后的数据与原数据合并，然后进行表格重载
                for (var i =0; i < tableProcessedIndex.length; i++){
                    var tmpp = tableIndex.indexOf(tableProcessedIndex[i]);
                    tableData[tmpp]["coordinates"] = tableProcessed[i]["coordinates"];
                }
                stationTable.reload({
                    data: tableData
                });
                counterToReload = 0;
                counterToReloadLimit = 0;
//                tableProcessed = [];
//                tableProcessedIndex = [];
                document.getElementById("getWords").click();
            }
        }else{
            console.log("您选择地址没有解析到结果!");
        }
    }, city);
}

//地址分词
function getPlaceInfo(geo, info){
    var place = info["coordinates"];
    place = JSON.parse(place);
    var city = info["city"];
    var tmpPlace = new BMap.Point(place["lng"],place["lat"]);
    geo.getLocation(tmpPlace, function(point){
        if (point) {
            counterToReload += 1;
            console.log("解析后地点：" );
            console.log(point);

//坐标转换完之后的回调函数

var bm = new BMap.Map("allmap");
bm.centerAndZoom(tmpPlace, 16);
var marker = new BMap.Marker(tmpPlace);
bm.addOverlay(marker);
//
//var arr2 = GPS.bd_decrypt(place["lat"], place["lng"]);
//var tmpPlaceP = new BMap.Point(arr2["lon"],arr2["lat"]);
//
//   translateCallback = function (data){
//      if(data.status === 0) {
//        var marker = new BMap.Marker(data.points[0]);
//        bm.addOverlay(marker);
//        var label = new BMap.Label("地点",{offset:new BMap.Size(20,-10)});
//        marker.setLabel(label); //添加百度label
//        bm.setCenter(data.points[0]);
//      }
//    }
//    var convertor = new BMap.Convertor();
//    var pointArr = [];
//    pointArr.push(tmpPlaceP);
//    convertor.translate(pointArr, 1, 5, translateCallback);

            var addComp = point.addressComponents;
//			alert(addComp.province + ", " + addComp.city + ", " + addComp.district + ", " + addComp.street + ", " + addComp.streetNumber)

            var tmpIndex = tableProcessedWordsIndex.indexOf(info["index"]);
            if (tmpIndex == -1){
                var tmpInfo = {index: info["index"], coordinates: JSON.stringify(point), province: addComp.province,
                    city: addComp.city, district: addComp.district, street: addComp.street, roomNum: addComp.streetNumber};
                tableProcessedWords.push(tmpInfo);
                tableProcessedWordsIndex.push(info["index"]);
            }else{
                tableProcessedWords[tmpIndex]["province"] = addComp.province;
                tableProcessedWords[tmpIndex]["city"] = addComp.city;
                tableProcessedWords[tmpIndex]["district"] = addComp.district;
                tableProcessedWords[tmpIndex]["street"] = addComp.street;
                tableProcessedWords[tmpIndex]["roomNum"] = addComp.streetNumber;
            }
            if (counterToReload == counterToReloadLimit){//所有选择的地点全都解析完了
                // 将解析后的数据与原数据合并，然后进行表格重载
                for (var i =0; i < tableProcessedWordsIndex.length; i++){
                    var tmpp = tableIndex.indexOf(tableProcessedWordsIndex[i]);
                    tableData[tmpp]["province"] = tableProcessedWords[i]["province"];
                    tableData[tmpp]["city"] = tableProcessedWords[i]["city"];
                    tableData[tmpp]["district"] = tableProcessedWords[i]["district"];
                    tableData[tmpp]["street"] = tableProcessedWords[i]["street"];
                    tableData[tmpp]["roomNum"] = tableProcessedWords[i]["roomNum"];
                }
                stationTable.reload({
                    data: tableData
                });
                counterToReload = 0;
                tableProcessedWords = [];
                tableProcessedWordsIndex = [];
                tableProcessed = [];
                tableProcessedIndex = [];
            }
        }else{
            console.log("您选择地址没有解析到结果!");
        }
    }, city);
}

var GPS = {// https://www.oschina.net/code/snippet_260395_39205#58007     百度坐标和GPS坐标转化
    PI : 3.14159265358979324,
    x_pi : 3.14159265358979324 * 3000.0 / 180.0,
    delta : function (lat, lon) {
        // Krasovsky 1940
        //
        // a = 6378245.0, 1/f = 298.3
        // b = a * (1 - f)
        // ee = (a^2 - b^2) / a^2;
        var a = 6378245.0; //  a: 卫星椭球坐标投影到平面地图坐标系的投影因子。
        var ee = 0.00669342162296594323; //  ee: 椭球的偏心率。
        var dLat = this.transformLat(lon - 105.0, lat - 35.0);
        var dLon = this.transformLon(lon - 105.0, lat - 35.0);
        var radLat = lat / 180.0 * this.PI;
        var magic = Math.sin(radLat);
        magic = 1 - ee * magic * magic;
        var sqrtMagic = Math.sqrt(magic);
        dLat = (dLat * 180.0) / ((a * (1 - ee)) / (magic * sqrtMagic) * this.PI);
        dLon = (dLon * 180.0) / (a / sqrtMagic * Math.cos(radLat) * this.PI);
        return {'lat': dLat, 'lon': dLon};
    },

    //WGS-84 to GCJ-02
    gcj_encrypt : function (wgsLat, wgsLon) {
        if (this.outOfChina(wgsLat, wgsLon))
            return {'lat': wgsLat, 'lon': wgsLon};

        var d = this.delta(wgsLat, wgsLon);
        return {'lat' : wgsLat + d.lat,'lon' : wgsLon + d.lon};
    },
    //GCJ-02 to WGS-84
    gcj_decrypt : function (gcjLat, gcjLon) {
        if (this.outOfChina(gcjLat, gcjLon))
            return {'lat': gcjLat, 'lon': gcjLon};

        var d = this.delta(gcjLat, gcjLon);
        return {'lat': gcjLat - d.lat, 'lon': gcjLon - d.lon};
    },
    //GCJ-02 to WGS-84 exactly
    gcj_decrypt_exact : function (gcjLat, gcjLon) {
        var initDelta = 0.01;
        var threshold = 0.000000001;
        var dLat = initDelta, dLon = initDelta;
        var mLat = gcjLat - dLat, mLon = gcjLon - dLon;
        var pLat = gcjLat + dLat, pLon = gcjLon + dLon;
        var wgsLat, wgsLon, i = 0;
        while (1) {
            wgsLat = (mLat + pLat) / 2;
            wgsLon = (mLon + pLon) / 2;
            var tmp = this.gcj_encrypt(wgsLat, wgsLon)
            dLat = tmp.lat - gcjLat;
            dLon = tmp.lon - gcjLon;
            if ((Math.abs(dLat) < threshold) && (Math.abs(dLon) < threshold))
                break;

            if (dLat > 0) pLat = wgsLat; else mLat = wgsLat;
            if (dLon > 0) pLon = wgsLon; else mLon = wgsLon;

            if (++i > 10000) break;
        }
        //console.log(i);
        return {'lat': wgsLat, 'lon': wgsLon};
    },
    //GCJ-02 to BD-09
    bd_encrypt : function (gcjLat, gcjLon) {
        var x = gcjLon, y = gcjLat;
        var z = Math.sqrt(x * x + y * y) + 0.00002 * Math.sin(y * this.x_pi);
        var theta = Math.atan2(y, x) + 0.000003 * Math.cos(x * this.x_pi);
        bdLon = z * Math.cos(theta) + 0.0065;
        bdLat = z * Math.sin(theta) + 0.006;
        return {'lat' : bdLat,'lon' : bdLon};
    },
    //BD-09 to GCJ-02
    bd_decrypt : function (bdLat, bdLon) {
        var x = bdLon - 0.0065, y = bdLat - 0.006;
        var z = Math.sqrt(x * x + y * y) - 0.00002 * Math.sin(y * this.x_pi);
        var theta = Math.atan2(y, x) - 0.000003 * Math.cos(x * this.x_pi);
        var gcjLon = z * Math.cos(theta);
        var gcjLat = z * Math.sin(theta);
        return {'lat' : gcjLat, 'lon' : gcjLon};
    },
    //WGS-84 to Web mercator
    //mercatorLat -> y mercatorLon -> x
    mercator_encrypt : function(wgsLat, wgsLon) {
        var x = wgsLon * 20037508.34 / 180.;
        var y = Math.log(Math.tan((90. + wgsLat) * this.PI / 360.)) / (this.PI / 180.);
        y = y * 20037508.34 / 180.;
        return {'lat' : y, 'lon' : x};
        /*
        if ((Math.abs(wgsLon) > 180 || Math.abs(wgsLat) > 90))
            return null;
        var x = 6378137.0 * wgsLon * 0.017453292519943295;
        var a = wgsLat * 0.017453292519943295;
        var y = 3189068.5 * Math.log((1.0 + Math.sin(a)) / (1.0 - Math.sin(a)));
        return {'lat' : y, 'lon' : x};
        //*/
    },
    // Web mercator to WGS-84
    // mercatorLat -> y mercatorLon -> x
    mercator_decrypt : function(mercatorLat, mercatorLon) {
        var x = mercatorLon / 20037508.34 * 180.;
        var y = mercatorLat / 20037508.34 * 180.;
        y = 180 / this.PI * (2 * Math.atan(Math.exp(y * this.PI / 180.)) - this.PI / 2);
        return {'lat' : y, 'lon' : x};
        /*
        if (Math.abs(mercatorLon) < 180 && Math.abs(mercatorLat) < 90)
            return null;
        if ((Math.abs(mercatorLon) > 20037508.3427892) || (Math.abs(mercatorLat) > 20037508.3427892))
            return null;
        var a = mercatorLon / 6378137.0 * 57.295779513082323;
        var x = a - (Math.floor(((a + 180.0) / 360.0)) * 360.0);
        var y = (1.5707963267948966 - (2.0 * Math.atan(Math.exp((-1.0 * mercatorLat) / 6378137.0)))) * 57.295779513082323;
        return {'lat' : y, 'lon' : x};
        //*/
    },
    // two point's distance
    distance : function (latA, lonA, latB, lonB) {
        var earthR = 6371000.;
        var x = Math.cos(latA * this.PI / 180.) * Math.cos(latB * this.PI / 180.) * Math.cos((lonA - lonB) * this.PI / 180);
        var y = Math.sin(latA * this.PI / 180.) * Math.sin(latB * this.PI / 180.);
        var s = x + y;
        if (s > 1) s = 1;
        if (s < -1) s = -1;
        var alpha = Math.acos(s);
        var distance = alpha * earthR;
        return distance;
    },
    outOfChina : function (lat, lon) {
        if (lon < 72.004 || lon > 137.8347)
            return true;
        if (lat < 0.8293 || lat > 55.8271)
            return true;
        return false;
    },
    transformLat : function (x, y) {
        var ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
        ret += (20.0 * Math.sin(6.0 * x * this.PI) + 20.0 * Math.sin(2.0 * x * this.PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(y * this.PI) + 40.0 * Math.sin(y / 3.0 * this.PI)) * 2.0 / 3.0;
        ret += (160.0 * Math.sin(y / 12.0 * this.PI) + 320 * Math.sin(y * this.PI / 30.0)) * 2.0 / 3.0;
        return ret;
    },
    transformLon : function (x, y) {
        var ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
        ret += (20.0 * Math.sin(6.0 * x * this.PI) + 20.0 * Math.sin(2.0 * x * this.PI)) * 2.0 / 3.0;
        ret += (20.0 * Math.sin(x * this.PI) + 40.0 * Math.sin(x / 3.0 * this.PI)) * 2.0 / 3.0;
        ret += (150.0 * Math.sin(x / 12.0 * this.PI) + 300.0 * Math.sin(x / 30.0 * this.PI)) * 2.0 / 3.0;
        return ret;
    }
};
