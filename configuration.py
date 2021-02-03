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
import os
import yaml
import logging

from programs import ProgramManager, Action

class Config:
  def __init__(self):
    self.LOWLEVEL_TOKEN = None
    self.pm = ProgramManager()
    self.secrets = {}

  def getToken(self):
    return self.LOWLEVEL_TOKEN

  def getProgramManager(self):
    return self.pm

  def load(self):
    # First, load all secrets (if any)
    if os.path.exists('secrets.yml'):
      with open('secrets.yml') as f:
        data = yaml.safe_load(f)
        if 'secrets' in data and not isinstance(data['secrets'], dict):
          logging.error('secrets is not a dict')
        elif 'secrets' in data:
          self.secrets = data['secrets']

        self.LOWLEVEL_TOKEN = data.get('token', None)
    else:
      logging.warning('You don\'t have a secrets.yml, please don\'t put your secrets in the config.yml')

    if not self.LOWLEVEL_TOKEN:
      logging.warning('Without token defined in secrets.yml, the REST endpoints are disabled.')

    if os.path.exists('config.yml'):
      with open('config.yml') as f:
        txt = f.read()
        data = yaml.safe_load(txt.format_map(self.secrets))
        if 'endpoints' in data:
          # Create end-points
          for name in data['endpoints']:
            self.pm.createEndpoint(name.lower(), data['endpoints'][name]['url'], data['endpoints'][name]['token'])
        for name in data.get('programs', {}):
          prg = self.pm.createProgram(name)
          for item in data['programs'][name].get('start', []):
            endpoint = self.pm.getEndpoint(item.get('endpoint', 'local').lower())
            method = item.get('method', '').lower()
            arguments = item.get('arguments', [])
            if method not in Action.METHOD_START:
              logging.error(f"{method} isn't a supported start method")
              continue
            if not endpoint:
              logging.error(f"endpoint isn't available for program {name}")
              continue
            if not isinstance(arguments, list):
              arguments = [arguments]
            prg.addStartAction(endpoint, method, *arguments)

          for item in data['programs'][name].get('stop', []):
            endpoint = self.pm.getEndpoint(item.get('endpoint', 'local').lower())
            method = item.get('method', '').lower()
            arguments = item.get('arguments', [])
            if method not in Action.METHOD_STOP:
              logging.error(f"{method} isn't a supported stop method")
              continue
            if not endpoint:
              logging.error(f"endpoint isn't available for program {name}")
              continue
            if not isinstance(arguments, list):
              arguments = [arguments]
            prg.addStopAction(endpoint, method, *arguments)
