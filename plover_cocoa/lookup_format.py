from collections import namedtuple
from enum import Enum
import re

from AppKit import (
  NSBackgroundColorAttributeName,
  NSColor,
  NSFont,
  NSFontAttributeName,
  NSMutableArray,
  NSStrikethroughStyleAttributeName,
  NSUnderlineStyleNone,
  NSUnderlineStyleSingle,
)
from Foundation import NSMutableAttributedString

from plover.key_combo import KEYNAME_TO_CHAR
from plover_cocoa.fonts import LOOKUP_LIST_FONT

Function = type(lambda a: a)

class TokenType(Enum):
  CANCEL = 0
  NOOP = 1
  SPACE = 2
  STRING = 3
  COMMAND = 4
  MODE = 5
  MODE_SPACE = 6
  GLUE = 7
  ATTACH_RAW = 8
  ATTACH_INFIX = 9
  ATTACH_PREFIX = 10
  ATTACH_SUFFIX = 11
  CARRY_CAP = 12
  CURRENCY = 13
  KEY_COMBO = 14
  META = 15
  MACRO = 16

  DISC_EMOJI = 17

PLOVER_COMMAND_FRIENDLY_NAMES = {
  "add_translation": "Add Translation",
  "suspend": "Disable Output",
  "resume": "Enable Output",
  "toggle": "Toggle Output",
  "lookup": "Open Lookup Tool",
  "configure": "Open Preferences",
  "focus": "Show Main Window",
  "quit": "Quit",
}

MODE_FRIENDLY_NAMES = {
  "caps": "ALL CAPS",
  "title": "Title Case",
  "lower": "lower case",
  "camel": "CamelCase",
  "snake": "snake_case",
  "reset_case": "Reset Case",
  "reset_space": "Reset Space",
  "reset": "Reset Case and Space",
  "clear": "Reset Case and Space",

  "fancytext_off": "Reset Fancy Text",
  "kebab": "kebab-case",
  "fullwidth": "ｆｕｌｌ　ｗｉｄｔｈ",
  "sarcasm": "sArCaSm",
  "zalgo": "z̶͉a̕l̬ḡ͙o̕",
}

OPERATOR_METAS = {
  "-|": ("case", "cap_first_word"),
  "<": ("case", "upper_first_word"),
  ">": ("case", "lower_first_char"),
  ".": ("stop", "."),
  "!": ("stop", "!"),
  "?": ("stop", "?"),
  ",": ("comma", ","),
  ":": ("comma", ":"),
  ";": ("comma", ";"),
}

OPERATOR_MACROS = {
  "*": ("retrospective_toggle_asterisk",),
  "*+": ("repeat_last_stroke",),
  "*?": ("retrospective_insert_space",),
  "*!": ("retrospective_delete_space",),
}

META_FRIENDLY_NAMES = {
  "carry_capitalize": "Carry Capitalization",

  "case": "{0} Next Word",
  "retro_case": "{0} Last Word",
  "cap_first_word": "Capitalize",
  "upper_first_word": "ALL CAPS",
  "lower_first_char": "lowercase",

  "stop": "{0}",
  "comma": "{0}",
  ".": "Full Stop",
  "!": "Exclamation Mark",
  "?": "Question Mark",
  ",": "Comma",
  ":": "Colon",
  ";": "Semicolon",

  "retro_double_quotes": lambda num: f"Surround Last {num + ' ' if int(num) > 1 else ''}Word{'s' if int(num) > 1 else ''} with Double Quotes",
  "retro_single_quotes": lambda num: f"Surround Last {num + ' ' if int(num) > 1 else ''}Word{'s' if int(num) > 1 else ''} with Single Quotes",
  "retro_surround": lambda num, left, right: f"Surround Last {num + ' ' if int(num) > 1 else ''}Word{'s' if int(num) > 1 else ''} with {left} {right}",
  "fancytext_retro": lambda num, transformer: f"{MODE_FRIENDLY_NAMES.get(transformer, transformer)} Last {num + ' ' if int(num) > 1 else ''}Word{'s' if int(num) > 1 else ''}"
}

MACRO_FRIENDLY_NAMES = {
  "undo": "Undo Last Stroke",
  "repeat_last_stroke": "Repeat Last Stroke",
  "retrospective_toggle_asterisk": "Toggle * on Last Stroke",
  "retrospective_insert_space": "Retroactive Insert Space",
  "retrospective_delete_space": "Retroactive Delete Space",
}

