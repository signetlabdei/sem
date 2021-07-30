from dashboard import flask_app

flask_app.config['log_path'] = '/tmp/sem-test/wifi-plotting-example/data/4b175ec0-0d1e-41bf-b6a9-b38ea8299ada/stderr'
flask_app.run()
