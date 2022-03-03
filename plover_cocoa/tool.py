from AppKit import NSApplication, NSWindowController
from objc import IBOutlet, super

from plover_cocoa.async_utils import do_async
from plover_cocoa.resources import nib_path

class Tool(NSWindowController):
  enabled = True
  actionText = None
  shortcut = None
  nibName = None
  win = IBOutlet()

  def initWithEngine_(self, engine):
    self = super(Tool, self).initWithWindowNibPath_owner_(nib_path(self.nibName), self)
    if self is None: return None

    self.engine = engine
    engine.hook_connect("config_changed", self.configDidChange_)
    self.completeInit()
    return self

  def awakeFromNib(self):
    self.configDidChange_(self.engine.config)

  def canBecomeKeyWindow(self):
    return True

  def showWindow_(self, sender):
    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    super(Tool, self).showWindow_(sender)
    if not self.win.isVisible():
      self.win.center()
    self.win.makeKeyAndOrderFront_(sender)
    self.win.orderFrontRegardless()

  def asyncShowWindow(self):
    do_async(self.showWindow_, self)

  def completeInit(self):
    pass

  def configDidChange_(self, config):
    pass
