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

  def close_window(self, options, *args):
    logging.debug(f'{args}')
    if args:
      window = args[0]
    else:
      window = None
    ret = False
    logging.debug(f'close_window({window})')
    if window:
      handle = win32gui.FindWindow(None, window)
      if not handle and options.get('waitforit', False):
        timeout = options.get('maxwait', 0)
        logging.info(f'Waiting for "{window}" to appear (for max {timeout} seconds)')
        timer = 0
        while not handle:
          time.sleep(0.1)
          timer += 0.1
          if timeout > 0 and timer >= timeout:
            logging.info(f'Timed out waiting for window "{window}" to appear. Max wait was {timeout} seconds')
            handle = 0
            break
          handle = win32gui.FindWindow(None, window)

      if handle and options.get('whenactive', False):
        timeout = options.get('maxwait', 0)
        logging.info(f'Waiting for "{window}" to become the active window (for max {timeout} seconds)')
        looking = None
        timer = 0
        while looking != handle:
          time.sleep(0.1)
          timer += 0.1
          if timeout > 0 and timer >= timeout:
            logging.info(f'Timed out waiting for window "{window}" to get focus. Max wait was {timeout} seconds')
            handle = 0 # So we don't close it
            break
          looking = win32gui.GetForegroundWindow()
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
        timeout = options.get('maxwait', 0)
        logging.info(f'Waiting for "{window}" to appear (for max {timeout} seconds)')
        timer = 0
        while not handle:
          time.sleep(0.1)
          timer += 0.1
          if timeout > 0 and timer >= timeout:
            logging.info(f'Timed out waiting for window "{window}" to appear. Max wait was {timeout} seconds')
            handle = 0
            break
          handle = win32gui.FindWindow(None, window)

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

  def close_window(self, options, window):
    return self._remote_call('close window', options, window)

  def kill_app(self, options, appname):
    return self._remote_call('kill app', options, appname)

  def sendkeys(self, options, keys):
    return self._remote_call('sendkeys', options, keys)

  def focus(self, options, window):
    return self._remote_call('focus', options, window)
