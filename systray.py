from infi.systray import SysTrayIcon

class Menu:
  def __init__(self, reloadFunc, shutdownFunc):
    self.reloadFunc = reloadFunc
    self.shutdownFunc = shutdownFunc
    menu = (("Reload config", None, self.reloadFunc),)
    self.systray = SysTrayIcon("icon.ico", "Window Opener", menu, on_quit=self.shutdownFunc)

  def start(self):
    self.systray.start()
