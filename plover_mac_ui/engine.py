from threading import Thread, current_thread

from plover.engine import StenoEngine

class Engine(StenoEngine, Thread):
  def __init__(self, config, controller, keyboard_emulation):
    StenoEngine.__init__(self, config, controller, keyboard_emulation)
    Thread.__init__(self)
    self.name += "-engine"

  def _in_engine_thread(self):
    return current_thread() == self

  @property
  def improved_keyboard_emulation(self):
    return self._keyboard_emulation.improved

  def toggle_keyboard_emulation(self):
    new = not self._keyboard_emulation.improved
    self._keyboard_emulation.improved = new
    self._trigger_hook("emulation_changed", new)

  def start(self):
    Thread.start(self)
    StenoEngine.start(self)

  def join(self):
    Thread.join(self)
    return self.code
