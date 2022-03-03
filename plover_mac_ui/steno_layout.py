from plover import system

def remove_numbers(keys, stroke):
  keys = set(keys)
  stroke = stroke[:]

  reverse_numbers = {value: key for key, value in system.NUMBERS.items()}

  has_numbers = False
  for key in list(keys):
    if key in system.NUMBERS.values():
      has_numbers = True
      keys.remove(key)
      keys.add(reverse_numbers[key])
      keys.add("#")
      stroke = stroke.replace(
        key.replace("-", ""), reverse_numbers[key].replace("-", ""))
  if has_numbers:
    stroke = "#" + stroke

  return list(keys), stroke
