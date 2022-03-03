from AppKit import NSFont

DEFAULT_FONT = NSFont.systemFontOfSize_(NSFont.systemFontSize())

STENO_FONT = "JetBrainsMono"  # "CartographCF"
ZH_JA_STENO_FONT = "Sarasa-Mono-TC"
KOREAN_STENO_FONT = "NotoSansMonoCJKtc"

KEY_NAME_SIZE = 20
SMALL_KEY_NAME_SIZE = 16
KEY_LIST_SIZE = 24
PAPER_TAPE_SIZE = 16
LOOKUP_STENO_SIZE = 16
SUGGESTIONS_SIZE = 14
SUGGESTIONS_STENO_SIZE = 13
LOOKUP_LIST_SIZE = 14

def is_korean(text):
  return any(ord(c) in range(0x3130, 0x3190) for c in text)

def is_zh_ja(text):
  return any(ord(c) > 0x3000 for c in text) and not is_korean(text)

def steno_font(text):
  return KOREAN_STENO_FONT if is_korean(text) else \
    ZH_JA_STENO_FONT if is_zh_ja(text) else STENO_FONT

def paper_tape_font(text):
  return NSFont.fontWithName_size_(f"{steno_font(text)}-Regular",
    PAPER_TAPE_SIZE)

def suggestions_steno_font(text):
  return NSFont.fontWithName_size_(f"{steno_font(text)}-Regular",
    SUGGESTIONS_STENO_SIZE)

def lookup_steno_font(text):
  return NSFont.fontWithName_size_(f"{steno_font(text)}-Regular",
    LOOKUP_STENO_SIZE)

def key_name_font(text):
  return NSFont.fontWithName_size_(f"{steno_font(text)}-Regular", KEY_NAME_SIZE)

def key_list_font(text):
  light_font = NSFont.fontWithName_size_(
    f"{steno_font(text)}-Light", KEY_LIST_SIZE)
  if not light_font:
    return NSFont.fontWithName_size_(
      f"{steno_font(text)}-Regular", KEY_LIST_SIZE)
  return light_font

def key_list_bold_font(text):
  return NSFont.fontWithName_size_(f"{steno_font(text)}-Bold", KEY_LIST_SIZE)

SUGGESTIONS_FONT = NSFont.boldSystemFontOfSize_(SUGGESTIONS_SIZE)
LOOKUP_LIST_FONT = NSFont.boldSystemFontOfSize_(LOOKUP_LIST_SIZE)
SMALL_KEY_NAME_FONT = NSFont.systemFontOfSize_(SMALL_KEY_NAME_SIZE)

HANGUL = {
  "ㅎ": "ﾾ",
  "ㅁ": "ﾱ",
  "ㄱ": "ﾡ",
  "ㅈ": "ﾸ",
  "ㄴ": "ﾤ",
  "ㄷ": "ﾧ",
  "ㅇ": "ﾷ",
  "ㅅ": "ﾵ",
  "ㅂ": "ﾲ",
  "ㄹ": "ﾩ",
  "ㅗ": "ￌ",
  "ㅏ": "ￂ",
  "ㅜ": "ￓ",
  "ㅓ": "ￆ",
  "ㅣ": "ￜ",
  "ㅎ": "ﾾ",
  "ㅇ": "ﾷ",
  "ㄹ": "ﾩ",
  "ㄱ": "ﾡ",
  "ㄷ": "ﾧ",
  "ㅂ": "ﾲ",
  "ㄴ": "ﾤ",
  "ㅅ": "ﾵ",
  "ㅈ": "ﾸ",
  "ㅁ": "ﾱ",
}

def to_halfwidth(text):
  # return "".join([HANGUL.get(c, c) for c in text])
  return text
