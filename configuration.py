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
    self.pm = None
    self.secrets = {}

  def getToken(self):
    return self.LOWLEVEL_TOKEN

  def getProgramManager(self):
    return self.pm

  def _read_with_substitution(self, file, subst):
    if os.path.exists(file):
      with open(file) as f:
        txt = f.read()
        data = yaml.safe_load(txt.format_map(subst))
        return data
    return {}

  def load(self):
    # Wipe out existing configuration
    self.pm = ProgramManager()
    self.secrets = {}

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

    data = self._read_with_substitution('config.yml', self.secrets)
    if data:
      if 'endpoints' in data:
        # Create end-points
        for name in data['endpoints']:
          if 'url' in data['endpoints'][name] and 'token' in data['endpoints'][name]:
            self.pm.createEndpoint(name.lower(), data['endpoints'][name]['url'], data['endpoints'][name]['token'])
          else:
            logging.error(f'Endpoint "{name}" cannot be created since it\'s missing url, token or both')

      for name in data.get('programs', {}):

        # Make sure we substitute this entry with the included one if defined
        if 'include' in data['programs'][name]:
          replace = self._read_with_substitution(
            data['programs'][name]['include'],
            data['programs'][name].get('parameters', {})
          )
          if not replace:
            logging.error(f'File {data["programs"][name]["include"]} is missing or corrupt')
            continue
          data['programs'][name] = replace

        if 'start' not in data['programs'][name] and 'stop' not in data['programs'][name]:
          logging.error(f'Program "{name}" doesn\'t have any defined actions')
          continue

        prg = self.pm.createProgram(name)
        for item in data['programs'][name].get('start', []):
          endpoint = self.pm.getEndpoint(item.get('endpoint', 'local').lower())
          method = item.get('method', '').lower()
          arguments = item.get('arguments', [])
          options = item.get('options', None)
          if method not in Action.METHOD_START:
            logging.error(f"{method} isn't a supported start method (program \"{data['programs'][name]}\")")
            continue
          if not endpoint:
            logging.error(f"endpoint \"{item.get('endpoint', 'local').lower()}\" isn't available (program \"{data['programs'][name]}\")")
            continue
          if not isinstance(arguments, list):
            arguments = [arguments]
          action = prg.addStartAction(endpoint, method, *arguments)
          if options:
            action.setOptions(options)

        for item in data['programs'][name].get('stop', []):
          endpoint = self.pm.getEndpoint(item.get('endpoint', 'local').lower())
          method = item.get('method', '').lower()
          arguments = item.get('arguments', [])
          options = item.get('options', None)
          if method not in Action.METHOD_STOP:
            logging.error(f"{method} isn't a supported stop method (program \"{data['programs'][name]}\")")
            continue
          if not endpoint:
            logging.error(f"endpoint \"{item.get('endpoint', 'local').lower()}\" isn't available (program \"{data['programs'][name]}\")")
            continue
          if not isinstance(arguments, list):
            arguments = [arguments]
          action = prg.addStopAction(endpoint, method, *arguments)
          if options:
            action.setOptions(options)
    else:
      logging.error('No "config.yml" found')