TOKEN_RE = re.compile(r"""
    (?P<escaped>\\\\|\\{|\\})
  | (?:{(?P<space>)\s+})
  | (?P<cancel>{})
  | (?P<noop>{\#})
  | (?:^=(?P<macro_name>\w+)(?::(?P<macro_args>.+))?$)
  | (?:{(?:PLOVER|:command):(?P<command>[^}]+?)})
  | (?:{(?:MODE|:mode):(?:SET_SPACE:(?P<mode_space>(?:\\\\|\\}|[^}])*?)|(?P<mode>[^}]+?))})
  | (?:{(?:&|:glue:)(?P<glue>(?:\\\\|\\}|[^}])+?)})
  | (?:{(?:\^~\||:carry_capitalize:\^)(?P<carry_cap_infix>(?:\\\\|\\}|[^}])+?)\^})
  | (?:{(?:\^~\||:carry_capitalize:\^)(?P<carry_cap_suffix>(?:\\\\|\\}|[^}])+?)})
  | (?:{(?:~\||:carry_capitalize:)(?P<carry_cap_prefix>(?:\\\\|\\}|[^}])+?)\^})
  | (?:{(?:~\||:carry_capitalize:)(?P<carry_cap>(?:\\\\|\\}|[^}])+?)})
  | (?:{(?::attach|\^)(?P<attach_raw>)})
  | (?:{\^(?P<attach_infix>(?:\\\\|\\}|[^}])+?)\^})
  | (?:{:attach:(?P<attach_infix_2>(?:\\\\|\\}|[^}\^])+?)})
  | (?:{(?:(?::attach:)?\^)(?P<attach_suffix>(?:\\\\|\\}|[^}])+?)})
  | (?:{(?:(?::attach:)?)(?P<attach_prefix>(?:\\\\|\\}|[^}])+?)\^})
  | (?:{(?:\*\(|:retro_currency:)(?P<currency_pre>(?:\\\\|\\}|[^}])*?)c(?P<currency_post>(?:\\\\|\\}|[^}])*?)\)?})
  | (?:{(?:\#|:key_combo:)(?P<key_combo>[^}]+?)})
  | (?:{:(?P<meta_name>\w+)(?::(?P<meta_args>[^}]+?))?})
  | (?:{(?P<operator>(?:\^|&)(?:[^}]+?)?|\*|\*?(?:-\||[<>+?!])|~\|(?:[^}]+?)?|(?:[^}]+?)\^|[\.,:;!\?])})
  | (?:<a?:(?P<discord_emoji>\w+):\d+>)
  | (?P<raw>(?:\\\\|\\{|[^\{=])+|{)
  """, re.VERBOSE | re.IGNORECASE)

KEY_COMBO_RE = re.compile(r"""
    (?P<oper_begin>(?:(?:control|shift|alt|super)|option|windows|command))(?:_[LR])?\(
  | (?P<oper_begin_bad>)\(
  | \)(?P<oper_end>)
  | (?P<key>[^\(\)\s]+)
  """, re.VERBOSE | re.IGNORECASE)
CANONICAL_MOD_KEYS = {
  "option": "alt",
  "windows": "super",
  "command": "super",
}
MOD_KEY_ORDER = ["super", "control", "alt", "shift"]
KEY_SYMBOLS = {
  "super": "⌘",
  "control": "⌃",
  "alt": "⌥",
  "shift": "⇧",
  "caps_lock": "⇪",
  "return": "⏎",
  "left": "←",
  "right": "→",
  "up": "↑",
  "down": "↓",
  "tab": "⇥",
  "escape": "⎋",
  "space": "␣",
  "backspace": "⌫",
}

SPECIAL_CASE_MODES = {
  ((TokenType.MODE, "lower"), "-"): "kebab",
  ((TokenType.META, "fancytext_set", "fullwidth"), "\u3000"): "fullwidth",
  ((TokenType.META, "fancytext_set", "sarcasm"),): "sarcasm",
  ((TokenType.META, "fancytext_set", "zalgo"),): "zalgo",
  ((TokenType.META, "fancytext_set", "off"),): "fancytext_off",
}

U = lambda u: f"‹U+{hex(u)[2:].rjust(4, '0')}›"

REPLACEMENTS = {
  "\u3000": U(0x3000),
  "\\r\\n": "⏎",
  "\\r": "⏎",
  "\\n": "⏎",
  "\\t": "\u21e5",
}

def format_unicode(string):
  s = string
  for uni, repl in REPLACEMENTS.items():
    s = s.replace(uni, repl)
  return s

