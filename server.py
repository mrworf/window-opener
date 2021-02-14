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
from flask import Flask
from threading import Thread

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
