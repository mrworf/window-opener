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
from infi.systray import SysTrayIcon

class Menu:
  def __init__(self, reloadFunc, shutdownFunc, aboutFunc):
    menu = (
      ("Reload config", None, reloadFunc),
      ("About...", None, aboutFunc)
    )
    self.systray = SysTrayIcon("icon.ico", "Window Opener", menu, on_quit=shutdownFunc)

  def start(self):
    self.systray.start()