def split_keys(string):
  mod_stack = []
  keys = []

  for match in KEY_COMBO_RE.finditer(string.lower()):
    d = match.groupdict()

    mod = set(mod_stack) - {""}
    if d["oper_begin"]:
      mod_stack.append(CANONICAL_MOD_KEYS.get(d["oper_begin"], d["oper_begin"]))
    elif d["oper_begin_bad"] is not None:
      mod_stack.append("")
    elif d["oper_end"] is not None:
      if not mod_stack:
        continue
      mod_stack.pop()
    elif d["key"]:
      keys.append((*sorted(mod, key=MOD_KEY_ORDER.index), d["key"]))
  return keys

def format_key_seq(seq):
  keys = []
  for key in seq:
    if len(key) == 1:
      keys.append(key.upper())
    elif key in KEY_SYMBOLS:
      keys.append(KEY_SYMBOLS[key])
    elif key in KEYNAME_TO_CHAR:
      keys.append(KEYNAME_TO_CHAR[key])
    else:
      keys.append(f"‹{key}›")
  return "".join(keys)

def format_for_word_list(tl, bad=False):
  return NSMutableAttributedString.alloc().initWithString_attributes_(tl,
    {
      NSFontAttributeName: LOOKUP_LIST_FONT,
      NSStrikethroughStyleAttributeName:
        NSUnderlineStyleSingle if bad else NSUnderlineStyleNone,
    })

def format_for_translation_list(tl):
  lst = []

  for match in TOKEN_RE.finditer(tl):
    d = match.groupdict()

    obj = None
    if d["cancel"]:
      obj = (TokenType.CANCEL,)
    elif d["noop"]:
      obj = (TokenType.NOOP,)
    elif d["command"]:
      obj = (TokenType.COMMAND, d["command"].lower())
    elif d["mode_space"] is not None:
      if lst and (lst[-1], d["mode_space"]) in SPECIAL_CASE_MODES:
        mode = lst.pop()
        obj = (TokenType.MODE, SPECIAL_CASE_MODES[(mode, d["mode_space"])])
      else:
        obj = [
          (TokenType.MODE_SPACE,),
          (TokenType.STRING, format_unicode(d["mode_space"])),
        ]
    elif d["mode"]:
      if lst and (lst[-1],) in SPECIAL_CASE_MODES:
        mode = lst.pop()
        obj = (TokenType.MODE, SPECIAL_CASE_MODES[(mode,)])
      else:
        obj = (TokenType.MODE, d["mode"].lower())
    elif d["glue"]:
      obj = [
        (TokenType.GLUE, d["glue"]),
        (TokenType.STRING, d["glue"]),
      ]
    elif d["attach_raw"] is not None:
      obj = [
        (TokenType.ATTACH_RAW,),
        (TokenType.STRING, d["attach_raw"]),
      ]
    elif d["attach_infix"] is not None or d["attach_infix_2"] is not None:
      obj = [
        (TokenType.ATTACH_INFIX,),
        (TokenType.STRING, d["attach_infix"] or d["attach_infix_2"]),
      ]
    elif d["attach_prefix"]:
      obj = [
        (TokenType.ATTACH_PREFIX,),
        (TokenType.STRING, d["attach_prefix"]),
      ]
    elif d["attach_suffix"]:
      obj = [
        (TokenType.ATTACH_SUFFIX,),
        (TokenType.STRING, d["attach_suffix"]),
      ]
    elif d["carry_cap"]:
      obj = [
        (TokenType.STRING, d["carry_cap"]),
        (TokenType.CARRY_CAP,),
      ]
    elif d["carry_cap_infix"]:
      obj = [
        (TokenType.ATTACH_INFIX,),
        (TokenType.STRING, d["carry_cap_infix"]),
        (TokenType.CARRY_CAP,),
      ]
    elif d["carry_cap_prefix"]:
      obj = [
        (TokenType.ATTACH_PREFIX,),
        (TokenType.STRING, d["carry_cap_prefix"]),
        (TokenType.CARRY_CAP,),
      ]
    elif d["carry_cap_suffix"]:
      obj = [
        (TokenType.ATTACH_SUFFIX,),
        (TokenType.STRING, d["carry_cap_suffix"]),
        (TokenType.CARRY_CAP,),
      ]
    elif d["currency_pre"] or d["currency_post"]:
      obj = (
        ([(TokenType.STRING, d["currency_pre"])] if d["currency_pre"] else []) +
        [(TokenType.CURRENCY,)] +
        ([(TokenType.STRING, d["currency_post"])] if d["currency_post"] else [])
      )
    elif d["macro_name"]:
      macro, args = d["macro_name"], d["macro_args"].split(",") if d["macro_args"] else []
      if args == ["", ""]: args = [","]
      obj = (TokenType.MACRO, macro, *args) if args else (TokenType.MACRO, macro)
    elif d["meta_name"]:
      meta, args = d["meta_name"], d["meta_args"].split(":") if d["meta_args"] else []
      if args == ["", ""]: args = [":"]
      obj = (TokenType.META, meta, *args) if args else (TokenType.META, meta)
    elif d["operator"]:
      oper = d["operator"]
      is_macro = False
      if oper in OPERATOR_METAS:
        name, *args = OPERATOR_METAS[oper]
      elif oper in OPERATOR_MACROS:
        is_macro = True
        name, *args = OPERATOR_MACROS[oper]
      elif oper.startswith("*") and oper[1:] in OPERATOR_METAS:
        name, *args = OPERATOR_METAS[oper[1:]]
        name = "retro_" + name
      else:
        name, args = oper, []
      if args == ["", ""]:
        args = [","]
      obj = (TokenType.MACRO if is_macro else TokenType.META, name, *args)
    elif d["key_combo"]:
      obj = []
      for key in split_keys(d["key_combo"]):
        obj.append((TokenType.KEY_COMBO, key))
    elif d["escaped"]:
      obj = (TokenType.STRING, d["escaped"][1:])
    elif d["discord_emoji"]:
      obj = (TokenType.DISC_EMOJI, d["discord_emoji"])
    elif d["space"] is not None:
      obj = (TokenType.SPACE,)
    elif d["raw"]:
      if d["raw"] == " ":
        obj = (TokenType.SPACE,)
      else:
        obj = (TokenType.STRING, d["raw"])

    if isinstance(obj, list):
      lst.extend(obj)
    elif isinstance(obj, tuple):
      lst.append(obj)

  array = NSMutableArray.alloc().initWithArray_(lst)

  return array

