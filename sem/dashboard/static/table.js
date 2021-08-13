$(document).ready(function () {
    // $(document).ajaxSend(function() {
    //     $("#overlay").fadeIn(300);　
    // });
    function addData(chart, data) {
        // chart.data.datasets.forEach((dataset) => {
        //     dataset.data.push(data);
        // });
        console.log(data);
        chart.data.datasets[0].data = data;
        chart.update('none');
    }

    function removeData(chart) {
        // chart.data.datasets.forEach((dataset) => {
        //     dataset.data.pop();
        // });
        chart.data.datasets[0].data.pop();
        chart.update();
    }
    var table = $('#serverside_table').DataTable({
        bProcessing: true,
        serverSide: true,
        searchPanes: {
            viewTotal: true,
            show: true,
        },
        dom: 'Plfrtip',
        sPaginationType: "full_numbers",
        lengthMenu: [[10, 25, 50, 100, 1000, -1], [10, 25, 50, 100, 1000, "All"]],
        scrollY: 500,
        scroller: {
            loadingIndicator: true
        },
        bjQueryUI: true,
        autoWidth: true,
        sAjaxSource: '/serverside_table',
        language: {
            processing: '<i class="fa fa-spinner fa-spin fa-3x fa-fw"></i><span class="sr-only">Loading..n.</span> ',
        },
        columnDefs: [
            { width: '10px', targets: 0 },
            { width: '10px', targets: 1 },
            { width: '10px', orderable: false, targets: 2 },
            { width: '10px', targets: 3 },
            { width: '10px', targets: 4 },
            { width: '10px', targets: 5 },
            { width: '10px', targets: 6 },
            { width: '10px', targets: 7 }
        ],
        fixedColumns: true,
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
    var scatter_chart;
    $.ajax({
        url: '/chart',
        success: function(result){
            console.log(result);
            // custom_dataset = []
            // $.each(result.component, function(i, val){
            //     console.log(i);
            //     console.log(val);
            // });
            var data = {
                datasets: [{
                    label: "Dataset #1",
                    backgroundColor: "rgba(255,99,132,0.2)",
                    borderColor: "rgba(255,99,132,1)",
                    borderWidth: 2,
                    hoverBackgroundColor: "rgba(255,99,132,0.4)",
                    hoverBorderColor: "rgba(255,99,132,1)",
                    // showLine: true,
                    indexAxis: 'x',
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    data: result.plot
                }]
            };

            var option = {
                parsing: false,
                normalized: true,
                animation: false,

                scales: {
                    yAxes: [{
                        stacked: true,
                        gridLines: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    }],
                    xAxes: [{
                        type: 'time',
                        gridLines: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    }]
                },
                // elements: {
                //     line: {
                //         tension: 0,
                //     }
                // },
                plugins: {
                    decimation: {
                        enabled: true,
                        algorithm: 'lttb'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(tooltipItem) {
                                // console.log('hi');
                                // console.log(tooltipItem);
                                // console.log(result.data);
                                // console.log(result.data[0]);
                                var current_log = result.data[tooltipItem.dataIndex];
                                var timestamp = current_log.time;
                                var context = current_log.context;
                                var extended_context = current_log.extended_context;
                                var component = current_log.component;
                                var func = current_log.function;
                                var args = current_log.arguments;
                                var severity_class = current_log.severity_class;
                                var mssg = current_log.message;
                                if (extended_context != null)
                                {
                                    return ["Extended Context: " + extended_context, "Component: " + component,  "Function: " + func, "Arguments: " + args, "Severity Class: " + severity_class, "Message: " + mssg];
                                }
                                else
                                {
                                    return ["Component: " + component,  "Function: " + func, "Arguments: " + args, "Severity Class: " + severity_class, "Message: " + mssg];
                                }
                            }
                        },
                    },
                    zoom: {
                        pan: {
                            enabled: true,
                            mode: 'xy',
                        },
                        zoom: {
                            wheel: {
                                enabled: true,
                            },
                            pinch: {
                                enabled: true
                            },
                            // drag: {
                            //     enabled: true
                            // },
                            mode: 'xy',
                        }
                    }
                }
            };
            var mychart = document.getElementById("chart").getContext("2d");

            scatter_chart = new Chart(mychart, {
                type: 'scatter',
                options: option,
                data: data
            });
        }
    })
    $.ajax({
        url: '/unique_values',
        success: function(result){
            console.log(result)
            var lis = ["log_class", "context", "function", "component", "all_columns"];

            $.each(lis, function(index, value){
                for (let j=0;j<result[value].length;j++)
                {
                    var opt = "<option>" + result[value][j] + "</option>";
                    $("#" + value).append(opt);
                }
                if (value=='all_columns')
                {
                    $('#' + value).selectpicker('val', result['search_column']);
                }
                // else
                // {
                //     $('#' + value).selectpicker('val', result[value]);
                // }
            });
            $('.selectpicker, .search_column').selectpicker('refresh');
        }
    });
    $('#serverside_table tbody').on('click', 'tr', function(){
        var data = table.row(this).data();
        var pageNumber = data.index / table.page.info().length;

        table.search('').page(pageNumber).draw(false);
    });

    $('.search_column').change(function() {
        var columns = $("#all_columns").val();
        $.ajax({
            url: '/update_search_column',
            data: {
                search_column: columns,
            },
            traditional: true,
            beforeSend: function(){
                $("#overlay").fadeIn(300);　
            }
        }).done(function() {
            setTimeout(function(){
                $("#overlay").fadeOut(300);
            },500);

        });
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
        // beforeSend: function(){
        //     $("#overlay").fadeIn(300);　
        // },
        success: function(result){
            // console.log(result);
            // $('.clear-selectpicker').selectpicker('refresh');
            // table.ajax.reload().columns.adjust();
            // table.draw().columns.adjust();

            table.clear();
            table.rows.add(result.data)
            table.draw().columns.adjust();

            // removeData(scatter_chart);
            addData(scatter_chart, result.plot);
            scatter_chart.options.plugins.tooltip.callbacks.label = function(tooltipItem) {
                var current_log = result.data[tooltipItem.dataIndex];
                var timestamp = current_log.time;
                var context = current_log.context;
                var extended_context = current_log.extended_context;
                var component = current_log.component;
                var func = current_log.function;
                var args = current_log.arguments;
                var severity_class = current_log.severity_class;
                var mssg = current_log.message;
                if (extended_context != null)
                {
                    return ["Extended Context: " + extended_context, "Component: " + component,  "Function: " + func, "Arguments: " + args, "Severity Class: " + severity_class, "Message: " + mssg];
                }
                else
                {
                    return ["Component: " + component,  "Function: " + func, "Arguments: " + args, "Severity Class: " + severity_class, "Message: " + mssg];
                }
            }
        }
    })
        // .done(function() {
        // setTimeout(function(){
        //     $("#overlay").fadeOut(300);
        // },500);
    // });
});
});
