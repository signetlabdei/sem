from flask import Flask, render_template, jsonify, request

from sem.dashboard.dashboard import Dashboard


flask_app = Flask(__name__)
dashboard = Dashboard()


@flask_app.route("/")
def index():
    return render_template("dashboard.html")


@flask_app.route("/serverside_table", methods=['GET'])
def serverside_table_content():
    dashboard.set_request(request)
    data = dashboard.build_datatable()
    return jsonify(data)


@flask_app.route("/filters", methods=['GET'])
def filter():
    dashboard.set_filter_request(request)

    data = dashboard.buildchart()
    plot_data = []
    for i in data:
        plot_data += [{'x': i['time'], 'y': float(i['jitter_context'])}]
    ret_dict = {
            'plot': plot_data,
            'data': data
            }
    return jsonify(ret_dict)


@flask_app.route("/unique_values", methods=['GET'])
def get_unique():
    return jsonify(dashboard.get_metadata())


@flask_app.route("/chart", methods=['GET'])
def make_chart():
    data = dashboard.buildchart()
    plot_data = []
    for i in data:
        plot_data += [{'x': i['time'], 'y': float(i['jitter_context'])}]

    ret_dict = {
            'plot': plot_data,
            'data': data,
            }
    return jsonify(ret_dict)


@flask_app.route("/update_search_column", methods=['GET'])
def set_search_columns():
    dashboard.set_search_columns(request)
    return jsonify('SUCCESS')
