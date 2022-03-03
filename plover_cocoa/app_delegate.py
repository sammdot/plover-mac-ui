from AppKit import (
  NSAboutPanelOptionApplicationIcon,
  NSAboutPanelOptionApplicationName,
  NSAboutPanelOptionApplicationVersion,
  NSAboutPanelOptionCredits,
  NSAboutPanelOptionVersion,
  NSApplication,
  NSAttributedString,
  NSFontAttributeName,
  NSImageLeading,
  NSMenu,
  NSMenuItem,
  NSOffState,
  NSOnState,
  NSSquareStatusItemLength,
  NSStatusBar,
  NSVariableStatusItemLength,
)
from Foundation import NSObject
from objc import ivar, protocolNamed, super
import os

import plover
from plover import system
from plover.config import DictionaryConfig
from plover.registry import Plugin, registry
from plover_cocoa.fonts import DEFAULT_FONT
from plover_cocoa.lookup_model import Dictionary
from plover_cocoa.preferences import PreferencesController
from plover_cocoa.resources import icon_named, nib_named, plover_logo
from plover_cocoa.systems import (
  MACHINE_NAMES, machine_plugin, pretty_machine_name, machine_icon,
  SYSTEM_NAMES, system_plugin, pretty_system_name, system_abbr, system_icon,
)

SOFTWARE_NAME = plover.__name__.capitalize()


def make_item(title="", action="", key="", icon=None, obj=None, enabled=True, selected=None, indent=0):
  item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, key)
  if obj:
    item.setRepresentedObject_(obj)
  if not enabled:
    item.setEnabled_(False)
  if icon:
    item.setImage_(icon)
  if indent:
    item.setIndentationLevel_(indent)
  if selected is not None:
    item.setState_(NSOnState if selected else NSOffState)
  return item


NSApplicationDelegate = protocolNamed("NSApplicationDelegate")

