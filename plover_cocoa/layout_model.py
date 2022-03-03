from enum import Enum

from plover_cocoa.layout_display_views import (
  PreonicDisplayView,
  QwertyDisplayView,
  SplitoDisplayView,
  StenographDisplayView,
  StenotypeDisplayView,
  StenoKeyView,
  UniDisplayView,
  ZenDisplayView,
)
from plover_cocoa.layout_display_controllers import (
  PreonicDisplayController,
  QwertyDisplayController,
  SplitoDisplayController,
  StenographDisplayController,
  StenotypeDisplayController,
  UniDisplayController,
  ZenDisplayController,
)

class Machine(Enum):
  QWERTY = 0
  STENOTYPE = 1
  STENOGRAPH = 2
  SPLITOGRAPHY = 3
  ZEN = 4
  UNI = 5
  PREONIC = 6

STROKE_TIMEOUT = 0.75

MACHINE_TYPES = {
  "Stentura": Machine.STENOGRAPH,
  "Stenograph USB": Machine.STENOGRAPH,
  "Stenograph Wi-Fi": Machine.STENOGRAPH,
  "TX Bolt": Machine.STENOTYPE,
  "Gemini PR": Machine.PREONIC,
  "Keyboard": Machine.QWERTY,
}

CONTROLLERS = {
  Machine.STENOTYPE: StenotypeDisplayController,
  Machine.STENOGRAPH: StenographDisplayController,
  Machine.SPLITOGRAPHY: SplitoDisplayController,
  Machine.ZEN: ZenDisplayController,
  Machine.UNI: UniDisplayController,
  Machine.PREONIC: PreonicDisplayController,
  Machine.QWERTY: QwertyDisplayController,
}

def machine_type_for(machine):
  return MACHINE_TYPES[machine]

def display_controller_for(machine):
  return CONTROLLERS[machine_type_for(machine)]
