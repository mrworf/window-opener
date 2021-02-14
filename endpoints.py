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
import subprocess
import psutil
import win32gui
import win32api
import win32con
import requests
import win32com.client
import pythoncom
import logging
import time

class LocalEndpoint:
  def __init__(self, name, url = None, token = None):
    self.name = name

  def execute(self, options, cmdline):
    try:
      logging.debug(f'Starting {cmdline}')
      ret = subprocess.Popen(cmdline)
      logging.debug(f'Process started, PID = {ret.pid}')
      return ret.pid
    except:
      logging.exception(f'Failed to launch "{cmdline}"')
    return -1

  def kill_pid(self, options, pid):
    ret = False
    if pid > 0:
      logging.debug(f'Killing {pid}')
      try:
        p = psutil.Process(pid)
        p.terminate()
        ret = True
      except psutil.NoSuchProcess:
        logging.warning(f'PID {pid} does not exist')
      except:
        logging.exception('Unknown error')
    return ret

  def _wait_for_it(self, timeout, checkFunc, userData=None):
    timer = 0
    result = checkFunc(userData)
    while not result:
      time.sleep(0.1)
      timer += 0.1
      if timeout > 0 and timer >= timeout:
        break
      result = checkFunc(userData)
    return result

  def close_window(self, options, window=None):
    ret = False
    logging.debug(f'close_window({window})')
    if window:
      handle = win32gui.FindWindow(None, window)
      if not handle and options.get('waitforit', False):
        logging.info(f'Waiting for "{window}" to appear')
        handle = self._wait_for_it(options.get('maxwait', 0), win32gui.FindWindow, window)
        if not handle:
          logging.info(f'Timed out waiting for window "{window}" to appear.')

      if handle and options.get('whenactive', False):
        logging.info(f'Waiting for "{window}" to become the active window')
        if not self._wait_for_it(options.get('maxwait', 0), lambda wnd: win32gui.GetForegroundWindow() == wnd, window):
          logging.info(f'Timed out waiting for window "{window}" to get focus.')
          handle = 0

      if handle and options.get('whenvisible', False):
        logging.info(f'Waiting for "{window}" to become visible')
        if not self._wait_for_it(options.get('maxwait', 0), win32gui.IsWindowVisible, window):
          logging.info(f'Timed out waiting for window "{window}" to become visible.')
          handle = 0

      if handle and options.get('wheniconic', False):
        logging.info(f'Waiting for "{window}" to be iconic (minimized)')
        if not self._wait_for_it(options.get('maxwait', 0), win32gui.IsIconic, window):
          logging.info(f'Timed out waiting for window "{window}" to become iconic.')
          handle = 0
    else:
      handle = win32gui.GetForegroundWindow()

    if handle:
      win32gui.PostMessage(handle, win32con.WM_CLOSE, 0, 0)
      ret = True
    else:
      logging.warning(f'Cannot find window "{window}"')
    return ret

  def kill_app(self, options, appname):
    ret = False
    logging.debug(f'kill_app({appname})')
    for proc in psutil.process_iter(['pid', 'name', 'username', 'ppid']):
      try:
        if proc.name() == appname:
          logging.debug(f'Found {proc.info}, proceeding to killing it')
          ret = ret | self.kill_pid(proc.pid)
      except:
        logging.debug('Permission denied when inspecting a process, skipping')
        pass # c'est la vie
    return ret

  def sendkeys(self, options, keys):
    pythoncom.CoInitialize()
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys(keys)
    return True

  def focus(self, options, window):
    ret = False
    handle = 0

    if window:
      handle = win32gui.FindWindow(None, window)
      if not handle and options.get('waitforit', False):
        logging.info(f'Waiting for "{window}" to appear')
        handle = self._wait_for_it(options.get('maxwait', 0), win32gui.FindWindow, window)
        if not handle:
          logging.info(f'Timed out waiting for window "{window}" to appear.')

      if handle and options.get('whenvisible', False):
        logging.info(f'Waiting for "{window}" to become visible')
        if not self._wait_for_it(options.get('maxwait', 0), win32gui.IsWindowVisible, window):
          logging.info(f'Timed out waiting for window "{window}" to become visible.')
          handle = 0

      if handle and options.get('wheniconic', False):
        logging.info(f'Waiting for "{window}" to be iconic (minimized)')
        if not self._wait_for_it(options.get('maxwait', 0), win32gui.IsIconic, window):
          logging.info(f'Timed out waiting for window "{window}" to become iconic.')
          handle = 0

    if handle:
      pythoncom.CoInitialize()
      #shell = win32com.client.Dispatch("WScript.Shell")
      #shell.SendKeys(keys)

      shell = win32com.client.Dispatch("WScript.Shell")
      shell.SendKeys('%')

      win32gui.ShowWindow(handle, 5)
      win32gui.SetForegroundWindow(handle)
      if options.get('maximize', False):
        win32gui.ShowWindow(handle, 3)
      elif options.get('restore', False):
        win32gui.ShowWindow(handle, 9)
      ret = True
    else:
      logging.warning(f'Cannot find window "{window}"')
    return ret

  def mouse_move(self, options, x, y):
    win32api.SetCursorPos((x,y))
    leftclicks = options.get('leftclick', 0)
    rightclicks = options.get('rightclick', 0)
    for i in range(0, leftclicks):
      win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
      win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
      win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
    for i in range(0, rightclicks):
      win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,x,y,0,0)
      win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,x,y,0,0)
      win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,x,y,0,0)
    return True

class RemoteEndpoint:
  def __init__(self, name, url, token):
    self.name = name
    self.url = url
    self.token = token

  def _remote_call(self, method, options, *arguments):
    r = requests.post(f'{self.url}/lowlevel/{method}', json={'arguments': [*arguments], 'options': options, 'token' : self.token})
    if 'result' in r.json():
      return r.json()['result']
    return False

  def execute(self, options, cmdline):
    try:
      logging.debug(f'Starting {cmdline}')
      return self._remote_call('execute', options, *cmdline)
    except:
      logging.error(f'Failed to launch {cmdline}')
    return -1

  def kill_pid(self, options, pid):
    if pid > 0:
      logging.debug(f'Killing {pid}')
      return self._remote_call('kill pid', options, pid)
    return False

  def close_window(self, options, window=None):
    return self._remote_call('close window', options, window)

  def kill_app(self, options, appname):
    return self._remote_call('kill app', options, appname)

  def sendkeys(self, options, keys):
    return self._remote_call('sendkeys', options, keys)

  def focus(self, options, window):
    return self._remote_call('focus', options, window)

  def mouse_move(self, options, x, y):
    return self._remote_call('mouse move', options, x, y)
