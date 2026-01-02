import re


def time(str):
    match = re.search("(?P<minutes>\\d+):(?P<seconds>\\d+(\\.\\d+)?)", str)
    if match:
        minutes = int(match.group("minutes"))
        seconds = float(match.group("seconds"))
        return minutes + seconds / 60.0
    else:
        return float(str)


def fmt_time(minutes):
    m, s = divmod(minutes * 60, 60)
    m, s = int(m), round(s, 2)
    if m > 0:
        return f"{m} min {s} sec"
    else:
        return f"{s} sec"


# Super incomplete for all of English, but enough for now.
def pluralize(name, count, name_only=False):
    if count == 1:
        pluralization = f"{name}"
    else:
        pluralization = f"{name}s"

    if name_only:
        return pluralization
    else:
        return f"{count} {pluralization}"
