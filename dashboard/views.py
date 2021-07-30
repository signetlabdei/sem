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
    return jsonify('Success')


@tables.route("/unique_values", methods=['GET'])
def get_unique():
    return jsonify(tab.get_unique_values(request))
