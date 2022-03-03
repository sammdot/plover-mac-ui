from AppKit import NSMenu, NSMenuItem, NSOffState, NSOnState, NSViewController
from Quartz import CGPointMake
from objc import IBOutlet, ivar, super

from plover_cocoa.async_utils import do_async
from plover_cocoa.resources import BUNDLE

class DisplayController(NSViewController):
  nibName = None
  engine = ivar()
  keymap = ivar()
  reverse_keymap = ivar()
  machine_keymap = ivar()
  actionMenu = ivar()
  selection = ivar()
  delegate = ivar()

  def initWithEngine_(self, engine):
    self = super(DisplayController, self).initWithNibName_bundle_(self.nibName, BUNDLE)
    if self is None: return None
    self.engine = engine
    self.engine.hook_connect("config_changed", self.configDidChange_)
    self.keymap = {}
    return self

  def awakeFromNib(self):
    self.configureKeymap()
    self.actionMenu = NSMenu.alloc().initWithTitle_("")
    self.actionMenu.setAutoenablesItems_(False)
    self.configDidChange_(self.engine.config)

  def setDelegate_(self, delegate):
    self.delegate = delegate

  def configureKeymap(self):
    pass

  def configDidChange_(self, config):
    self.machine_keymap = self.engine.config["system_keymap"]
    self.reverse_keymap = {
      view: [key for key in self.keymap if self.keymap[key] == view]
      for view in self.keymap.values()
    }

    noops = {view for view, keys in self.reverse_keymap.items()
      if all(self.machine_keymap.get_action(key) in {None, "no-op"}
        for key in keys)}
    for view in self.reverse_keymap:
      view.disabled = view in noops
      labels = {self.machine_keymap.get_action(key) for key in self.reverse_keymap[view]}
      labels.discard(None)
      view.fullLabel = list(labels)[0] if labels else ""
      view.label = view.fullLabel.replace("-", "")[:3]
      view.setNeedsDisplay_(True)

    if not self.actionMenu:
      return
    self.actionMenu.removeAllItems()
    actions = ["no-op"] + [act for act in self.machine_keymap.get_actions() if act != "no-op"]
    for action in actions:
      item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
         action, "selectMappingForKey:", "")
      item.setEnabled_(True)
      item.setTarget_(self)
      item.setState_(NSOffState)
      item.setRepresentedObject_(action)
      self.actionMenu.addItem_(item)

  def displayStroke_(self, keys):
    if not self.keymap:
      return
    for key_view in self.keymap.values():
      key_view.highlighted = False
    for key in keys:
      for machine_key in self.machine_keymap[key]:
        if machine_key in self.keymap:
          self.keymap[machine_key].highlighted = True
    for key_view in self.keymap.values():
      key_view.setNeedsDisplay_(True)

  def keyView_didReceiveClick_(self, view, event):
    for item in self.actionMenu.itemArray():
      item.setState_(NSOffState)
    if view is None:
      self.selection = None
      return

    key = self.reverse_keymap[view]
    if not key:
      return
    key = key[0]
    action = self.machine_keymap.get_action(key) or "no-op"
    self.selection = key

    self.actionMenu.itemWithTitle_(action).setState_(NSOnState)
    NSMenu.popUpContextMenu_withEvent_forView_(self.actionMenu, event, view)

  def selectMappingForKey_(self, sender):
    key, action = self.selection, sender.representedObject()
    if not self.delegate:
      return
    self.delegate.didSelectAction_forKey_(action, key)

    do_async(self.configDidChange_, self.engine.config)

