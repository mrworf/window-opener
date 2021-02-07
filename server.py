from flask import Flask, jsonify, abort, request
import logging
from threading import Thread, Lock

class WebServer(Thread):
  def __init__(self, port=8080, listen='0.0.0.0'):
    Thread.__init__(self)
    self.app = Flask(__name__)
    self.port = port
    self.listen = listen
    self.daemon = True

  def addRoute(self, url, func, **kwargs):
    self.app.add_url_rule(url, view_func=func, **kwargs)

  def run(self):
    self.app.run(debug=False, port=self.port, host=self.listen)
