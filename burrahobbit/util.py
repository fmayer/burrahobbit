def _all(iterable):
    for elem in iterable:
        if not elem:
            return False
    return True

try:
    all = all
except NameError:
    all = _all