def display_string(obj):
  if obj[0] == TokenType.CANCEL:
    return "Cancel Formatting"
  elif obj[0] == TokenType.COMMAND:
    if obj[1].lower() in PLOVER_COMMAND_FRIENDLY_NAMES:
      return f"Plover: {PLOVER_COMMAND_FRIENDLY_NAMES[obj[1]].lower()}"
    else:
      return obj[1].replace("_", " ").capitalize()
  elif obj[0] == TokenType.MODE_SPACE:
    return "Set Space:"
  elif obj[0] == TokenType.MODE:
    return MODE_FRIENDLY_NAMES.get(obj[1].lower(), f"Mode: {obj[1].lower()}")
  elif obj[0] == TokenType.GLUE:
    return "Glue:"
  elif obj[0] == TokenType.ATTACH_RAW:
    return "Attach"
  elif obj[0] == TokenType.ATTACH_INFIX:
    return "Attach Infix:"
  elif obj[0] == TokenType.ATTACH_PREFIX:
    return "Attach Prefix:"
  elif obj[0] == TokenType.ATTACH_SUFFIX:
    return "Attach Suffix:"
  elif obj[0] == TokenType.CARRY_CAP:
    return "Carry Capitalization"
  elif obj[0] == TokenType.CURRENCY:
    return "Format Currency"
  elif obj[0] == TokenType.KEY_COMBO:
    return format_key_seq(obj[1])
  elif obj[0] == TokenType.MACRO:
    if obj[1].lower() in MACRO_FRIENDLY_NAMES:
      macro_name = MACRO_FRIENDLY_NAMES[obj[1].lower()]
      if isinstance(macro_name, Function):
        try:
          macro_name = macro_name(*obj[2:])
        finally:
          pass
      elif "{0}" in macro_name:
        return macro_name.format(*[MACRO_FRIENDLY_NAMES.get(arg, str(arg)) for arg in obj[2:]])
      return macro_name
    else:
      args = f"({', '.join(obj[2:])})" if len(obj) > 2 else ""
      return f"Macro: {obj[1].lower()}{args}"
  elif obj[0] == TokenType.META:
    if obj[1].lower() in META_FRIENDLY_NAMES:
      meta_name = META_FRIENDLY_NAMES[obj[1].lower()]
      if isinstance(meta_name, Function):
        try:
          meta_name = meta_name(*obj[2:])
        finally:
          pass
      elif "{0}" in meta_name:
        return meta_name.format(*[META_FRIENDLY_NAMES.get(arg, str(arg)) for arg in obj[2:]])
      return meta_name
    else:
      args = f"({', '.join(obj[2:])})" if len(obj) > 2 else ""
      return f"Meta: {obj[1].lower()}{args}"
  elif obj[0] == TokenType.DISC_EMOJI:
    return f":{obj[1]}:"
  elif obj[0] == TokenType.SPACE:
    return "Space"
  elif obj[0] == TokenType.NOOP:
    return "Do Nothing"

  elif obj[0] == TokenType.STRING:
    return format_unicode(obj[1])
  else:
    return str(obj)
