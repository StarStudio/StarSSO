import os

from .wsgi import WSGIAppFactory

app = WSGIAppFactory(os.environ.get('STARSSO_SERVER_MODE', 'APIServer')).Build()
