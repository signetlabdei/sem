from flask import Flask, redirect, session

from dashboard.table import Table

tab = Table()

flask_app = Flask(__name__)

from dashboard.views import tables
flask_app.register_blueprint(tables)
