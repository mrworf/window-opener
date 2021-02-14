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
import time
import logging

from endpoints import LocalEndpoint, RemoteEndpoint

class ProgramManager:
  def __init__(self):
    self.PROGRAMS = {}
    self.endpoints = {'local' : LocalEndpoint('local')}
    self.activeProgram = None

  def createEndpoint(self, name, url, token):
    if name not in self.endpoints:
      self.endpoints[name] = RemoteEndpoint(name, url, token)
    return self.endpoints[name]

  def createProgram(self, name):
    if name not in self.PROGRAMS:
      self.PROGRAMS[name] = Program(name)
    return self.PROGRAMS[name]

  def getEndpoint(self, name):
    return self.endpoints.get(name, None)

  def getPrograms(self):
    return list(self.PROGRAMS.keys())

  def getActiveProgram(self):
    return self.activeProgram.name if self.activeProgram else None

  def start(self, name):
    if name not in self.PROGRAMS:
      logging.error(f'Program "{name}" does not exist')
      return None
    if self.activeProgram and self.activeProgram.name == name:
      logging.warning(f'Program "{name}" is already active')
      return self.activeProgram
    self.stop()
    p = self.PROGRAMS[name]
    ret = p.start()
    if ret:
      self.activeProgram = p
      return p
    return None

  def stop(self, name=None):
    if not self.activeProgram:
      return False
    if name and name != self.activeProgram.name:
      return False

    self.activeProgram.stop()
    self.activeProgram = None
    return True

class Program:
  def __init__(self, name):
    self.START_ACTIONS = []
    self.PRE_STOP_ACTIONS = []
    self.POST_STOP_ACTIONS = []
    self.safe = True
    self.name = name

  def addStartAction(self, endpoint, method, *args):
    ''' Command(s) to run when starting
    All of these will be closed when terminating
    '''
    if method not in Action.METHOD_START:
      logging.error(f'No such method "{method}" for start actions')
      return False
    action = Action(endpoint, method, args)
    self.START_ACTIONS.append(action)
    return action

  def addStopAction(self, endpoint, method, *arguments):
    if method not in Action.METHOD_STOP:
      logging.error(f'No such method "{method}" for stop actions')
      return False
    action = Action(endpoint, method, arguments)
    self.POST_STOP_ACTIONS.append(action)
    return action

  def addPreStopAction(self, endpoint, method, *arguments):
    if method not in Action.METHOD_STOP:
      logging.error(f'No such method "{method}" for pre-stop actions')
      return False
    self.PRE_STOP_ACTIONS.append(Action(endpoint, method, arguments))

  def start(self):
    for action in self.START_ACTIONS:
      action.execute()
    return True

  def stop(self):
    for action in self.PRE_STOP_ACTIONS:
      action.execute()
    for action in self.START_ACTIONS:
      action.finish()
    for action in self.POST_STOP_ACTIONS:
      action.execute()

class Action:
  ACTION_EXECUTE = 'execute'
  ACTION_DELAY = 'delay'
  ACTION_KILL_APP = 'kill app'
  ACTION_KILL_PID = 'kill pid'
  ACTION_CLOSE_WINDOW = 'close window'
  ACTION_SENDKEYS = 'sendkeys'
  ACTION_FOCUS = 'focus'
  ACTION_MOUSE_MOVE = 'mouse move'

  METHOD_START = [ACTION_EXECUTE, ACTION_DELAY, ACTION_SENDKEYS, ACTION_FOCUS, ACTION_MOUSE_MOVE]
  METHOD_STOP = [ACTION_DELAY, ACTION_CLOSE_WINDOW, ACTION_KILL_PID, ACTION_KILL_APP, ACTION_SENDKEYS, ACTION_FOCUS, ACTION_MOUSE_MOVE]

  def __init__(self, endpoint, method, *arguments):
    self.endpoint = endpoint
    self.method = method.lower()
    self.arguments = arguments
    self.options = {}
    self.pid = -1

  def setOptions(self, options):
    self.options = options if options else {}

  def finish(self):
    if self.pid == -1:
      logging.debug(f'{self.arguments} has no pid to kill')
      return
    self.endpoint.kill_pid({}, self.pid)
    self.pid = -1

  def execute(self):
    ret = None
    if self.method == Action.ACTION_EXECUTE:
      ret = self.endpoint.execute(self.options, *self.arguments)
      if ret == -1:
        logging.error(f'Unable to execute command ({self.arguments})')
        ret = None
      else:
        self.pid = ret
    elif self.method == Action.ACTION_DELAY:
      time.sleep(float(*self.arguments[0]))
    elif self.method == Action.ACTION_KILL_APP:
      self.endpoint.kill_app(self.options, *self.arguments[0])
    elif self.method == Action.ACTION_KILL_PID:
      self.endpoint.kill_pid(self.options, *self.arguments[0])
    elif self.method == Action.ACTION_CLOSE_WINDOW:
      self.endpoint.close_window(self.options, *self.arguments[0])
    elif self.method == Action.ACTION_SENDKEYS:
      self.endpoint.sendkeys(self.options, *self.arguments[0])
    elif self.method == Action.ACTION_FOCUS:
      self.endpoint.focus(self.options, *self.arguments[0])
    elif self.method == Action.ACTION_MOUSE_MOVE:
      self.endpoint.mouse_move(self.options, *self.arguments[0], *self.arguments[1])
    return ret
