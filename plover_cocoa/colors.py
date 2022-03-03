from AppKit import NSColor

def rgb(r, g, b):
  return NSColor.colorWithRed_green_blue_alpha_(r / 255, g / 255, b / 255, 1.0)

def hex_color(hex):
  return rgb(int(hex[:2], base=16), int(hex[2:4], base=16), int(hex[4:], base=16))

# Colors based on Typey Type's steno diagram style.
# DARK = hex_color("7109aa")
# SEMI_DARK = hex_color("c592e0")
# LIGHT = hex_color("e9d9f2")

# Pink theme :3
DARK = hex_color("e46f87")
SEMI_DARK = hex_color("f29bad")
LIGHT = hex_color("fde0f0")
# LIGHT = hex_color("ffffff")
