import os

from AppKit import (
  NSAlert,
  NSApplication,
  NSAttributedString,
  NSFont,
  NSFontAttributeName,
  NSMakeRect,
  NSTextView,
)
from PyObjCTools import AppHelper

from plover import log
from plover.oslayer import keyboardcontrol
from plover.registry import registry
from plover_mac_ui.app_delegate import AppDelegate
from plover_mac_ui.engine import Engine
from plover_mac_ui.fonts import DEFAULT_FONT
from plover_mac_ui.resources import plover_logo
from plover_mac_ui.utils import every

class KeyboardEmulation(keyboardcontrol.KeyboardEmulation):
  LIMIT_PER_STRING = 20

  def __init__(self):
    super(keyboardcontrol.KeyboardEmulation, self).__init__()
    self.improved = True

  def send_string(self, s):
    if not self.improved:
      return super().send_string(s)

    if "\n" in s:
      parts = s.split("\n")
      parts = sum([[part, "\n"] for part in parts[:-1]], []) + [parts[-1]]
      for part in parts:
        if not part:
          continue
        if part == "\n":
          self._send_sequence([(36, True)])
        else:
          self.send_string(part)
      return

    for substr in every(self.LIMIT_PER_STRING, s):
      self._send_string_press(substr)

def show_error(title, body):
  alert = NSAlert.alloc().init()
  alert.setIcon_(plover_logo)
  alert.setMessageText_(title)
  acc_view = NSTextView.alloc().initWithFrame_(NSMakeRect(0, 0, 200, 200))
  acc_view.insertText_(
    NSAttributedString.alloc().initWithString_attributes_(
      body, { NSFontAttributeName: DEFAULT_FONT }))
  acc_view.setEditable_(False)
  acc_view.setDrawsBackground_(False)
  alert.setAccessoryView_(acc_view)
  alert.layout()
  res = alert.runModal()

def main(config, controller):
  engine = Engine(config, controller, KeyboardEmulation())
  if not engine.load_config():
    return 3

  # Add Mac UI tools as a plugin type
  registry.PLUGIN_TYPES += ("gui.mac.tool",)
  registry._plugins["gui.mac.tool"] = {}
  registry.update()

  # Add hooks
  engine.HOOKS.append("emulation_changed")
  engine._hooks["emulation_changed"] = []

  # Patch to override the built-in RTF/CRE dictionary plugin
  from better_rtf import RtfDictionary
  registry.register_plugin("dictionary", "rtf", RtfDictionary)

  delegate = AppDelegate.alloc().initWithEngine_(engine)
  NSApplication.sharedApplication().setDelegate_(delegate)

  engine.start()
  try:
    AppHelper.runEventLoop()
  except KeyboardInterrupt:
    engine.quit()
  return engine.join()
