import httplib2
from werkzeug.utils import cached_property
from flask import Flask, url_for
from flask_restx import Api
from flask_swagger_ui import get_swaggerui_blueprint
h = httplib2.Http(".cache", disable_ssl_certificate_validation=True)
from flask_cors import CORS
import os
import json
from werkzeug.middleware.proxy_fix import ProxyFix
from src.utils import Globals
from src.namespaces import groupNamespace, roleNamespace, userNamespace, shareNamespace
from src.admin_client import AdminClient
from dotenv import load_dotenv
import logging

app = Flask(__name__)

CORS(app, origins=['http://localhost:4200', 'http://localhost:4200/*', "http://teide:8131", "https://tools.cartif.es/buildspace"])

app.wsgi_app = ProxyFix(app.wsgi_app)


authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}

SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
SWAGGER_BLEUPRNT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config = {
        'app_name': 'Account Manager API'
    }
)

app.register_blueprint(SWAGGER_BLEUPRNT, url_prefix = SWAGGER_URL)
# Load environment variables from .env file.
env_path="./env-files/prod/.env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)
debug = Globals().get_env("DEBUG")
if debug == "true":
    logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler()])
else:
    logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])

logger.info("Env variables loaded.")

if os.environ.get('HTTPS'):
    @property
    def specs_url(self):
        return url_for(self.endpoint('specs'), _external=True, _scheme='https')


manager_api = Api(app=app, version='1.0'
            , title="Account Manager"
            , description='Account Manager API', authorizations=authorizations, doc=False, default_swagger_filename='llll')


manager_api.add_namespace(groupNamespace)
manager_api.add_namespace(roleNamespace)
manager_api.add_namespace(userNamespace)
manager_api.add_namespace(shareNamespace)

# manager_api.init_app(app=app, add_specs=False)
if __name__ == "__main__":
    debug = Globals().get_env("DEBUG")

    if debug == "true":
        app.run(host='0.0.0.0', port=5001, debug=True)
    else:
        app.run(host='0.0.0.0', port=5001, debug=False)