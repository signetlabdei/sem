from flask import Flask, redirect, session, render_template, jsonify, request

from dashboard.table import Table


flask_app = Flask(__name__)
tab = Table()


@flask_app.route("/")
def index():
    return render_template("table.html")


@flask_app.route("/serverside_table", methods=['GET'])
def serverside_table_content():
    tab.set_request(request)
    data = tab.build_datatable()
    return jsonify(data)


@flask_app.route("/filters", methods=['GET'])
def filter():
    tab.set_filter_request(request)

    data = tab.buildchart()
    plot_data = []
    # plot_data = [{'x': x, 'y': y} for x, y in data]
    for i in data:
        plot_data += [{'x': i['time'], 'y': float(i['jitter_context'])}]
    ret_dict = {
            'plot': plot_data,
            'data': data
            }
    return jsonify(ret_dict)


@flask_app.route("/unique_values", methods=['GET'])
def get_unique():
    return jsonify(tab.get_unique_values())


@flask_app.route("/chart", methods=['GET'])
def make_chart():
    data = tab.buildchart()
    plot_data = []
    # plot_data = [{'x': x, 'y': y} for x, y in data]
    for i in data:
        plot_data += [{'x': i['time'], 'y': float(i['jitter_context'])}]

    # unique_values = tab.get_unique_values()
    ret_dict = {
            'plot': plot_data,
            'data': data,
            # 'component': unique_values['component']
            }
    return jsonify(ret_dict)


@flask_app.route("/update_search_column", methods=['GET'])
def set_search_columns():
    tab.set_search_columns(request)
    return jsonify('SUCCESS')
# ef __name__ == '__main__':
#     flask_app.run()
