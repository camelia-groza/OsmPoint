import flask
import py

import OsmApi
import yaml

from database import db
from frontend import frontend, oid

def load_imported_points(file_path_cfg):
    if file_path_cfg is not None:
        file_path = py.path.local(file_path_cfg)
        if file_path.check(file=True):
            with file_path.open('rb') as f:
                return yaml.load(f)
    return []

def configure_app(app, workdir):
    import os.path
    workdir = os.path.abspath(workdir)

    app.config['OSMPOINT_ADMINS'] = []
    app.config['IMPORTED_POINTS_PATH'] = None

    config_file = os.path.join(workdir, 'config.py')
    app.config.from_pyfile(config_file, silent=False)

    app.config['IMPORTED_POINTS'] = load_imported_points(
        app.config['IMPORTED_POINTS_PATH'])

    with app.test_request_context():
        db.create_all()

def create_app(workdir):
    app = flask.Flask(__name__)
    db.init_app(app)
    oid.init_app(app)

    app.register_blueprint(frontend)

    configure_app(app, workdir)

    return app
