/**
 * Created by SXChen on 2016/7/15.
 */
window.onload=function(){
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
            var sum=0;
            for(var i=0;i<6;i++){
                try{
                    sum += Number(x[i].value);
                } catch(e) {
                    //console.log(e);
                    sum += 0;
                };
                console.log(sum);
            };
            if ($(this).children){
                //console.log('have no children');
                $(this).html((sum/6).toFixed(2)); //??
            } else {
                $(this).children().attr('value',(sum/6).toFixed(2));
            }
        });
    });
}