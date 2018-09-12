# Example command to run the example:
#
#   $ gunicorn app:aioapp -k aiohttp.worker.GunicornWebWorker
#

from aiohttp import web
from aiohttp_wsgi import WSGIHandler
from flask import Flask
from helper import async

app = Flask(__name__)

@async
@app.route('/')
def hello():
    return 'Hello, world!'


def make_aiohttp_app(app):
    wsgi_handler = WSGIHandler(app)
    aioapp = web.Application()
    aioapp.router.add_route('*', '/{path_info:.*}', wsgi_handler)
    return aioapp

aioapp = make_aiohttp_app(app)