class StenotypeDisplayController(DisplayController):
  nibName = "StenotypeLayoutDisplay"

  leftS = IBOutlet()
  leftT = IBOutlet()
  leftK = IBOutlet()
  leftP = IBOutlet()
  leftW = IBOutlet()
  leftH = IBOutlet()
  leftR = IBOutlet()
  rightF = IBOutlet()
  rightR = IBOutlet()
  asterisk = IBOutlet()
  rightP = IBOutlet()
  rightB = IBOutlet()
  rightL = IBOutlet()
  rightG = IBOutlet()
  rightT = IBOutlet()
  rightS = IBOutlet()
  rightD = IBOutlet()
  rightZ = IBOutlet()
  numberBar = IBOutlet()
  A = IBOutlet()
  O = IBOutlet()
  E = IBOutlet()
  U = IBOutlet()

  def configureKeymap(self):
    for key in [
        self.leftS, self.leftK, self.leftW, self.leftR,
        self.A, self.O, self.asterisk, self.E, self.U,
        self.rightR, self.rightB, self.rightG, self.rightS, self.rightZ,
      ]:
      key.rounded = True
    self.asterisk.roundSide = "left"
    self.rightD.roundSide = "right"
    self.rightZ.roundSide = "right"

    self.keymap = {
      "#": self.numberBar,
      "S-": self.leftS,
      "T-": self.leftT,
      "K-": self.leftK,
      "P-": self.leftP,
      "W-": self.leftW,
      "H-": self.leftH,
      "R-": self.leftR,
      "A-": self.A,
      "O-": self.O,
      "*": self.asterisk,
      "-E": self.E,
      "-U": self.U,
      "-F": self.rightF,
      "-R": self.rightR,
      "-P": self.rightP,
      "-B": self.rightB,
      "-L": self.rightL,
      "-G": self.rightG,
      "-T": self.rightT,
      "-S": self.rightS,
      "-D": self.rightD,
      "-Z": self.rightZ,
    }

class StenographDisplayController(StenotypeDisplayController):
  nibName = "StenographLayoutDisplay"

  stenomark = IBOutlet()

  def configureKeymap(self):
    super().configureKeymap()
    self.keymap["^"] = self.stenomark

class GeminiDisplayController(DisplayController):
  res1 = IBOutlet()
  res2 = IBOutlet()
  Fn = IBOutlet()
  pwr = IBOutlet()
  leftS1 = IBOutlet()
  leftS2 = IBOutlet()
  leftT = IBOutlet()
  leftK = IBOutlet()
  leftP = IBOutlet()
  leftW = IBOutlet()
  leftH = IBOutlet()
  leftR = IBOutlet()
  star1 = IBOutlet()
  star2 = IBOutlet()
  star3 = IBOutlet()
  star4 = IBOutlet()
  rightF = IBOutlet()
  rightR = IBOutlet()
  rightP = IBOutlet()
  rightB = IBOutlet()
  rightL = IBOutlet()
  rightG = IBOutlet()
  rightT = IBOutlet()
  rightS = IBOutlet()
  rightD = IBOutlet()
  rightZ = IBOutlet()
  A = IBOutlet()
  O = IBOutlet()
  E = IBOutlet()
  U = IBOutlet()
  number1 = IBOutlet()
  number2 = IBOutlet()
  number3 = IBOutlet()
  number4 = IBOutlet()
  number5 = IBOutlet()
  number6 = IBOutlet()
  number7 = IBOutlet()
  number8 = IBOutlet()
  number9 = IBOutlet()
  numberA = IBOutlet()
  numberB = IBOutlet()
  numberC = IBOutlet()

  def configureKeymap(self):
    self.keymap = {
      "res1": self.res1,
      "res2": self.res2,
      "S1-": self.leftS1,
      "S2-": self.leftS2,
      "T-": self.leftT,
      "K-": self.leftK,
      "P-": self.leftP,
      "W-": self.leftW,
      "H-": self.leftH,
      "R-": self.leftR,
      "A-": self.A,
      "O-": self.O,
      "*1": self.star1,
      "*2": self.star2,
      "*3": self.star3,
      "*4": self.star4,
      "-E": self.E,
      "-U": self.U,
      "-F": self.rightF,
      "-R": self.rightR,
      "-P": self.rightP,
      "-B": self.rightB,
      "-L": self.rightL,
      "-G": self.rightG,
      "-T": self.rightT,
      "-S": self.rightS,
      "-D": self.rightD,
      "-Z": self.rightZ,
      "#1": self.number1,
      "#2": self.number2,
      "#3": self.number3,
      "#4": self.number4,
      "#5": self.number5,
      "#6": self.number6,
      "#7": self.number7,
      "#8": self.number8,
      "#9": self.number9,
      "#A": self.numberA,
      "#B": self.numberB,
      "#C": self.numberC,
    }

