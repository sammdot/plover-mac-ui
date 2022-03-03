from threading import Timer

from AppKit import (
  NSAttributedString,
  NSColor,
  NSFont,
  NSFontAttributeName,
  NSForegroundColorAttributeName,
  NSKernAttributeName,
  NSMakeRange,
  NSMutableAttributedString,
  NSTextAlignmentCenter,
)
from objc import IBOutlet, ivar

from plover import system
from plover_mac_ui.async_utils import do_async
from plover_mac_ui.fonts import (
  is_korean,
  key_list_bold_font,
  key_list_font,
  to_halfwidth,
)
from plover_mac_ui.layout_display_views import *
from plover_mac_ui.layout_display_controllers import *
from plover_mac_ui.layout_model import display_controller_for, STROKE_TIMEOUT
from plover_mac_ui.resources import BUNDLE
from plover_mac_ui.steno_layout import remove_numbers
from plover_mac_ui.tool import Tool

class LayoutDisplayController(Tool):
  actionText = "Layout Display"
  shortcut = "s"
  nibName = "LayoutDisplay"
  strokeLabel = IBOutlet()
  display = IBOutlet()

  displayController = ivar()
  timer = ivar()

  def awakeFromNib(self):
    self.win.setBackgroundColor_(NSColor.whiteColor())
    self.displayController = None
    self.configDidChange_(self.engine.config)

  def completeInit(self):
    self.engine.hook_connect("stroked", self.didStroke_)

  def configDidChange_(self, config):
    if "machine_type" in config and self.display is not None:
      self.machineDidChange_(config["machine_type"])
    if self.strokeLabel:
      self.displayStroke_([])

  @property
  def displayView(self):
    return self.displayController.view() if self.displayController else None

  def machineDidChange_(self, machine):
    if not self.display:
      return

    try:
      self.displayController = \
        display_controller_for(machine).alloc().initWithEngine_(self.engine)
    except KeyError:
      return

    for view in self.display.subviews():
      if view is not self.displayView:
        view.removeFromSuperview()

    def _changeDisplayController():
      self.display.addSubview_(self.displayView),
      self.displayView.setNeedsDisplay_(True),
      self.display.layout(),
    do_async(_changeDisplayController)

  def didStroke_(self, stroke):
    if not self.display:
      return
    if self.timer:
      self.timer.cancel()
      self.timer = None
    keys, _ = remove_numbers(stroke.steno_keys[:], stroke.rtfcre)
    self.displayStroke_(keys)
    self.timer = Timer(STROKE_TIMEOUT, lambda: self.displayStroke_([]))
    self.timer.start()

  def labelForKeys_(self, keys):
    string = NSMutableAttributedString.alloc().init()
    keys = set(keys)
    for key in system.KEYS:
      string.appendAttributedString_(
        NSAttributedString.alloc().initWithString_attributes_(
          to_halfwidth(key.replace("-", "")), {
            NSFontAttributeName:
              key_list_bold_font(key) if key in keys else key_list_font(key),
            NSForegroundColorAttributeName:
              StenoKeyView.DARK if key in keys else StenoKeyView.LIGHT,
          }))

    ALL = NSMakeRange(0, len(system.KEYS))
    string.setAlignment_range_(NSTextAlignmentCenter, ALL)
    if not any(map(is_korean, system.KEYS)):
      string.addAttribute_value_range_(NSKernAttributeName, 3, ALL)
    return string

  def displayStroke_(self, keys):
    if not all(key in system.KEYS for key in keys):
      return

    def _displayStroke():
      self.strokeLabel.setAttributedStringValue_(self.labelForKeys_(keys)),
      self.displayController.displayStroke_(keys),
      self.displayView.setNeedsDisplay_(True),
    do_async(_displayStroke)
