from flask import Blueprint, jsonify, request, render_template
from . import tab

tables = Blueprint('tables', __name__, url_prefix='')


@tables.route("/")
def index():
    return render_template("table.html")


@tables.route("/serverside_table", methods=['GET'])
def serverside_table_content():
    # print('hi')
    # db, data_dir = process_logs('/tmp/sem-test/wifi-plotting-example/data/bcbae1fc-8c50-4c61-99e7-878af4554ac8/stderr')
    # pass_data = filter_logs(db, time_end=0)
    # pass_data = db.table('logs').all()
    # print(db.get(doc_id=0))
    # print('hi')
    tab.set_request(request)
    data = tab.build_datatable()
    return jsonify(data)


@tables.route("/filters", methods=['GET'])
def filter():
    un = tab.set_filter_request(request)
    return jsonify(un)


@tables.route("/unique_values", methods=['GET'])
def get_unique():
    un = tab.get_unique_values(request)
    print('Unique')
    print(un)
    return jsonify(tab.get_unique_values(request))
