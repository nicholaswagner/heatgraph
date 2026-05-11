import codecs
import re


RESET = "\033[0m"

_ESCAPE_RE = re.compile(
    r'\\(U[0-9a-fA-F]{8}|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|[0-7]{1,3}|[\\\'"abfnrtv0])'
)


def decode_escapes(s: str) -> str:
    return _ESCAPE_RE.sub(lambda m: codecs.decode(m.group(0), 'unicode_escape'), s)


def hex_to_ansi(hex_str: str) -> str:
    if not hex_str.startswith("#") or len(hex_str) != 7:
        return hex_str
    try:
        r = int(hex_str[1:3], 16)
        g = int(hex_str[3:5], 16)
        b = int(hex_str[5:7], 16)
        return f"\033[38;2;{r};{g};{b}m"
    except ValueError:
        return hex_str


def resolve_color(val: str) -> str:
    """Convert a color spec into an ANSI escape prefix.

    Accepts: '#RRGGBB' hex, '256:N' xterm-256 shorthand, raw escape sequences
    (e.g. '\\033[31m'), or any literal pass-through.
    """
    if not val:
        return ""
    if val.startswith("#"):
        return hex_to_ansi(val)
    if val.startswith("256:"):
        try:
            n = int(val[4:])
            return f"\033[38;5;{n}m"
        except ValueError:
            return val
    if val.startswith("\\") or val.startswith("\x1b"):
        return decode_escapes(val)
    return val
