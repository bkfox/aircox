
def ensure_list (value):
    if type(value) in (list, set, tuple):
        return value
    return [value]

