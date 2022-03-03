import os
import os.path
import subprocess

from AppKit import (
  NSCompositeSourceIn,
  NSImage,
  NSMakeRect,
  NSNib,
  NSRectFillUsingOperation,
  NSZeroPoint,
)
from Foundation import NSBundle

PATH = os.path.dirname(os.path.abspath(__file__))
BUNDLE = NSBundle.bundleWithPath_(PATH)

_icons = {}
_nibs = {}

def icon_named(name, template=True):
  if (name, template) in _icons:
    return _icons[(name, template)]
  image = BUNDLE.imageForResource_(name)
  image.setTemplate_(template)
  _icons[(name, template)] = image
  return image

def nib_named(name):
  if name in _nibs:
    return _nibs[name]
  nib = NSNib.alloc().initWithNibNamed_bundle_(name, BUNDLE)
  _nibs[name] = nib
  return nib

def nib_path(name):
  return BUNDLE.pathForResource_ofType_(name, "nib")

def tintWithColor_(image, color):
  if not color:
    return image
  img = image.copy()
  img.lockFocus()
  color.set()
  rect = NSMakeRect(0, 0, img.size().width, img.size().height)
  NSRectFillUsingOperation(rect, NSCompositeSourceIn)
  img.unlockFocus()
  return img

NSImage.tintWithColor_ = tintWithColor_

plover_logo = icon_named("plover", template=False)
