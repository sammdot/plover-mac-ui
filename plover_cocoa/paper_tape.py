from AppKit import (
  NSFont,
  NSFontAttributeName,
  # NSForegroundColorAttributeName,
  NSMakeRange,
)
from Foundation import NSAttributedString
from objc import IBOutlet

from plover import system
from plover_cocoa.async_utils import do_async
from plover_cocoa.colors import DARK
from plover_cocoa.fonts import is_zh_ja, is_korean, to_halfwidth, paper_tape_font
from plover_cocoa.tool import Tool

LINES = 40

class PaperTapeController(Tool):
  actionText = "Paper Tape"
  shortcut = "t"
  nibName = "PaperTape"
  tape = IBOutlet()

  def completeInit(self):
    self._numbers = None
    self._all_keys = []
    self.engine.hook_connect("stroked", self.didStroke_)

  def awakeFromNib(self):
    self.configDidChange_(self.engine.config)
    self.tape.enclosingScrollView().setHasVerticalScroller_(False)

  def configDidChange_(self, config):
    self._numbers = set(system.NUMBERS.values())
    self._all_keys = "".join(key.strip("-") for key in system.KEYS)
    if self.tape:
      self.tape.setString_("\n" * LINES)
      self.scrollToBottom()
      font = paper_tape_font(self._all_keys)
      self.tape.setFont_(font)

      test_str = NSAttributedString.alloc().initWithString_attributes_(
        "".join(["\u3000" if is_zh_ja(key) else " " for key in self._all_keys]),
        { NSFontAttributeName: font })
      frame = self.win.frame()
      frame.size.width = test_str.size().width + 10
      self.win.setFrame_display_(frame, True)

  def appendToTape_(self, string):
    if not self.tape:
      return

    self.tape.setString_(f"{self.tape.string()}\n{string}")
    self.tape.setTextColor_(DARK)
    self.scrollToBottom()

  def scrollToBottom(self):
    do_async(
      self.tape.scrollRangeToVisible_,
      NSMakeRange(self.tape.string().length(), 0),
    )

  def paperFormat_(self, stroke):
    text = list(" " * len(self._all_keys))
    keys = stroke.steno_keys[:]
    if any(key in self._numbers for key in keys):
      keys.append('#')
    for key in keys:
      index = system.KEY_ORDER[key]
      text[index] = self._all_keys[index]
    if is_korean(text):
      text = "".join([to_halfwidth(ch) for ch in text])
    elif is_zh_ja(text):
      for i, char in enumerate(text):
        if char == " " and is_zh_ja(self._all_keys[i]):
          text[i:i + 1] = ["\u3000"]
    return ''.join(text)

  def didStroke_(self, stroke):
    self.appendToTape_(self.paperFormat_(stroke))
