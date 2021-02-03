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

class LocalEndpoint:
  def __init__(self, name, url = None, token = None):
    self.name = name

  def execute(self, cmdline):
    try:
      logging.debug(f'Starting {cmdline}')
      ret = subprocess.Popen(cmdline)
      logging.debug(f'Process started, PID = {ret.pid}')
      return ret.pid
    except:
      logging.exception(f'Failed to launch "{cmdline}"')
    return -1

  def kill_pid(self, pid):
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

  def close_window(self, window=None):
    ret = False
    logging.debug(f'close_window({window})')
    if window:
      handle = win32gui.FindWindow(None, window)
    else:
      handle = win32gui.GetForegroundWindow()

    if handle:
      win32gui.PostMessage(handle, win32con.WM_CLOSE, 0, 0)
      ret = True
    else:
      logging.warning(f'Cannot find window "{window}"')
    return ret

  def kill_app(self, appname):
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

  def sendkeys(self, keys):
    pythoncom.CoInitialize()
    shell = win32com.client.Dispatch("WScript.Shell")
    shell.SendKeys(keys)
    return True


class RemoteEndpoint:
  def __init__(self, name, url, token):
    self.name = name
    self.url = url
    self.token = token

  def _remote_call(self, method, *arguments):
    r = requests.post(f'{self.url}/lowlevel/{method}', json={'arguments': [*arguments], 'token' : self.token})
    if 'result' in r.json():
      return r.json()['result']
    return False

  def execute(self, cmdline):
    try:
      logging.debug(f'Starting {cmdline}')
      return self._remote_call('execute', *cmdline)
    except:
      logging.error(f'Failed to launch {cmdline}')
    return -1

  def kill_pid(self, pid):
    if pid > 0:
      logging.debug(f'Killing {pid}')
      return self._remote_call('kill pid', pid)
    return False

  def close_window(self, window=None):
    return self._remote_call('close window', window)

  def kill_app(self, appname):
    return self._remote_call('kill app', appname)

  def sendkeys(self, keys):
    return self._remote_call('sendkeys', keys)
