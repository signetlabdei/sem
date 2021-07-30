from flask import Flask, redirect, session

from dashboard.table import Table


flask_app = Flask(__name__)
tab = Table('/tmp/sem-test/wifi-plotting-example/data/4b175ec0-0d1e-41bf-b6a9-b38ea8299ada/stderr')

from dashboard.views import tables
flask_app.register_blueprint(tables)

if __name__ == '__main__':
    flask_app.run()
