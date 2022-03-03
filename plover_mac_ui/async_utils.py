from libdispatch import dispatch_async, dispatch_get_main_queue

def do_async(fn, *args):
  dispatch_async(
    dispatch_get_main_queue(),
    lambda: [fn(*args), None][-1],
  )
