/**
 * Created by SXChen on 2016/7/15.
 */
window.onload=function(){
    var $SCRIPT_ROOT =  window.location.host;

    $(".datetime").datetimepicker({
    format:'yyyy-mm-dd hh:ii',
    //autoclose:true,//点选日期之后关闭控件
    todayHighlight:true,
    todayBtn:true,
    maxView: "decade"
});
    /*
    双击修改td，保留原值
     */
    $("td").dblclick(function(){
        //获取不到td的id值则取消逻辑
        if ('undefined' == typeof($(this).attr('id'))){
            alert('该单元格无法修改');
            return false;
        } else {
            try {
                var nodename = $(this).children()[0].nodeName;
            } catch(e) {
                var nodename = 'undefined';
            };
            if( nodename == 'INPUT' || nodename == 'TEXTAREA' || $(this).attr('class') == 'avg1') {
                /*
                如果没有子节点那么就会出错，无法执行下一步的判断
                td中如果嵌套了input/textarea也不提供修改,如果是avg1的机器计算的也不提供修改
                知识点：1.jquery对象和原生js对象的转换 2.判断节点的方法
                */
                //避免干扰
                //alert('该单元格已经嵌套INPUT,无法再次生成INPUT');
                return false;
            } else {
                //若获取到id值传入构造的input中作为name
                var td_id = $(this).attr('id');
                var td_cls = $(this).attr('class');
                //原值
                var old_value = $(this)[0].innerText;
                //原class
                //console.log(td_id);
                //console.log(old_value);
                if(confirm('确定需要修改数据吗？')){
                    if (td_id.indexOf('time') != -1){
                    str = '<input type="text" class="form-control datetime" name="' +
                    td_id + '" value="' + old_value + '">';
                    } else {
                        str = '<input type="text" class="form-control" name="' +
                        td_id + '" value="' + old_value + '">';
                    }
                    //console.log(str);
                    $(this).html(str);
                }
            }
        }
    });
    /*
    求平均值
     */
    $(".avg").bind("input propertychange oninput", function(){
        $(".avg1").each(function(){
            var x = $(this).siblings().children('input.avg');
            var y = $(this).siblings('td.avg');
            //console.log(y);
            var sum=0;
            for(var i=0;i<6;i++){
                var z = 0;
                z = Number(y[i].innerHTML);
                if (isNaN(z)) {
                    z =  Number($(x[i]).val());//js对象转化为jquery对象,使用$符号
                    if (isNaN(z)) {
                        z = Number($(y[i]).children('input').val())
                    }
                }
                //console.log(z);
                sum += z;
            }
            $(this).html('<input type="text" class="form-control" name="' + $(this).attr('id') + '" value="' +
                (sum/6).toFixed(2) +'" readonly'+'>'); //??
        });
    });
    /*
    相同轮辋代码只用输入一次
     */
    $('.rim-code').bind('input propertychange oninput',function(){
        $('.rim-code').val($(this).val());
    });
    /*
    ajax获取图片
     */
    $(function(){
        $.ajax({
            url: 'http://' + $SCRIPT_ROOT + '/api/v1.0/pic/condition/circum/',
            method:'GET',
            data:{},
            dataType:"json",
            processData:false,
            success:function(html){
                str = '';
                var ddData = [];
                for(k in html){
                    ddData.push(html[k])
                }
                //console.log(ddData);
                //构造<option></option>
                for(k in ddData){
                    //console.log(ddData[k]);
                    str += '<option value="' + ddData[k].value + ' data-imagescr="' + ddData[k].imageSrc +
                        '"' + ' data-description="' + ddData[k].description +
                        '"' +
                        '>' + ddData[k].text + '</option>'
                }
                //console.log(str);

                $('.load_pic_circum').ddslick({
                    data:ddData,
                    width:558,   //指定px之后打印会出现偏差
                    selectText: "选择周向破坏的图形",
                    imagePosition:"right",
                    onSelected: function(selectedData){
                        //callback function: do something with selectedData;
                        //console.log(selectedData.original.context);
                        //console.log(selectedData.selectedData.imageSrc);

                    }
                });
            }
        });
    });

    $(function(){
        $.ajax({
            url: 'http://' + $SCRIPT_ROOT + '/api/v1.0/pic/condition/section/',
            method:'GET',
            data:{},
            dataType:"json",
            processData:false,
            success:function(html){
                var ddData = [];
                for(k in html){
                    ddData.push(html[k])
                }
                //console.log(ddData);
                $('.load_pic_section').ddslick({
                    data:ddData,
                    width:558,
                    selectText: "选择断面破坏的图形",
                    imagePosition:"right",
                    onSelected: function(selectedData){
                        //callback function: do something with selectedData;
                        //console.log(selectedData);
                    }
                });
            }
        });
    });
    /*
    点击图标保存
     */
    click_submit = function(){
        $("form").submit();
        return true;
    };
    /*
    按照屏幕宽度控制组件位置
     */
    var resize_layer = function(){
        console.log('resizing...');
        var screen_width = $(window).outerWidth();//获取屏幕宽度
        var container_width = $(".container").outerWidth();//获取container宽度
        var offset_width = (screen_width - container_width)/4;
        $(".rightLayer").css({
            "display":"block",
            "right":offset_width + "px",
            "position":"fixed",
            "bottom":"0px"
        });
        $(".leftLayer").css({
            "display":"block",
            "left":offset_width + "px",
            "position":"fixed",
            "bottom":"0px"
        });
    };

    resize_layer();

    $(window).resize(function(){
        console.log("正在调整窗口大小!");
        $(".rightLayer,.leftLayer").removeAttr('style');
        resize_layer();
    });
};
