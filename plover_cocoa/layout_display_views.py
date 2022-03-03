from AppKit import (
  NSBezierPath,
  NSColor,
  NSFont,
  NSFontAttributeName,
  NSForegroundColorAttributeName,
  NSGraphicsContext,
  NSRectFill,
  NSView,
)
from Foundation import NSAttributedString, NSMakePoint
from objc import ivar, super

from plover_cocoa import colors
from plover_cocoa.fonts import key_name_font, SMALL_KEY_NAME_FONT

class DisplayView(NSView):
  clickHandler = ivar()

  def setClickHandler_(self, fn):
    self.clickHandler = fn

  def mouseDown_(self, event):
    if not self.clickHandler:
      return
    self.clickHandler(event)

  def drawRect_(self, rect):
    NSColor.clearColor().set()
    NSRectFill(rect)

class StenotypeDisplayView(DisplayView): pass
class StenographDisplayView(DisplayView): pass
class SplitoDisplayView(DisplayView): pass
class PreonicDisplayView(DisplayView): pass
class UniDisplayView(DisplayView): pass
class ZenDisplayView(DisplayView): pass
class QwertyDisplayView(DisplayView): pass

class StenoKeyView(DisplayView):
  disabled = ivar()
  rounded = ivar()
  roundSide = ivar()
  highlighted = ivar()
  darkOutlineWhenDisabled = ivar()
  showFullLabel = ivar()
  fullLabel = ivar()
  label = ivar()

  DARK = colors.DARK
  SEMI_DARK = colors.SEMI_DARK
  LIGHT = colors.LIGHT

  def drawRect_(self, rect):
    super(StenoKeyView, self).drawRect_(rect)

    NSGraphicsContext.currentContext().setShouldAntialias_(True)

    size = rect.size
    radius = (size.width - 10 if self.roundSide else size.width) / 2
    path = NSBezierPath.bezierPath()
    path.setLineWidth_(1.5)

    path.moveToPoint_(NSMakePoint(1, size.height - 1))
    path.lineToPoint_(NSMakePoint(size.width - 1, size.height - 1))
    if self.rounded and self.roundSide:
      if self.roundSide == "right":
        path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
          NSMakePoint(size.width - radius, radius), radius - 1, 0.0, 180.0, True)
        path.lineToPoint_(NSMakePoint(1, radius))
      elif self.roundSide == "left":
        path.lineToPoint_(NSMakePoint(size.width - 1, radius))
        path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
          NSMakePoint(radius, radius), radius - 1, 0.0, 180.0, True)
    elif self.rounded:
      path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
        NSMakePoint(radius, radius), radius - 1, 0.0, 180.0, True)
    else:
      path.lineToPoint_(NSMakePoint(size.width - 1, 1))
      path.lineToPoint_(NSMakePoint(1, 1))
    path.closePath()

    if self.disabled:
      (self.SEMI_DARK if self.darkOutlineWhenDisabled else self.LIGHT).set()
      path.stroke()
      return

    (self.DARK if self.highlighted else self.LIGHT).set()
    path.fill()
    self.DARK.set()
    path.stroke()

    if self.label:
      label_color = NSColor.whiteColor() if self.highlighted else self.DARK
      label = NSAttributedString.alloc().initWithString_attributes_(
        self.fullLabel if \
          self.frame().size.width >= 3 * self.frame().size.height \
          or (self.showFullLabel and len(self.fullLabel) < 3) else self.label,
        {
          NSFontAttributeName:
            SMALL_KEY_NAME_FONT if len(self.label) >= 3 else
              key_name_font(self.label),
          NSForegroundColorAttributeName: label_color,
        })
      label_size = label.size()
      origin = NSMakePoint(size.width / 2 - label_size.width / 2, size.height / 2 - label_size.height / 2 + 2)
      if self.roundSide:
        origin.x += (size.width - 2 * radius) / 3 * (1 if self.roundSide == "right" else -1)
      if self.rounded:
        origin.y += 2
      if len(self.label) >= 3:
        origin.y -= 1
      label.drawAtPoint_(origin)