class AppDelegate(NSObject, protocols=[NSApplicationDelegate]):
  tools = ivar()
  prefs = ivar()

  def initWithEngine_(self, engine):
    self = super(AppDelegate, self).init()
    if self is None: return None

    self.engine = engine
    engine.cocoa_app = self
    engine.hook_connect("quit", self.quit)

    self.tools = {
      plugin.name: plugin.obj.alloc().initWithEngine_(engine)
      for plugin in registry.list_plugins("gui.cocoa.tool")
      if plugin.obj.enabled
    }
    self.prefs = PreferencesController.alloc().initWithEngine_(engine)
    return self

  def applicationDidFinishLaunching_(self, _):
    main_menu_nib = nib_named("MainMenu")
    ok, objects = main_menu_nib.instantiateWithOwner_topLevelObjects_(None, None)
    assert ok
    main_menu = [obj for obj in objects if isinstance(obj, NSMenu)][0]
    NSApplication.sharedApplication().setMainMenu_(main_menu)

    status_bar = NSStatusBar.systemStatusBar()
    self.statusItem = status_item = status_bar.statusItemWithLength_(NSVariableStatusItemLength)  # NSSquareStatusItemLength
    status_item.button().setImage_(icon_named("state-enabled"))
    status_item.button().setImagePosition_(NSImageLeading)
    status_item.setToolTip_(SOFTWARE_NAME)

    self.menu = menu = NSMenu.alloc().init()
    menu.setAutoenablesItems_(False)

    def make_empty_item():
      return make_item(enabled=False)

    machine_name = (lambda x: x) \
      if "PLOVER_FULL_NAMES" in os.environ else pretty_machine_name
    system_name = (lambda x: x) \
      if "PLOVER_FULL_NAMES" in os.environ else pretty_system_name

    def make_machine_item(mach):
      if "PLOVER_ALL_PLUGINS" in os.environ:
        return make_item(machine_name(mach.name), "changeMachine:",
          # icon=icon_named(f"{machine_name(mach.name)-enabled"),
          obj=mach, indent=1)
      else:
        plugin = registry.get_plugin("machine", mach)
        return make_item(machine_name(mach), "changeMachine:",
          # icon=icon_named(f"{machine_icon(mach)}-enabled"),
          obj=plugin, indent=1, enabled=plugin is not None)

    def make_system_item(sys):
      if "PLOVER_ALL_PLUGINS" in os.environ:
        return make_item(system_name(sys.name), "changeSystem:",
          # icon=icon_named(system_icon(sys.name), template=False),
          obj=sys, indent=1)
      else:
        plugin = registry.get_plugin("system", sys)
        return make_item(system_name(sys), "changeSystem:",
          # icon=icon_named(system_icon(sys), template=False),
          obj=plugin, indent=1, enabled=plugin is not None)

    def make_tool_item(tool):
      return make_item(
        tool.obj.actionText or None, "openTool:", tool.obj.shortcut or None,
        obj=self.tools.get(tool.name),
        enabled=tool.obj.enabled)

    self.outputMenuItem = make_empty_item()
    self.emulationMenuItem = make_empty_item()
    self.machineStateMenuItem = make_empty_item()
    self.systemNameMenuItem = make_empty_item()

    self.toggleOutputMenuItem = make_item("Toggle Output", "toggleOutput", "o")
    self.toggleEmulationMenuItem = make_item("Toggle Emulation", "toggleKeyboardEmulation", "e")

    self.manageDictMenuItem = make_item("Dictionaries")
    self.dictMenu = NSMenu.alloc().init()
    self.manageDictMenuItem.setSubmenu_(self.dictMenu)

    menu_items = [
      self.outputMenuItem,
      self.toggleOutputMenuItem,

      NSMenuItem.separatorItem(),
      self.emulationMenuItem,
      self.toggleEmulationMenuItem,

      NSMenuItem.separatorItem(),
      self.machineStateMenuItem,
      make_item("Reconnect Machine", "reconnectMachine", "r"),
      *map(make_machine_item,
        registry.list_plugins("machine")
        if "PLOVER_ALL_PLUGINS" in os.environ else MACHINE_NAMES),

      NSMenuItem.separatorItem(),
      self.systemNameMenuItem,
      *map(make_system_item,
        registry.list_plugins("system")
        if "PLOVER_ALL_PLUGINS" in os.environ else SYSTEM_NAMES),

      NSMenuItem.separatorItem(),
      self.manageDictMenuItem,

      NSMenuItem.separatorItem(),
      *map(make_tool_item, registry.list_plugins("gui.cocoa.tool")),

      NSMenuItem.separatorItem(),
      make_item(self.prefs.actionText, "openPreferences", ","),

      NSMenuItem.separatorItem(),
      make_item(f"About {SOFTWARE_NAME}", "openAboutWindow"),
      make_item(f"Quit {SOFTWARE_NAME}", "quit", "q"),
    ]
    for item in menu_items:
      menu.addItem_(item)

    status_item.setMenu_(menu)

    self.engine.hook_connect("output_changed", self.outputDidChange_)
    self.engine.hook_connect("emulation_changed", self.emulationDidChange_)
    self.engine.hook_connect("machine_state_changed", self.machine_stateDidChange_)
    self.engine.hook_connect("config_changed", self.configDidChange_)
    self.engine.hook_connect("configure", self.openPreferences)

    self.outputDidChange_(self.engine.output)
    self.machine_stateDidChange_(self.engine.config["machine_type"], self.engine.machine_state)
    self.configDidChange_(self.engine.config)
    self.emulationDidChange_(self.engine.improved_keyboard_emulation)

  def toggleOutput(self):
    with self.engine:
      self.engine.toggle_output()

  def toggleKeyboardEmulation(self):
    with self.engine:
      self.engine.toggle_keyboard_emulation()

  def reconnectMachine(self):
    with self.engine:
      self.engine.reset_machine()

  def changeSystem_(self, selection):
    with self.engine:
      self.engine._update({"system_name": selection.representedObject().name})

  def changeMachine_(self, selection):
    with self.engine:
      self.engine._update({"machine_type": selection.representedObject().name})

  def openTool_(self, sender):
    if sender.representedObject():
      sender.representedObject().asyncShowWindow()

  def openPreferences(self):
    self.prefs.asyncShowWindow()

  def openAboutWindow(self):
    about_text = (
      plover.__long_description__.replace("\n", " "))
    NSApplication.sharedApplication().orderFrontStandardAboutPanelWithOptions_({
      NSAboutPanelOptionApplicationIcon: plover_logo,
      NSAboutPanelOptionApplicationName: SOFTWARE_NAME,
      NSAboutPanelOptionApplicationVersion: plover.__version__,
      NSAboutPanelOptionCredits: (
        NSAttributedString.alloc().initWithString_attributes_(
          about_text, { NSFontAttributeName: DEFAULT_FONT })),
      NSAboutPanelOptionVersion: "",
      "Copyright": plover.__copyright__.replace("(C)", "\xa9"),
    })

  def iconName(self):
    machine_type = machine_icon(self.engine.config["machine_type"]) \
      if "PLOVER_MACHINE_ICON" in os.environ else "state"
    state = "disconnected" if self.engine._machine_state != "connected" else \
      "enabled" if self.engine.output else "disabled"
    return f"{machine_type}-{state}"

  def statusLabel(self):
    label_type = os.environ.get("PLOVER_STATUS_LABEL")
    if label_type == "short":
      return system_abbr(system.NAME)
    elif label_type == "long":
      return pretty_system_name(system.NAME)
    return None

  def outputDidChange_(self, enabled):
    self.outputMenuItem.setTitle_(f"Output: {'On' if enabled else 'Off'}")
    self.statusItem.button().setImage_(icon_named(self.iconName()))
    self.toggleOutputMenuItem.setTitle_(f"{'Disable' if enabled else 'Enable'} Output")

  def clearSelections_(self, plugin_type):
    for item in self.menu.itemArray():
      if (isinstance(item.representedObject(), Plugin) and
          item.representedObject().plugin_type == plugin_type):
        item.setState_(NSOffState)

  def machine_stateDidChange_(self, machine_type, state):
    self.clearSelections_("machine")
    self.menu.itemAtIndex_(
      self.menu.indexOfItemWithRepresentedObject_(
        registry.get_plugin("machine", machine_type))).setState_(NSOnState)
    self.machineStateMenuItem.setTitle_(
      f"{pretty_machine_name(machine_type)}: {state.capitalize()}")
    self.statusItem.button().setImage_(icon_named(self.iconName()))

  def configDidChange_(self, config):
    self.clearSelections_("system")
    self.menu.itemAtIndex_(
      self.menu.indexOfItemWithRepresentedObject_(
        registry.get_plugin("system", system.NAME))).setState_(NSOnState)
    self.systemNameMenuItem.setTitle_(
      f"System: {pretty_system_name(system.NAME)}")
    
    label = self.statusLabel()
    if label:
      self.statusItem.button().setTitle_(f" {label}")

    if "dictionaries" in config:
      self.dictMenu.removeAllItems()
      for d in config["dictionaries"]:
        item = make_item(
          Dictionary.short_dict_name(d), "toggleDictionary:",
          obj=d, selected=d.enabled)
        self.dictMenu.addItem_(item)

  def toggleDictionary_(self, selection):
    obj = selection.representedObject()
    dict_index = self.dictMenu.indexOfItemWithRepresentedObject_(obj)
    config = self.engine.config["dictionaries"]
    enabled = not config[dict_index].enabled
    config[dict_index] = DictionaryConfig(obj.path, enabled=enabled)
    with self.engine:
      self.engine._update({"dictionaries": config})
    self.dictMenu.itemAtIndex_(dict_index).setState_(NSOnState if enabled else NSOffState)

  def emulationDidChange_(self, emulation):
    self.emulationMenuItem.setTitle_(
      f"Emulation: {'Improved' if self.engine.improved_keyboard_emulation else 'Stock'}")

  def openPaperTape(self):
    self.tools["tool2_paper_tape"].asyncShowWindow()

  def openLayoutDisplay(self):
    self.tools["tool3_layout_display"].asyncShowWindow()

  def quit(self):
    NSApplication.sharedApplication().terminate_(self)
