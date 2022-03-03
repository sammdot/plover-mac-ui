from AppKit import (
  NSCollectionViewFlowLayout,
  NSCollectionViewItem,
  NSColor,
  NSMakeSize,
  NSView,
)
from Foundation import NSObject
from objc import IBOutlet, ivar, protocolNamed

from plover_cocoa.fonts import suggestions_steno_font
from plover_cocoa.lookup_format import format_for_word_list
from plover_cocoa.lookup_model import LookupMethod
from plover_cocoa.steno import STROKE_DELIMITER

NSCollectionViewDataSource = protocolNamed("NSCollectionViewDataSource")
NSCollectionViewDelegate = protocolNamed("NSCollectionViewDelegate")
NSCollectionViewDelegateFlowLayout = protocolNamed("NSCollectionViewDelegateFlowLayout")
NSCollectionViewElement = protocolNamed("NSCollectionViewElement")

class WordListItemView(NSView):
  selected = ivar()
  badTranslation = ivar()

  @property
  def backColor(self):
    return NSColor.controlAccentColor() if self.selected else NSColor.clearColor()

  @property
  def textColor(self):
    return NSColor.whiteColor() if self.selected else \
      NSColor.tertiaryLabelColor() if self.badTranslation else NSColor.labelColor()

  @property
  def translationField(self):
    return self.subviews()[0]

  @property
  def strokeField(self):
    return self.subviews()[1]

  def redraw(self):
    self.setWantsLayer_(True)
    self.layer().setBackgroundColor_(self.backColor.CGColor())
    self.translationField.setTextColor_(self.textColor)
    self.strokeField.setTextColor_(self.textColor)

  def setContentsWithStrokes_translation_bad_(self, strokes, translation, bad):
    self.badTranslation = bad or False
    self.translationField.setAttributedStringValue_(format_for_word_list(translation, bad))
    steno = "\n".join(STROKE_DELIMITER.join(stroke) for stroke in strokes)
    self.strokeField.setStringValue_(steno)
    self.strokeField.setFont_(suggestions_steno_font(steno))
    self.redraw()

  def setSelected_(self, selected):
    self.selected = selected
    self.redraw()
    self.setNeedsDisplay_(True)

  def draw_(self, dirty_rect):
    self.redraw()
    super(WordListItemView, self).draw_(dirty_rect)

class WordListItem(NSCollectionViewItem, protocols=[NSCollectionViewElement]):
  nibName = "WordListItem"
  identifier = "wordListItemIdentifier"

  def updateWithObject_(self, obj):
    self.setRepresentedObject_(obj)
    self.view().setContentsWithStrokes_translation_bad_(obj.strokes, obj.translation, obj.bad)

  def setSelected_(self, selected):
    super(WordListItem, self).setSelected_(selected)
    self.view().setSelected_(selected)

class WordListLayout(NSCollectionViewFlowLayout):
  def init(self):
    self = super(WordListLayout, self).init()
    if self is None: return None

    self.setMinimumLineSpacing_(0)
    return self

class WordListController(NSObject, protocols=[
    NSCollectionViewDelegate,
    NSCollectionViewDelegateFlowLayout,
    NSCollectionViewDataSource,
  ]):
  selection = ivar()
  results = ivar()
  fullResults = ivar()
  lookupBy = ivar()
  delegate = ivar()

  def init(self):
    self = super(WordListController, self).init()
    if self is None: return None

    self.results = []
    self.fullResults = {}
    return self

  def setDelegate_(self, delegate):
    self.delegate = delegate

  def updateResults_full_lookingUpBy_(self, short, full, lookup_by):
    self.fullResults = full
    self.results = short
    self.lookupBy = lookup_by
    if self.delegate:
      self.delegate.wordListDidUpdateResults()

  # MARK: NSCollectionViewDataSource

  def numberOfSectionsInCollectionView_(self, view):
    return 1

  def collectionView_numberOfItemsInSection_(self, view, section):
    return len(self.results)

  def collectionView_itemForRepresentedObjectAtIndexPath_(self, view, path):
    item = view.makeItemWithIdentifier_forIndexPath_(WordListItem.identifier, path)
    if item is None:
      item = NSCollectionViewItem.alloc().init()
    item.__class__ = WordListItem
    item.updateWithObject_(self.results[path.item()])
    return item

  # MARK: NSCollectionViewDelegateFlowLayout

  def collectionView_layout_sizeForItemAtIndexPath_(self, view, layout, path):
    item = self.results[path.item()] or []
    if not item.strokes:
      return NSMakeSize(view.frame().size.width, 0)
    return NSMakeSize(view.frame().size.width, (len(item.strokes) + 1) * 22 + 6)

  # MARK: NSCollectionViewDelegate

  def collectionView_didSelectItemsAtIndexPaths_(self, view, paths):
    if self.selection is not None:
      self.selection.setSelected_(False)
      self.selection = None

    paths = list(paths)
    if len(paths) > 1:
      return

    if not paths:
      self.delegate.wordListDidSelectItem_withTranslations_lookingUpBy_(None, [], self.lookupBy)
      return

    index = paths[0].item()
    self.selection = item = view.itemAtIndex_(index)
    item.setSelected_(True)
    if self.delegate:
      self.delegate.wordListDidSelectItem_withTranslations_lookingUpBy_(
        self.results[index], self.fullResults[
          self.results[index].translation if self.lookupBy == LookupMethod.TRANSLATION
          else self.results[index].strokes[0]], self.lookupBy)
