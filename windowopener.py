# This file is part of window-opener (https://github.com/mrworf/window-opener).
#
# window-opener is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# window-opener is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with window-opener.  If not, see <http://www.gnu.org/licenses/>.
#
from flask import jsonify, abort, request
import logging
import argparse
from threading import Lock
import ctypes

from programs import Action
from endpoints import LocalEndpoint
from configuration import Config
from systray import Menu
from server import WebServer

parser = argparse.ArgumentParser(description="WindowOpener - A windows REST API automation tool", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--port', default=8080, type=int, help="Port to listen on")
parser.add_argument('--listen', default="0.0.0.0", help="Address to listen on")
parser.add_argument('--debug', action='store_true', default=False, help='Enable loads more logging')
parser.add_argument('--lowlevel', choices=['yes', 'no'], default='yes', help='Enable lowlevel REST API')
parser.add_argument('--program', choices=['yes', 'no'], default='yes', help='Enable program REST API')
cmdline = parser.parse_args()

if cmdline.debug:
  logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
else:
  logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

config = Config()
config.load()

pm = config.getProgramManager()

def get_action():
  if cmdline.program != 'yes':
    abort(403)
  elif not config.getToken():
    abort(404)

  if request.method == 'GET':
    active = pm.getActiveProgram()
    ret = {'programs' : pm.getPrograms(), 'active' : active.name if active else None}
  elif request.method == 'POST':
    j = request.json
    if 'token' not in j or j['token'] != config.getToken():
      logging.error('Token either missing from request or wrong')
      abort(403)

    if 'start' in j and j['start'] in pm.getPrograms():
      ret = {'result' : pm.start(j['start']) != None }
    elif 'stop' in j and j['stop'] in pm.getPrograms():
      ret = {'result' : pm.stop(j['stop'])}
    elif 'stop' in j and not j['stop']:
      ret = {'result' : pm.stop()}
  else:
    abort(500)

  result = jsonify(ret)
  result.status_code = 200
  return result

def post_lowlevel(method):
  if cmdline.lowlevel != 'yes':
    abort(403)
  elif not config.getToken():
    abort(404)

  ret = {'result' : None}
  j = request.json
  if 'token' not in j or j['token'] != config.getToken():
    logging.error('Token either missing from request or wrong')
    abort(403)

  if method not in Action.METHOD_START and method not in Action.METHOD_STOP:
    abort(404, f'No such method ({method})')
  elif 'arguments' not in j or not isinstance(j['arguments'], list):
    abort(500, 'Corrupt request')
  else:
    ep = LocalEndpoint('req')
    if method == Action.ACTION_EXECUTE:
      ret['result'] = ep.execute(j['options'], j['arguments'])
      if ret['result'] == -1:
        ret['result'] = None
    elif method == Action.ACTION_DELAY:
      logging.info('Ignoring delay method')
      ret['result'] = False
    elif method == Action.ACTION_KILL_APP:
      ret['result'] = ep.kill_app(j['options'], j['arguments'][0])
    elif method == Action.ACTION_KILL_PID:
      ret['result'] = ep.kill_pid(j['options'], j['arguments'][0])
    elif method == Action.ACTION_CLOSE_WINDOW:
      ret['result'] = ep.close_window(j['options'], j['arguments'][0])
    elif method == Action.ACTION_FOCUS:
      ret['result'] = ep.focus(j['options'], j['arguments'][0])
  result = jsonify(ret)
  result.status_code = 200
  return result

def onReload(systray):
  MessageBox = ctypes.windll.user32.MessageBoxW
  if pm.getActiveProgram():
    MessageBox(None, 'Can\'t reload configuration with an active program', 'WindowOpener', 0)
  else:
    config.load()
    MessageBox(None, 'Configuration has been reloaded', 'WindowOpener', 0)

# Prepare to run
running = Lock()
running.acquire()

server = WebServer()
server.addRoute('/program', get_action, methods=['GET', 'POST'])
server.addRoute('/lowlevel/<method>', post_lowlevel, methods=['POST'])

systray = Menu(onReload, lambda _: running.release())

if cmdline.debug:
  server.run()
else:
  server.start()
  systray.start()
  running.acquire()
