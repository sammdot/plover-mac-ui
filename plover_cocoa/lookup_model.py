from collections import namedtuple
from enum import Enum
import re
from os.path import relpath

from plover import system
from plover.oslayer.config import CONFIG_DIR
from plover.resource import ASSET_SCHEME
from plover.steno import sort_steno_strokes
from plover_cocoa.resources import icon_named
from plover_cocoa.steno import STROKE_DELIMITER

Translation = namedtuple("Translation", "strokes translation dictionary comment bad reason")
Translation.__new__.__defaults__ = (None,) * len(Translation._fields)

MAX_RESULTS = 50

class LookupMethod(Enum):
  TRANSLATION = 0
  STROKE = 1

class LookupResultReason(Enum):
  UNDEFINED = 0
  DISABLED = 1
  OVERRIDDEN = 2
  DELETED = 3
  DEFINED = 99

  @property
  def icon(self):
    return icon_named(f"dict-{self.name.lower()}", template=False)

def rank_approx(key, tl):
  if key.lower() == tl.lower():
    return 0
  elif tl.lower().startswith(key.lower()):
    return 1
  else:
    return 2

SUB_RE = re.compile(r"(^{\^|\^}$|{\^})")

def approx_equal(a, b):
  return SUB_RE.sub("", a) == SUB_RE.sub("", b)


PREFIX = "../../../projects/plover/dict/"

def dict_short_name(path):
  if ASSET_SCHEME in path:
    _, module, path = path.split(":", 2)
    if "." in module:
      module = module.split(".", 1)[0]
    if "/" in path:
      path = path.rsplit("/", 1)[1]
    short_name = path.rsplit(".", 1)[0]
    return f"{module}:{short_name}"
  elif path.startswith(PREFIX):
    return path[len(PREFIX):].rsplit(".", 1)[0]
  elif path.startswith("dict/"):
    return path.split("/", 1)[1].rsplit(".", 1)[0]
  return path.rsplit(".", 1)[0]


class Dictionary:
  @staticmethod
  def short_dict_name(dict):
    path = relpath(dict.path, CONFIG_DIR)
    return dict_short_name(path) or path

  def approx_translations(self, key):
    translations = {key}
    for d in self.dicts:
      translations |= {tl for tl in d.reverse if key.lower() in tl.lower()}
    return sorted(translations, key=lambda tl: (rank_approx(key, tl), len(tl), tl))[:MAX_RESULTS]

  def approx_strokes(self, key):
    strokes = {tuple(key.split(STROKE_DELIMITER))}
    for d in self.dicts:
      strokes |= {tl for tl in d._dict if key.upper() in STROKE_DELIMITER.join(tl).upper()}
    return sorted(strokes, key=lambda tl: (
      rank_approx(key, STROKE_DELIMITER.join(tl)), len(tl), sum(map(len, tl)), tl))[:MAX_RESULTS]

  def find_by_translation(self, key):
    strokes = set()
    for d in self.dicts:
      matches = d.reverse_lookup(key) or []
      if not matches:
        continue
      for match in matches:
        strokes.add(match)

    existing_strokes = set()
    full_results = []
    for d in self.dicts:
      path = Dictionary.short_dict_name(d)
      for stroke in strokes:
        match = d.get(stroke)
        if match:
          comment = d.lookup(stroke)[1] if hasattr(d, "lookup") else None
          full_results.append(
            Translation(
              strokes=[stroke], translation=match, dictionary=path, comment=comment,
              reason=(
                LookupResultReason.DISABLED if not d.enabled else
                LookupResultReason.OVERRIDDEN if stroke in existing_strokes else
                LookupResultReason.DEFINED)))
          if d.enabled and stroke not in existing_strokes:
            existing_strokes.add(stroke)

    has_good_def = any(approx_equal(tl.translation, key) and tl.reason == LookupResultReason.DEFINED for tl in full_results)
    has_any_def = any(approx_equal(tl.translation, key) and tl.reason != LookupResultReason.UNDEFINED for tl in full_results)

    short_results = [
      Translation(
        strokes=sort_steno_strokes(sum(
          [tl.strokes for tl in full_results if
            approx_equal(tl.translation, key) and tl.reason == LookupResultReason.DEFINED], [])),
        translation=key,
      )
    ] if has_good_def else [
      Translation(
        strokes=sort_steno_strokes(sum(
          [tl.strokes for tl in full_results if
            approx_equal(tl.translation, key) and tl.reason != LookupResultReason.UNDEFINED], [])),
        translation=key,
        bad=True,
      )
    ] if has_any_def else []
    return full_results, short_results

  def find_by_stroke(self, key):
    existing_strokes = set()
    full_results = []
    for d in self.dicts:
      path = Dictionary.short_dict_name(d)
      match = d.get(key) or None

      if not match:
        continue

      comment = d.lookup(key)[1] if hasattr(d, "lookup") else None
      full_results.append(
        Translation(
          strokes=[key], translation=match, dictionary=path, comment=comment,
          reason=(
            LookupResultReason.DISABLED if not d.enabled else
            LookupResultReason.OVERRIDDEN if key in existing_strokes else
            LookupResultReason.DEFINED)))
      if d.enabled and key not in existing_strokes:
        existing_strokes.add(key)

    defined_results = [tl for tl in full_results if tl.reason == LookupResultReason.DEFINED]
    short_results = [
      Translation(
        strokes=[key],
        translation=defined_results[0].translation,
      )
    ] if defined_results else []
    return full_results, short_results
