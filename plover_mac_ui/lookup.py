from functools import partial

from AppKit import (
  NSCollectionViewFlowLayout,
  NSCollectionViewItem,
  NSColor,
  NSMakeSize,
  NSView,
)
from Foundation import NSObject
from objc import IBAction, IBOutlet, ivar, protocolNamed, super

from plover_mac_ui.async_utils import do_async
from plover_mac_ui.lookup_model import (
  Dictionary,
  LookupMethod,
  LookupResultReason,
  MAX_RESULTS,
)
from plover_mac_ui.lookup_word_list import (
  WordListItem,
  WordListItemView,
  WordListLayout,
  WordListController,
)
from plover_mac_ui.lookup_translation_list import (
  TranslationListItem,
  TranslationListItemView,
  TranslationListLayout,
  TranslationListController,
)
from plover_mac_ui.resources import nib_named
from plover_mac_ui.tool import Tool
from plover_mac_ui.utils import debounce

NSControlTextEditingDelegate = protocolNamed("NSControlTextEditingDelegate")
NSSplitViewDelegate = protocolNamed("NSSplitViewDelegate")
NSWindowDelegate = protocolNamed("NSWindowDelegate")

class LookupToolController(Tool, protocols=[
    NSControlTextEditingDelegate,
    NSSplitViewDelegate,
    NSWindowDelegate,
  ]):
  actionText = "Lookup"
  shortcut = "l"
  nibName = "Lookup"
  lookupMethod = IBOutlet()
  searchField = IBOutlet()
  splitView = IBOutlet()
  wordList = IBOutlet()
  translationList = IBOutlet()

  wordListController = ivar()
  translationListController = ivar()
  wordListNib = ivar()
  translationListNib = ivar()
  dictionary = ivar()

  def completeInit(self):
    self.engine.hook_connect("lookup", self.asyncShowWindow)
    self.engine.hook_connect("dictionaries_loaded", self.dictionariesDidLoad_)

    self.wordListNib = nib_named(WordListItem.nibName)
    self.translationListNib = nib_named(TranslationListItem.nibName)

    self.wordListController = WordListController.alloc().init()
    self.wordListController.setDelegate_(self)
    self.translationListController = TranslationListController.alloc().init()
    self.translationListController.setDelegate_(self)

  @property
  def lookupBy(self):
    return LookupMethod(self.lookupMethod.selectedSegment())

  def configureWordList(self):
    self.wordList.setCollectionViewLayout_(WordListLayout.alloc().init())
    self.wordList.setDelegate_(self.wordListController)
    self.wordList.setDataSource_(self.wordListController)
    self.wordList.setSelectable_(True)
    self.wordList.registerNib_forItemWithIdentifier_(self.wordListNib, WordListItem.identifier)
    self.translationList.setCollectionViewLayout_(TranslationListLayout.alloc().init())
    self.translationList.setDelegate_(self.translationListController)
    self.translationList.setDataSource_(self.translationListController)
    self.translationList.setSelectable_(True)
    self.translationList.registerNib_forItemWithIdentifier_(self.translationListNib, TranslationListItem.identifier)

  def dictionariesDidLoad_(self, dic):
    self.dictionary = dic
    do_async(self.clearResults)

  def clearResults(self):
    if self.lookupMethod is not None:
      self.searchField.setStringValue_("")
      self.wordListController.updateResults_full_lookingUpBy_([], [], self.lookupBy)
      self.translationListController.updateTranslations_lookingUpBy_([], self.lookupBy)

  @IBAction
  def changeLookupMethod_(self, _):
    self.performLookup()

  @debounce(0.1)
  def performLookup(self):
    approx_fn, lookup_fn = {
      LookupMethod.TRANSLATION: (Dictionary.approx_translations, Dictionary.find_by_translation),
      LookupMethod.STROKE: (Dictionary.approx_strokes, Dictionary.find_by_stroke),
    }[self.lookupBy]
    approx, lookup = partial(approx_fn, self.dictionary), partial(lookup_fn, self.dictionary)

    search_text = __import__("os").environ.get(
      "PLOVER_SEARCH", self.searchField.stringValue() or "")

    fullResults = {}
    results = []
    if search_text:
      for tl in approx(search_text):
        full_results, short_results = lookup(tl)
        fullResults[tl] = full_results
        results.extend(short_results)

    self.wordListController.updateResults_full_lookingUpBy_(results, fullResults, self.lookupBy)

  def forceRelayout(self):
    self.wordList.collectionViewLayout().invalidateLayout()
    self.wordList.reloadData()
    self.translationList.collectionViewLayout().invalidateLayout()
    self.translationList.reloadData()

  # MARK: NSWindowController

  def awakeFromNib(self):
    self.win.setDelegate_(self)
    self.splitView.setDelegate_(self)
    self.searchField.setDelegate_(self)
    self.lookupMethod.setAction_("changeLookupMethod:")
    self.lookupMethod.selectSegmentWithTag_(0)
    self.changeLookupMethod_(self)

  def windowDidLoad(self):
    self.configureWordList()

  # MARK: NSWindowDelegate

  def windowDidResize_(self, _):
    self.forceRelayout()

  # MARK: NSSplitViewDelegate

  def splitViewDidResizeSubviews_(self, _):
    self.forceRelayout()

  # MARK: NSControlTextEditingDelegate

  def controlTextDidChange_(self, _):
    self.performLookup()

  # MARK: WordListControllerDelegate

  def wordListDidUpdateResults(self):
    self.wordList.reloadData()

  def wordListDidSelectItem_withTranslations_lookingUpBy_(self, item, translations, lookup_by):
    self.translationListController.updateTranslations_lookingUpBy_(translations, lookup_by)

  # MARK: TranslationListControllerDelegate

  def translationListDidUpdateResults(self):
    self.translationList.reloadData()

  def translationListDidSelectItem_(self, item):
    pass
