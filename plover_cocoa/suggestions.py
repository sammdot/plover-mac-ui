import re

from AppKit import (
  NSAttributedString,
  NSFont,
  NSFontAttributeName,
  NSMutableAttributedString,
  NSMakeRange,
)
from objc import IBOutlet, protocolNamed

from plover.formatting import RetroFormatter
from plover.suggestions import Suggestion
from plover_cocoa.async_utils import do_async
from plover_cocoa.fonts import (
  SUGGESTIONS_FONT,
  suggestions_steno_font,
  to_halfwidth,
)
from plover_cocoa.steno import STROKE_DELIMITER
from plover_cocoa.tool import Tool

NSWindowDelegate = protocolNamed("NSWindowDelegate")

class SuggestionsToolController(Tool, protocols=[NSWindowDelegate]):
  actionText = "Suggestions"
  shortcut = "z"
  nibName = "Suggestions"

  tape = IBOutlet()

  WORD_RX = re.compile(r'(?:\w+|[^\w\s]+)\s*')

  def completeInit(self):
    self._last_suggestions = None
    self.engine.hook_connect("suggestions", self.asyncShowWindow)
    self.engine.hook_connect("translated", self.didTranslateFrom_to_)

  def scrollToBottom(self):
    do_async(
      self.tape.scrollRangeToVisible_,
      NSMakeRange(self.tape.string().length(), 0),
    )

  @staticmethod
  def tails_(lst):
    for i in range(len(lst)):
      yield lst[i:]

  def didTranslateFrom_to_(self, old, new):
    for a in reversed(new):
      if a.text and not a.text.isspace():
        break
    else:
      return

    with self.engine:
      last_translations = self.engine.translator_state.translations
      retro_formatter = RetroFormatter(last_translations)
      split_words = retro_formatter.last_words(10, rx=self.WORD_RX)

    suggestion_list = []
    for phrase in self.tails_(split_words):
      phrase = ''.join(phrase)
      suggestion_list.extend(self.engine.get_suggestions(phrase))

    if not suggestion_list and split_words:
      suggestion_list = [Suggestion(split_words[-1], [])]

    if suggestion_list and suggestion_list != self._last_suggestions:
      self._last_suggestions = suggestion_list
      self.showSuggestions_(suggestion_list)

  def showSuggestions_(self, suggestion_list):
    if not self.tape:
      return

    self.tape.setString_("")

    for sug in suggestion_list:
      word = NSMutableAttributedString.alloc().initWithString_attributes_(
        f"{sug.text}\n", { NSFontAttributeName: SUGGESTIONS_FONT })
      for steno in sug.steno_list:
        stroke = STROKE_DELIMITER.join(steno)
        word.appendAttributedString_(
          NSAttributedString.alloc().initWithString_attributes_(
            f"  {stroke}\n",
            { NSFontAttributeName: suggestions_steno_font(stroke) }))
      word.appendAttributedString_(
        NSAttributedString.alloc().initWithString_attributes_(
          "\n", { NSFontAttributeName: SUGGESTIONS_FONT }))
      self.tape.textStorage().appendAttributedString_(word)

    self.scrollToBottom()
