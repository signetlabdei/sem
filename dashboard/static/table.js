$(document).ready(function () {
    var table = $('#serverside_table').DataTable({
        bProcessing: true,
        serverSide: true,
        searchPanes: {
            viewTotal: true,
            show: true,
        },
        dom: 'Plfrtip',
        sPaginationType: "full_numbers",
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        bjQueryUI: true,
        sAjaxSource: '/serverside_table',
        columns: [
            {"data": "time"},
            {"data": "context"},
            {"data": "extended_context"},
            {"data": "component"},
            {"data": "function"},
            {"data": "arguments"},
            {"data": "severity_class"},
            {"data": "message"}
        ],
    });
    $.ajax({
        url: '/unique_values',
        success: function(result){
            console.log(result)
            for (let i=0; i<result['context'].length; i++)
            {
                var opt = "<option>" + result['context'][i] + "</option>"
                console.log(opt)
                $("#context").append(opt)
            }
            for (let i=0; i<result['function'].length; i++)
            {
                var opt = "<option>" + result['function'][i] + "</option>"
                console.log(opt)
                $("#function").append(opt)
            }
            for (let i=0; i<result['component'].length; i++)
            {
                var opt = "<option>" + result['component'][i] + "</option>"
                console.log(opt)
                $("#component").append(opt)
            }

            $('.clear-selectpicker').selectpicker('refresh');
        }
    });
    $('.selectpicker, .time').change(function () {
        var log_class = $('#log_class').val();
        // alert(log_class);

        var context = $('#context').val();
        // alert( context)

        var func = $('#function').val();
        // alert(func)

        var component = $('#component').val();
        // alert('Component:' + component)
        
        var lower_window = $('#min').val();
        // alert("Time:" + lower_window)

        var upper_window = $('#max').val();
        // alert("Time:" + upper_window)

        $.ajax({
            url: '/filters',
            data: {
                severity_class: log_class,
                context: context,
                func: func,
                component: component,
                time_begin: lower_window,
                time_end: upper_window
            },
            traditional: true,
            success: function(result){
                console.log(result);
                // $('.clear-selectpicker').empty()
                // if ($('#context').is(':contains("Mustard")'))
                // {
                //     alert("hi")
                // }
                // console.log(test)
                // for (let i=0; i<result['context'].length; i++)
                // {
                //     var opt = "<option>" + result['context'][i] + "</option>"
                //     console.log(opt)
                //     $("#context").append(opt)
                // }
                // for (let i=0; i<result['function'].length; i++)
                // {
                //     var opt = "<option>" + result['function'][i] + "</option>"
                //     console.log(opt)
                //     $("#function").append(opt)
                // }
                // for (let i=0; i<result['component'].length; i++)
                // {
                //     var opt = "<option>" + result['component'][i] + "</option>"
                //     console.log(opt)
                //     $("#component").append(opt)
                // }

                // $('.clear-selectpicker').selectpicker('refresh');
                table.ajax.reload()
                // table.clear().draw();
                // table.rows.add(result); // Add new data
                // table.columns.adjust().draw(); // Redraw the DataTable
            }
        })
    });
});
//$(document).ready(function() {
//
//    var dtage = $('#serverside_table').DataTable({
//         "ajax": "dump.txt",
//         "columns": [
//          {"data": "time"},
//          {"data": "context"},
//          {"data": "component"},
//          {"data": "function"},
//          {"data": "severity_class"},
//          {"data": "message"}
//         ]
//    } );
//
//    // Event listener to the two range filtering inputs to redraw on input
//    $('#min, #max').keyup(function() {
//        dtage.draw();
//    });
//});
