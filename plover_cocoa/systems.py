from plover.registry import registry

MACHINE_NAMES = {
  "Keyboard": "Keyboard",
  "Gemini PR": "Gemini PR",
  "Stenograph USB": "Stentura",
  "Stenograph Wi-Fi": "Luminex",
  "Plover HID": "HID",
}

SYSTEM_NAMES = {
  "English Stenotype": "Stenotype",
  "French LaSalle": "LaSalle",
  # "Chinese Yawei": "亞偉",
  # "Chinese SanSan": "珊々",
  # "Japanese Sokutaipu": "速タイプ",
  # "Japanese Hachidori": "はちどり",
  # "Korean Modern C": "CAS",
  "Korean Ireland": "Korean",
}

MACHINE_ICONS = {
  "Keyboard": "keyboard",
  "TX Bolt": "txbolt",
  "Gemini PR": "gemini",
  "Passport": "serial",
  "ProCAT": "serial",
  "Stentura": "serial",
  "Stenograph USB": "usb",
  "Stenograph Wi-Fi": "wifi",
  "Plover HID": "usb",
}

SYSTEM_ABBRS = {
  "English Stenotype": "EN",
  "French LaSalle": "FR",
  "Chinese Yawei": "ZH",
  "Japanese Sokutaipu": "JA",
}

SYSTEM_ICONS = {
  "English Stenotype": "US",
  "French LaSalle": "CA",
  "Chinese Yawei": "CN",
  "Chinese SanSan": "HK",
  "Japanese Hachidori": "JP",
  "Korean Modern C": "KR",
}

def pretty_machine_name(name):
  return MACHINE_NAMES.get(name, name)

def pretty_system_name(name):
  return SYSTEM_NAMES.get(name, name)

def machine_icon(name):
  return MACHINE_ICONS.get(name, "state")

def system_abbr(name):
  return SYSTEM_ABBRS.get(name, name)

def system_icon(name):
  return SYSTEM_ICONS.get(name, name)

def machine_plugin(name):
  try:
    return registry.get_plugin("machine", name)
  except:
    return None

def system_plugin(name):
  try:
    return registry.get_plugin("system", name)
  except:
    return None
