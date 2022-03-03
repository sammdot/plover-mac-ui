from functools import wraps
from threading import Timer

def debounce(delay):
  def _debounce(func):
    t = None
    @wraps(func)
    def debounced(*args, **kwargs):
      nonlocal t
      if t:
        t.cancel()
        t = None
      t = Timer(delay, lambda: func(*args, **kwargs))
      t.start()
    return debounced
  return _debounce

def every(n, lst):
  for i in range(0, len(lst), n):
    yield lst[i : i + n]
