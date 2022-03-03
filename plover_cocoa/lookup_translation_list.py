from AppKit import (
  NSCollectionViewFlowLayout,
  NSCollectionViewItem,
  NSColor,
  NSMakeSize,
  NSTokenStyleNone,
  NSTokenStylePlainSquared,
  NSTokenStyleSquared,
  NSView,
)
from Foundation import NSObject
from objc import IBOutlet, ivar, protocolNamed

from plover_cocoa.fonts import lookup_steno_font
from plover_cocoa.lookup_format import display_string, format_for_translation_list, TokenType
from plover_cocoa.lookup_model import LookupMethod, LookupResultReason
from plover_cocoa.resources import tintWithColor_
from plover_cocoa.steno import STROKE_DELIMITER

NSCollectionViewDataSource = protocolNamed("NSCollectionViewDataSource")
NSCollectionViewDelegate = protocolNamed("NSCollectionViewDelegate")
NSCollectionViewDelegateFlowLayout = protocolNamed("NSCollectionViewDelegateFlowLayout")
NSCollectionViewElement = protocolNamed("NSCollectionViewElement")
NSTokenFieldDelegate = protocolNamed("NSTokenFieldDelegate")

class TranslationListItemView(NSView):
  selected = ivar()
  reason = ivar()

  @property
  def backColor(self):
    return NSColor.controlAccentColor() if self.selected else NSColor.clearColor()

  @property
  def iconColor(self):
    return NSColor.whiteColor() if self.selected else \
      NSColor.systemGreenColor() if self.reason == LookupResultReason.DEFINED else \
      NSColor.systemRedColor() if self.reason == LookupResultReason.DISABLED else \
      NSColor.tertiaryLabelColor()

  @property
  def strokeTextColor(self):
    return NSColor.whiteColor() if self.selected else \
      NSColor.labelColor() if self.reason == LookupResultReason.DEFINED else \
      NSColor.tertiaryLabelColor()

  @property
  def dictionaryTextColor(self):
    return NSColor.whiteColor() if self.selected else \
      NSColor.secondaryLabelColor() if self.reason == LookupResultReason.DEFINED else \
      NSColor.tertiaryLabelColor()

  @property
  def commentTextColor(self):
    return NSColor.whiteColor() if self.selected else NSColor.tertiaryLabelColor()

  @property
  def icon(self):
    return self.subviews()[0].subviews()[0]

  @property
  def innerStack(self):
    return self.subviews()[0].subviews()[1]

  @property
  def innerInnerStack(self):
    return self.innerStack.subviews()[1]

  @property
  def strokeField(self):
    return self.innerStack.subviews()[0]

  @property
  def dictionaryField(self):
    return self.subviews()[0].subviews()[2]

  @property
  def translationField(self):
    return self.innerInnerStack.subviews()[0]

  @property
  def commentField(self):
    return self.innerInnerStack.subviews()[1]

  def redraw(self):
    self.setWantsLayer_(True)
    self.icon.setImage_(self.reason.icon.tintWithColor_(self.iconColor))
    self.layer().setBackgroundColor_(self.backColor.CGColor())
    self.strokeField.setTextColor_(self.strokeTextColor)
    self.translationField.setTextColor_(self.strokeTextColor)
    self.dictionaryField.setTextColor_(self.dictionaryTextColor)
    self.commentField.setTextColor_(self.commentTextColor)

  def setContentsWithStroke_translation_comment_dictionary_reason_(self, stroke, translation, comment, dictionary, reason):
    self.reason = reason
    self.strokeField.setStringValue_(stroke)
    self.strokeField.setFont_(lookup_steno_font(stroke))
    self.translationField.setObjectValue_(format_for_translation_list(translation))
    self.dictionaryField.setStringValue_(dictionary)
    self.commentField.setStringValue_(comment)
    self.redraw()
    self.setNeedsDisplay_(True)

  def setSelected_(self, selected):
    self.selected = selected
    self.redraw()
    self.setNeedsDisplay_(True)

  def draw_(self, dirty_rect):
    self.redraw()
    super(TranslationListItemView, self).draw_(dirty_rect)

class TranslationListItem(NSCollectionViewItem, protocols=[
    NSCollectionViewElement,
    NSTokenFieldDelegate,
  ]):
  nibName = "TranslationListItem"
  identifier = "translationListItemIdentifier"

  @property
  def defined(self):
    return self.representedObject().reason != LookupResultReason.UNDEFINED

  @property
  def stroke(self):
    return STROKE_DELIMITER.join(self.representedObject().strokes[0]) if self.defined else None

  def updateWithObject_lookingUpBy_(self, obj, lookup_by):
    self.setRepresentedObject_(obj)
    self.view().translationField.setDelegate_(self)
    self.view().setContentsWithStroke_translation_comment_dictionary_reason_(
      self.stroke, obj.translation, obj.comment or "", obj.dictionary, obj.reason)

  def setSelected_(self, selected):
    super(TranslationListItem, self).setSelected_(selected)
    self.view().setSelected_(selected)

  def tokenField_styleForRepresentedObject_(self, field, obj):
    return NSTokenStyleNone if obj[0] == TokenType.STRING else NSTokenStyleSquared

  def tokenField_displayStringForRepresentedObject_(self, field, obj):
    return display_string(obj)

class TranslationListLayout(NSCollectionViewFlowLayout):
  def init(self):
    self = super(TranslationListLayout, self).init()
    if self is None: return None

    self.setMinimumLineSpacing_(0)
    return self

class TranslationListController(NSObject, protocols=[
    NSCollectionViewDelegate,
    NSCollectionViewDelegateFlowLayout,
    NSCollectionViewDataSource,
  ]):
  selection = ivar()
  translations = ivar()
  lookupBy = ivar()
  delegate = ivar()

  def init(self):
    self = super(TranslationListController, self).init()
    if self is None: return None

    self.translations = []
    return self

  def setDelegate_(self, delegate):
    self.delegate = delegate

  def updateTranslations_lookingUpBy_(self, translations, lookup_by):
    self.translations = translations
    self.lookupBy = lookup_by
    self.delegate.translationListDidUpdateResults()

  # MARK: NSCollectionViewDataSource

  def numberOfSectionsInCollectionView_(self, view):
    return 1

  def collectionView_numberOfItemsInSection_(self, view, section):
    return len(self.translations)

  def collectionView_itemForRepresentedObjectAtIndexPath_(self, view, path):
    item = view.makeItemWithIdentifier_forIndexPath_(TranslationListItem.identifier, path)
    if item is None:
      item = NSCollectionViewItem.alloc().init()
    item.__class__ = TranslationListItem
    item.updateWithObject_lookingUpBy_(self.translations[path.item()], self.lookupBy)
    return item

  # MARK: NSCollectionViewDelegateFlowLayout

  def collectionView_layout_sizeForItemAtIndexPath_(self, view, layout, path):
    return NSMakeSize(view.frame().size.width, 48)

  # MARK: NSCollectionViewDelegate

  def collectionView_didSelectItemsAtIndexPaths_(self, view, paths):
    if self.selection is not None:
      self.selection.setSelected_(False)
      self.selection = None

    paths = list(paths)
    if len(paths) > 1:
      return

    if not paths:
      self.delegate.translationListDidSelectItem_(None)
      return

    index = paths[0].item()
    self.selection = item = view.itemAtIndex_(index)
    item.setSelected_(True)
    if self.delegate:
      self.delegate.translationListDidSelectItem_(self.translations[index])
