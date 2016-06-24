(function ($) {
    $(function () {
        $('.table-expandable').each(function () {
            var table = $(this);
            table.children('tbody').children('tr').filter(':odd').hide();
            table.children('tbody').children('tr').filter(':even').click(function () {
                var element = $(this);
                element.next('tr').toggle('fast');//'slow' is too slow
            });
        });
    });
})(jQuery); 