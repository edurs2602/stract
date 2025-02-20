from flask import Flask
from config import Config
from flasgger import Swagger

def create_api():
    api = Flask(__name__)
    api.config.from_object(Config)
    Swagger(api)

    from api import routes
    api.register_blueprint(routes.bp)

    return api

