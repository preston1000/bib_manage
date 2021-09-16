


// #3 显示解析结果
layui.use('form', function(){
    var $ = layui.$;
    $('#reset_sentence').click(function(){
        // 显示结果表格
        $('#show_parse_result').attr("style", "display:none");
        document.getElementById('sentence_input').reset();
        document.getElementById('show_parse_result').reset();
    });
});




// #1 home 页面的内容检查
layui.use(['form', 'layedit'], function(){
    var form = layui.form
        , layer = layui.layer
        , layedit = layui.layedit;

    // 验证规则， 在lay-verify=""中添加内容
    form.verify({
        sentence_check: function(value){
            if (value.length == 0){
                return "请输入有效的文本"
            }
        },
    });


    form.on('submit(parse_sentence_btn)', function(data){
        $('#problematic_2').prop('checked', true);
        $('#comment-block').attr('style', 'display: none');
        $('#comment-text').val('');
        sentence = data.field.sentence;
        $.ajax({
                type : 'post',//也可为get
                url : 'resolve-deprel/',
                contentType : "application/json",
                data : JSON.stringify(data.field),
                dataType : 'json',
                success : function(data, status) {
                    var parse_result = data;
                    if (data.code == "100") {
                        //显示结果
                        $('#image-block').attr("src", "../static/images/cache/" + data.data.deprel);
                        $('#image-block').attr("value", data.data.sentence); //sentence
                        $('#image-block').attr("head", data.data.head); //sentence
                        $('#image-block').attr("words", data.data.words); //sentence
                        $('#image-block').attr("relation", data.data.relation); //sentence
                        $('#show_parse_result').attr("style", "display:auto");
                        form.render();
                    }else{
                        layer.alert(data.msg, {
                            title: "解析失败"
                        })
                        return false
                    }
                },
                complete : function() {
                    return false
                },
                error : function(data, status, e) {
                    alert('接口调用错误！');
                    return false
                }
            });

        return false; //不刷新页面
    });

    form.on('submit(sub_comments)', function(data){
        if (data.field.is_problematic == 'yes' && data.field.comments.length <= 0){
            layer.alert('问题说明不能为空:', {time: 2000})
        }else{
            data.field.image_path = $('#image-block').attr('src')
            data.field.sentence = $('#image-block').attr('value')
            data.field.head = $('#image-block').attr('head')
            data.field.words = $('#image-block').attr('words')
            data.field.relation = $('#image-block').attr('relation')

            if (data.field.is_problematic == 'no'){
                data.field.comments = ''
            }
            $.ajax({
                type : 'post',//也可为get
                url : 'save-result/',
                async : false,
                contentType : "application/json",
                data : JSON.stringify(data.field),
                dataType : 'json',
                success : function(data, status) {
                    if (data.code == "400") {
                        layer.alert('提交成功，感谢您的帮助！', {
                            title: ""
                        })
                    } else {
                        alert('接口调用失败！');
                    }
                    return false
                },
                complete : function() {
                    return false
                },
                error : function(data, status, e) {
                    alert('接口调用错误！');
                    return false
                }
            });


        }
        return false;
    });

    // 是否有问题按钮
    form.on('radio(radio-no)', function(data){
        $('#comment-block').attr("style", "display:none;");
        $('#comment-text').attr("disabled", true);
    })


    form.on('radio(radio-yes)', function(data){
        $('#comment-block').attr("style", "display:auto;");
        $('#comment-text').removeAttr("disabled");
    })
});