class SplitoDisplayController(GeminiDisplayController):
  nibName = "SplitoLayoutDisplay"

  def configureKeymap(self):
    super().configureKeymap()
    for key in [
        self.res2, self.leftS2, self.leftK, self.leftW, self.leftR,
        self.A, self.O, self.star2, self.star4, self.E, self.U,
        self.rightR, self.rightB, self.rightG, self.rightS, self.rightZ,
      ]:
      key.rounded = True

class PreonicDisplayController(GeminiDisplayController):
  nibName = "PreonicLayoutDisplay"

  def configureKeymap(self):
    super().configureKeymap()
    self.keymap["Fn"] = self.Fn
    self.keymap["pwr"] = self.pwr

class UniDisplayController(GeminiDisplayController):
  nibName = "UniLayoutDisplay"

  def configureKeymap(self):
    super().configureKeymap()
    for key in ["res1", "res2", "#3", "#4", "#5", "#6", "#7", "#8", "#9", "#A", "#B", "#C"]:
      del self.keymap[key]

class ZenDisplayController(GeminiDisplayController):
  nibName = "ZenLayoutDisplay"

  def configureKeymap(self):
    super().configureKeymap()
    self.keymap["Fn"] = self.Fn
    self.keymap["pwr"] = self.pwr

    self.O.setFrameCenterRotation_(-10)
    self.Fn.setFrameCenterRotation_(-20)
    self.pwr.setFrameCenterRotation_(20)
    self.E.setFrameCenterRotation_(10)

class QwertyDisplayController(DisplayController):
  nibName = "QwertyLayoutDisplay"

  one = IBOutlet()
  two = IBOutlet()
  three = IBOutlet()
  four = IBOutlet()
  five = IBOutlet()
  six = IBOutlet()
  seven = IBOutlet()
  eight = IBOutlet()
  nine = IBOutlet()
  zero = IBOutlet()
  minus = IBOutlet()
  equals = IBOutlet()
  q = IBOutlet()
  w = IBOutlet()
  e = IBOutlet()
  r = IBOutlet()
  t = IBOutlet()
  y = IBOutlet()
  u = IBOutlet()
  i = IBOutlet()
  o = IBOutlet()
  p = IBOutlet()
  a = IBOutlet()
  s = IBOutlet()
  d = IBOutlet()
  f = IBOutlet()
  g = IBOutlet()
  h = IBOutlet()
  j = IBOutlet()
  k = IBOutlet()
  l = IBOutlet()
  z = IBOutlet()
  x = IBOutlet()
  c = IBOutlet()
  v = IBOutlet()
  b = IBOutlet()
  n = IBOutlet()
  m = IBOutlet()
  bracketleft = IBOutlet()
  bracketright = IBOutlet()
  semicolon = IBOutlet()
  apostrophe = IBOutlet()
  backslash = IBOutlet()
  comma = IBOutlet()
  period = IBOutlet()
  slash = IBOutlet()
  space = IBOutlet()

  def configureKeymap(self):
    self.keymap = dict(**{
      "1": self.one,
      "2": self.two,
      "3": self.three,
      "4": self.four,
      "5": self.five,
      "6": self.six,
      "7": self.seven,
      "8": self.eight,
      "9": self.nine,
      "0": self.zero,
      "-": self.minus,
      "=": self.equals,
      "[": self.bracketleft,
      "]": self.bracketright,
      ";": self.semicolon,
      "'": self.apostrophe,
      "\\": self.backslash,
      ",": self.comma,
      ".": self.period,
      "/": self.slash,
      "space": self.space,
    }, **{letter: getattr(self, letter) for letter in "abcdefghijklmnopqrstuvwxyz"})
