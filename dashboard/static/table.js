$(document).ready(function () {
    function addData(chart, data) {
        // chart.data.datasets.forEach((dataset) => {
        //     dataset.data.push(data);
        // });
        console.log(data);
        chart.data.datasets[0].data = data;
        chart.update();
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
        // scrollY: 200,
        // scroller: {
        //     loadingIndicator: true
        // },
        bjQueryUI: true,
        autoWidth: true,
        sAjaxSource: '/serverside_table',
        columnDefs: [
            { width: '10px', targets: 0 },
            { width: '10px', targets: 1 },
            { width: '10px', targets: 2 },
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
            var data = {
                datasets: [{
                    label: "Dataset #1",
                    backgroundColor: "rgba(255,99,132,0.2)",
                    borderColor: "rgba(255,99,132,1)",
                    borderWidth: 2,
                    hoverBackgroundColor: "rgba(255,99,132,0.4)",
                    hoverBorderColor: "rgba(255,99,132,1)",
                    showLine: true,
                    data: result.plot
                    // [{
                    //     x: 0,
                    //     y: 5
                    // },
                    //     {
                    //         x: 1,
                    //         y: 10
                    //     },
                    //     {
                    //         x: 1,
                    //         y: 5
                    //     },
                    //     {
                    //         x: 3,
                    //         y: 10
                    //     }]
                }]
            };

            var option = {
                scales: {
                    yAxes: [{
                        stacked: true,
                        gridLines: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    }],
                    xAxes: [{
                        gridLines: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    }]
                },
                elements: {
                    line: {
                        tension: 0, // bezier curves
                    }
                },
                plugins: {
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
                                return "Timestamp: " + timestamp  + ", Context: " + context + ", Extended Context: " + extended_context + ", Component: " + component + ", Function: " + func + ", Arguments: " + args + ", Severity Class: " + severity_class + ", Message: " + mssg;
                            }
                        },
                        // enabled: false,
                        // position: 'nearest',
                        // external: function(context) {
                        //     console.log(context);
                        //     // console.log('hi');
                        //     // Tooltip Element
                        //     var tooltipEl = document.getElementById('chartjs-tooltip');

                        //     // Create element on first render
                        //     if (!tooltipEl) {
                        //         tooltipEl = document.createElement('div');
                        //         tooltipEl.id = 'chartjs-tooltip';
                        //         tooltipEl.innerHTML = '<table></table>';
                        //         document.body.appendChild(tooltipEl);
                        //     }

                        //     // Hide if no tooltip
                        //     var tooltipModel = context.tooltip;
                        //     if (tooltipModel.opacity === 0) {
                        //         tooltipEl.style.opacity = 0;
                        //         return;
                        //     }

                        //     // Set caret Position
                        //     tooltipEl.classList.remove('above', 'below', 'no-transform');
                        //     if (tooltipModel.yAlign) {
                        //         tooltipEl.classList.add(tooltipModel.yAlign);
                        //     } else {
                        //         tooltipEl.classList.add('no-transform');
                        //     }

                        //     function getBody(bodyItem) {
                        //         return bodyItem.lines;
                        //     }

                        //     // Set Text
                        //     if (tooltipModel.body) {
                        //         var titleLines = tooltipModel.title || [];
                        //         var bodyLines = tooltipModel.body.map(getBody);

                        //         var innerHtml = '<thead>';

                        //         titleLines.forEach(function(title) {
                        //             innerHtml += '<tr><th>' + title + '</th></tr>';
                        //         });
                        //         innerHtml += '</thead><tbody>';

                        //         bodyLines.forEach(function(body, i) {
                        //             var colors = tooltipModel.labelColors[i];
                        //             var style = 'background:' + colors.backgroundColor;
                        //             style += '; border-color:' + colors.borderColor;
                        //             style += '; border-width: 2px';
                        //             var span = '<span style="' + style + '"></span>';
                        //             innerHtml += '<tr><td>' + span + body + '</td></tr>';
                        //         });
                        //         innerHtml += '</tbody>';

                        //         var tableRoot = tooltipEl.querySelector('table');
                        //         tableRoot.innerHTML = innerHtml;
                        //     }

                        //     var position = context.chart.canvas.getBoundingClientRect();
                        //     var bodyFont = Chart.helpers.toFont(tooltipModel.options.bodyFont);

                        //     // Display, position, and set styles for font
                        //     tooltipEl.style.opacity = 1;
                        //     tooltipEl.style.position = 'absolute';
                        //     tooltipEl.style.left = position.left + window.pageXOffset + tooltipModel.caretX + 'px';
                        //     tooltipEl.style.top = position.top + window.pageYOffset + tooltipModel.caretY + 'px';
                        //     tooltipEl.style.font = bodyFont.string;
                        //     tooltipEl.style.padding = tooltipModel.padding + 'px ' + tooltipModel.padding + 'px';
                        //     tooltipEl.style.pointerEvents = 'none';
                        // }
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
                // table.ajax.reload().columns.adjust();
                // table.draw().columns.adjust();

                table.clear();
                table.rows.add(result.data)
                table.draw().columns.adjust();
                
                // removeData(scatter_chart);
                addData(scatter_chart, result.plot);
                // table.clear().draw();
                // table.rows.add(result); // Add new data
                // table.columns.adjust().draw(); // Redraw the DataTable
            }
        })
    });
});
