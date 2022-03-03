from serial import Serial
from serial.tools.list_ports import comports

from AppKit import NSOffState, NSOnState
from objc import IBAction, IBOutlet, ivar

from plover import system
from plover.machine.base import SerialStenotypeBase
from plover.machine.keyboard import Keyboard
from plover.machine.keymap import Keymap
from plover.registry import registry
from plover_cocoa.async_utils import do_async
from plover_cocoa.layout_model import display_controller_for
from plover_cocoa.systems import (
  MACHINE_NAMES, SYSTEM_NAMES,
  pretty_machine_name, pretty_system_name,
)
from plover_cocoa.tool import Tool

class PreferencesController(Tool):
  actionText = "Preferences..."
  nibName = "Preferences"

  tabView = IBOutlet()
  machineList1 = IBOutlet()
  machineList2 = IBOutlet()
  systemList = IBOutlet()
  display = IBOutlet()

  enableOutputAtStartup = IBOutlet()
  startAttached = IBOutlet()
  startCapitalized = IBOutlet()
  addSpacesMode = IBOutlet()
  logStrokes = IBOutlet()
  logTranslations = IBOutlet()

  arpeggiate = IBOutlet()
  port = IBOutlet()
  baudRate = IBOutlet()
  byteSize = IBOutlet()
  parity = IBOutlet()
  stopBits = IBOutlet()
  readTimeout = IBOutlet()
  readTimeoutValue = IBOutlet()
  XonXoff = IBOutlet()
  RtsCts = IBOutlet()

  displayController = ivar()

  serial_options = ivar()
  keyboard_options = ivar()

  _parities = ivar()

  def awakeFromNib(self):
    self.populateSystems_initialValue_(self.systemList, system.NAME)
    self.populateMachines_initialValue_(
      self.machineList1, self.engine.config["machine_type"])
    self.populateMachines_initialValue_(
      self.machineList2, self.engine.config["machine_type"])
    self.tabView.setDelegate_(self)

    self.keyboard_options = [self.arpeggiate]
    self.serial_options = [
      self.port, self.baudRate, self.byteSize, self.parity, self.stopBits,
      self.readTimeout, self.readTimeoutValue, self.XonXoff, self.RtsCts,
    ]

    for baud_rate in Serial.BAUDRATES:
      self.baudRate.addItemWithTitle_(f"{baud_rate} Bd")
      self.baudRate.lastItem().setTag_(baud_rate)

    self._parities = [title[0] for title in self.parity.itemTitles()]

    self.machineDidChange_system_tab_(
      self.current_machine, self.current_system, self.current_tab)

  def populateSystems_initialValue_(self, lst, init):
    lst.removeAllItems()
    for name in SYSTEM_NAMES:
      plugin = registry.get_plugin("system", name)
      lst.addItemWithTitle_(pretty_system_name(name))
      lst.lastItem().setRepresentedObject_(plugin)
    lst.selectItemWithTitle_(pretty_system_name(init))

  def populateMachines_initialValue_(self, lst, init):
    lst.removeAllItems()
    for name in MACHINE_NAMES:
      plugin = registry.get_plugin("machine", name)
      lst.addItemWithTitle_(pretty_machine_name(name))
      lst.lastItem().setRepresentedObject_(plugin)
    lst.selectItemWithTitle_(pretty_machine_name(init))

  @property
  def current_tab(self):
    return self.tabView.selectedTabViewItem().label()

  @property
  def current_system(self):
    return self.systemList.selectedItem().representedObject()

  @property
  def current_machine(self):
    return self.machineList1.selectedItem().representedObject()

  @property
  def displayView(self):
    return self.displayController.view() if self.displayController else None

  @property
  def is_keyboard(self):
    return self.current_machine.obj is Keyboard

  @property
  def is_serial(self):
    return issubclass(self.current_machine.obj, SerialStenotypeBase)

  def tabView_didSelectTabViewItem_(self, view, item):
    self.machineDidChange_system_tab_(
      self.current_machine, self.current_system, self.current_tab)

  def configDidChange_(self, config):
    if not self.tabView:  # nib not initialized
      return
    self.machineList1.selectItemWithTitle_(
      pretty_machine_name(self.engine.config["machine_type"]))
    self.machineList2.selectItemWithTitle_(
      pretty_machine_name(self.engine.config["machine_type"]))
    self.systemList.selectItemWithTitle_(
      pretty_system_name(self.engine.config["system_name"]))
    self.machineDidChange_system_tab_(
      self.current_machine, self.current_system, self.current_tab)

  @IBAction
  def changeMachine_(self, sender):
    with self.engine:
      self.engine._update({"machine_type": sender.selectedItem().representedObject().name})

  @IBAction
  def changeSystem_(self, sender):
    with self.engine:
      self.engine._update({"system_name": sender.selectedItem().representedObject().name})

  @IBAction
  def resetToDefaults_(self, sender):
    if self.current_tab == "Machine":
      with self.engine:
        self.engine._update({
          "machine_specific_options":
            self.engine._config._OPTIONS["machine_specific_options"].default(
              None, [None, self.current_machine.name])})
    elif self.current_tab == "Keymap":
      default_keymap = self.engine._config._OPTIONS["system_keymap"].default(
        None, [None, self.current_system.name, self.current_machine.name])
      keymap = Keymap(default_keymap.get_keys(), default_keymap.get_actions())
      keymap.set_mappings(default_keymap)
      with self.engine:
        self.engine._update({"system_keymap": keymap})

  @property
  def machine_config(self):
    return self.engine.config["machine_specific_options"]

  def setConfig_toValue_(self, prop, value):
    with self.engine:
      self.engine._update({prop: value})

  def setMachineConfig_toValue_(self, prop, value):
    with self.engine:
      self.engine._update({"machine_specific_options": {prop: value}})

  def scanSerialPorts(self):
    self.port.removeAllItems()
    self.port.addItemWithTitle_("")
    for port in comports():
      title = port.device if not port.description or port.description == "n/a" \
        else f"{port.description} ({port.device})"
      self.port.addItemWithTitle_(title)
      self.port.lastItem().setRepresentedObject_(port)

    if "port" in self.machine_config:
      self.port.selectItemWithTitle_(self.machine_config["port"])

  def machineDidChange_system_tab_(self, mach, sys, tab):
    self.scanSerialPorts()

    self.enableOutputAtStartup.setState_(
      NSOnState if self.engine.config.get("auto_start") else NSOffState)
    self.startAttached.setState_(
      NSOnState if self.engine.config.get("start_attached") else NSOffState)
    self.startCapitalized.setState_(
      NSOnState if self.engine.config.get("start_capitalized") else NSOffState)
    self.logStrokes.setState_(
      NSOnState if self.engine.config.get("enable_stroke_logging") else NSOffState)
    self.logTranslations.setState_(
      NSOnState if self.engine.config.get("enable_translation_logging") else NSOffState)
    self.addSpacesMode.selectItemWithTitle_(self.engine.config.get("space_placement"))

    for opt in self.keyboard_options:
      opt.setEnabled_(self.is_keyboard)
    for opt in self.serial_options:
      opt.setEnabled_(self.is_serial)

    if self.is_keyboard:
      self.arpeggiate.setState_(NSOnState if self.machine_config["arpeggiate"] else NSOffState)
    elif self.is_serial:
      if "port" in self.machine_config:
        self.port.selectItemWithTitle_(self.machine_config["port"])
      else:
        self.port.selectItemAtIndex_(0)
      self.baudRate.selectItemWithTag_(self.machine_config.get("baudrate", 9600))
      self.byteSize.selectItemWithTag_(self.machine_config.get("bytesize", 8))
      self.parity.selectItemAtIndex_(self._parities.index(self.machine_config.get("parity", "N")))
      self.stopBits.selectItemWithTag_(self.machine_config.get("stopbits", 2) * 2)

      has_timeout = self.machine_config.get("timeout") is not None
      self.readTimeout.setState_(NSOnState if has_timeout else NSOffState)
      self.readTimeoutValue.setEnabled_(has_timeout)
      if has_timeout:
        self.readTimeoutValue.setStringValue_(self.machine_config["timeout"])

      self.XonXoff.setState_(NSOnState if self.machine_config.get("xonxoff") else NSOffState)
      self.RtsCts.setState_(NSOnState if self.machine_config.get("rtscts") else NSOffState)

    try:
      self.displayController = (
        display_controller_for(self.engine.config["machine_type"])
          .alloc().initWithEngine_(self.engine))
    except KeyError:
      return
    self.registerClickHandlers_(self.displayController)
    self.displayController.setDelegate_(self)

    for view in self.display.subviews():
      if view is not self.displayView:
        view.removeFromSuperview()

    def _changeDisplayController():
      self.display.addSubview_(self.displayView),
      self.displayView.setNeedsDisplay_(True),
      self.display.layout(),
    do_async(_changeDisplayController)

  def registerClickHandlers_(self, controller):
    controller.view().setClickHandler_(
        lambda event: controller.keyView_didReceiveClick_(None, None))
    for key_view in controller.view().subviews():
      key_view.darkOutlineWhenDisabled = True
      key_view.showFullLabel = True
      key_view.setClickHandler_((lambda v: (
        lambda event: controller.keyView_didReceiveClick_(v, event)))(key_view))

  @IBAction
  def toggleEnableOutputAtStartup_(self, sender):
    self.setConfig_toValue_("auto_start", sender.state() == NSOnState)

  @IBAction
  def toggleStartAttached_(self, sender):
    self.setConfig_toValue_("start_attached", sender.state() == NSOnState)

  @IBAction
  def toggleStartCapitalized_(self, sender):
    self.setConfig_toValue_("start_capitalized", sender.state() == NSOnState)

  @IBAction
  def changeAddSpacesMode_(self, sender):
    self.setConfig_toValue_("space_placement", sender.titleOfSelectedItem())

  @IBAction
  def toggleLogStrokes_(self, sender):
    self.setConfig_toValue_("enable_stroke_logging", sender.state() == NSOnState)

  @IBAction
  def toggleLogTranslations_(self, sender):
    self.setConfig_toValue_("enable_translation_logging", sender.state() == NSOnState)

  @IBAction
  def toggleArpeggiate_(self, sender):
    if self.is_keyboard:
      self.setMachineConfig_toValue_("arpeggiate", sender.state() == NSOnState)

  @IBAction
  def changeSerialPort_(self, sender):
    if self.is_serial:
      self.setMachineConfig_toValue_("port",
        sender.selectedItem().representedObject().device or None)

  @IBAction
  def changeBaudRate_(self, sender):
    if self.is_serial:
      self.setMachineConfig_toValue_("baudrate", sender.selectedTag())

  @IBAction
  def changeByteSize_(self, sender):
    if self.is_serial:
      self.setMachineConfig_toValue_("bytesize", sender.selectedTag())

  @IBAction
  def changeParity_(self, sender):
    if self.is_serial:
      self.setMachineConfig_toValue_("parity", sender.titleOfSelectedItem()[0])

  @IBAction
  def changeStopBits_(self, sender):
    if self.is_serial:
      self.setMachineConfig_toValue_("stopbits", sender.selectedTag() / 2)

  @IBAction
  def toggleReadTimeout_(self, sender):
    if self.is_serial:
      self.readTimeoutValue.setEnabled_(sender.state() == NSOnState)
      self.setMachineConfig_toValue_(
        "timeout", float(self.readTimeoutValue.stringValue() or "0"))

  @IBAction
  def changeReadTimeout_(self, sender):
    if self.is_serial:
      self.setMachineConfig_toValue_("timeout", float(sender.stringValue()))

  @IBAction
  def toggleXonXoff_(self, sender):
    if self.is_serial:
      self.setMachineConfig_toValue_("xonxoff", sender.state() == NSOnState)

  @IBAction
  def toggleRtsCts_(self, sender):
    if self.is_serial:
      self.setMachineConfig_toValue_("rtscts", sender.state() == NSOnState)

  def didSelectAction_forKey_(self, action, key):
    old_keymap = self.engine.config["system_keymap"]
    keymap = Keymap(old_keymap.get_keys(), old_keymap.get_actions())
    bindings = old_keymap.get_bindings()
    bindings[key] = action
    keymap.set_bindings(bindings)
    with self.engine:
      self.engine._update({"system_keymap": keymap})
