from flask import Blueprint, jsonify, request, render_template
from . import tab

tables = Blueprint('tables', __name__, url_prefix='')


@tables.route("/")
def index():
    return render_template("table.html")


@tables.route("/serverside_table", methods=['GET'])
def serverside_table_content():
    tab.set_request(request)
    data = tab.build_datatable()
    return jsonify(data)


@tables.route("/filters", methods=['GET'])
def filter():
    tab.set_filter_request(request)

    data = tab.buildchart()
    plot_data = []
    # plot_data = [{'x': x, 'y': y} for x, y in data]
    for i in data:
        plot_data += [{'x': i['time'], 'y': float(i['context'])}]
    ret_dict = {
            'plot': plot_data,
            'data': data
            }
    return jsonify(ret_dict)


@tables.route("/unique_values", methods=['GET'])
def get_unique():
    return jsonify(tab.get_unique_values())


@tables.route("/chart", methods=['GET'])
def make_chart():
    data = tab.buildchart()
    plot_data = []
    # plot_data = [{'x': x, 'y': y} for x, y in data]
    for i in data:
        plot_data += [{'x': i['time'], 'y': float(i['context'])}]

    unique_values = tab.get_unique_values()
    ret_dict = {
            'plot': plot_data,
            'data': data,
            'component': unique_values['component']
            }
    return jsonify(ret_dict)
