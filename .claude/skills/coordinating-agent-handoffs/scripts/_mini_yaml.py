"""Tiny YAML-subset loader used by the handoff scripts (Python 3.8+, stdlib only).

Only the subset documented in blueprints/profile-format.md is supported:

  * block mappings        key: value          (nesting by indentation, spaces only)
  * block sequences       - item              (items may be scalars, flow values or
                                               block mappings starting after the dash)
  * flow collections      {a: 1, b: [x, y]}   [a, b]   (nestable, one line)
  * scalars               plain, "double", 'single'; true/false, null/~, ints, floats
  * comments              '#' at line start or after whitespace (outside quotes)

NOT supported (a YamlError is raised or the text is read literally as a string):
anchors/aliases, tags, block scalars (| and >), multi-line scalars, multi-document
files, tab indentation, complex keys. Values starting with one of | > & * ! % @ `
must be quoted. Quote anything that must stay a string but looks like a number
or boolean (for example versions such as "1.15").
"""
import re


class YamlError(ValueError):
    """Raised for malformed or unsupported YAML input."""


_INT_RE = re.compile(r"^[-+]?\d+$")
_FLOAT_RE = re.compile(r"^[-+]?\d+\.\d+$")
_ESC_RE = re.compile(r'\\(["\\nt])')
_ESC_MAP = {'"': '"', "\\": "\\", "n": "\n", "t": "\t"}
_UNSUPPORTED_START = "|>&*!%@`"


def _quote_opens(s, i):
    return i == 0 or s[i - 1] in " \t[{,:"


def _unquote(token):
    quote = token[0]
    if len(token) < 2 or token[-1] != quote:
        raise YamlError("unterminated quoted string: %s" % token)
    inner = token[1:-1]
    if quote == "'":
        return inner.replace("''", "'")
    return _ESC_RE.sub(lambda m: _ESC_MAP[m.group(1)], inner)


def scalar(token):
    """Convert one scalar token to a Python value."""
    t = token.strip()
    if t == "":
        return None
    if t[0] in "\"'":
        return _unquote(t)
    if t in ("true", "True", "TRUE"):
        return True
    if t in ("false", "False", "FALSE"):
        return False
    if t in ("null", "Null", "NULL", "~"):
        return None
    if _INT_RE.match(t):
        return int(t)
    if _FLOAT_RE.match(t):
        return float(t)
    return t


def _strip_comment(s):
    quote = None
    i = 0
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'" and _quote_opens(s, i):
            quote = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
        i += 1
    return s.rstrip()


def _split_kv(s):
    """Return (key, rest) for 'key: rest' / 'key:', else None."""
    quote = None
    i = 0
    while i < len(s):
        ch = s[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "\"'" and _quote_opens(s, i):
            quote = ch
        elif ch == ":" and (i + 1 == len(s) or s[i + 1] == " "):
            key = s[:i].strip()
            if not key:
                return None
            if key[0] in "\"'":
                key = _unquote(key)
            return key, s[i + 1:].strip()
        i += 1
    return None


class _Flow(object):
    """Parser for one-line flow collections."""

    def __init__(self, text, line):
        self.s = text
        self.i = 0
        self.n = line

    def err(self, msg):
        raise YamlError("line %d: %s" % (self.n, msg))

    def ws(self):
        while self.i < len(self.s) and self.s[self.i] in " \t":
            self.i += 1

    def value(self):
        self.ws()
        if self.i >= len(self.s):
            self.err("unexpected end of flow value")
        c = self.s[self.i]
        if c == "{":
            return self.mapping()
        if c == "[":
            return self.seq()
        if c in "\"'":
            return self.quoted()
        start = self.i
        while self.i < len(self.s) and self.s[self.i] not in ",]}":
            self.i += 1
        return scalar(self.s[start:self.i])

    def quoted(self):
        q = self.s[self.i]
        j = self.i + 1
        closed = False
        while j < len(self.s):
            if self.s[j] == "\\" and q == '"':
                j += 2
                continue
            if self.s[j] == q:
                if q == "'" and j + 1 < len(self.s) and self.s[j + 1] == "'":
                    j += 2
                    continue
                closed = True
                break
            j += 1
        if not closed:
            self.err("unterminated quoted string")
        token = self.s[self.i:j + 1]
        self.i = j + 1
        try:
            return _unquote(token)
        except YamlError as exc:
            self.err(str(exc))

    def mapping(self):
        self.i += 1
        result = {}
        while True:
            self.ws()
            if self.i >= len(self.s):
                self.err("unterminated '{'")
            if self.s[self.i] == "}":
                self.i += 1
                return result
            if self.s[self.i] in "\"'":
                key = self.quoted()
            else:
                start = self.i
                while self.i < len(self.s) and self.s[self.i] not in ":,}":
                    self.i += 1
                key = self.s[start:self.i].strip()
            self.ws()
            if self.i >= len(self.s) or self.s[self.i] != ":":
                self.err("expected ':' after key %r" % key)
            self.i += 1
            result[key] = self.value()
            self.ws()
            if self.i < len(self.s) and self.s[self.i] == ",":
                self.i += 1
                continue
            if self.i < len(self.s) and self.s[self.i] == "}":
                continue
            self.err("expected ',' or '}'")

    def seq(self):
        self.i += 1
        result = []
        while True:
            self.ws()
            if self.i >= len(self.s):
                self.err("unterminated '['")
            if self.s[self.i] == "]":
                self.i += 1
                return result
            result.append(self.value())
            self.ws()
            if self.i < len(self.s) and self.s[self.i] == ",":
                self.i += 1
                continue
            if self.i < len(self.s) and self.s[self.i] == "]":
                continue
            self.err("expected ',' or ']'")


def _flow(text, line):
    parser = _Flow(text, line)
    value = parser.value()
    parser.ws()
    if parser.i != len(text):
        parser.err("unexpected trailing text %r" % text[parser.i:])
    return value


def _inline(rest, line):
    first = rest[0]
    if first in "{[":
        return _flow(rest, line)
    if first in _UNSUPPORTED_START:
        raise YamlError("line %d: unsupported YAML construct starting with %r (quote the value)"
                        % (line, first))
    try:
        return scalar(rest)
    except YamlError as exc:
        raise YamlError("line %d: %s" % (line, exc))


def _is_seq_item(text):
    return text == "-" or text.startswith("- ")


def load(text):
    """Parse a YAML-subset document into dicts, lists and scalars."""
    lines = []
    for n, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        lead = raw[: len(raw) - len(raw.lstrip())]
        if "\t" in lead:
            raise YamlError("line %d: tab indentation is not supported" % n)
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        if stripped.strip() == "---":
            raise YamlError("line %d: document markers are not supported" % n)
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((indent, stripped.strip(), n))
    if not lines:
        return {}
    value, i = _block(lines, 0, lines[0][0])
    if i != len(lines):
        raise YamlError("line %d: unexpected content" % lines[i][2])
    return value


def parse_frontmatter(text):
    """Split '---' frontmatter from the body. Returns (dict, body)."""
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        raise YamlError("frontmatter: file must start with a '---' line")
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            data = load("\n".join(lines[1:idx]))
            if not isinstance(data, dict):
                raise YamlError("frontmatter: must be a mapping of key: value lines")
            return data, "\n".join(lines[idx + 1:])
    raise YamlError("frontmatter: missing closing '---' line")


def _block(lines, i, indent):
    if lines[i][0] != indent:
        raise YamlError("line %d: unexpected indentation" % lines[i][2])
    if _is_seq_item(lines[i][1]):
        return _sequence(lines, i, indent)
    return _mapping(lines, i, indent)


def _sequence(lines, i, indent):
    result = []
    while i < len(lines) and lines[i][0] == indent and _is_seq_item(lines[i][1]):
        ind, text, n = lines[i]
        tail = text[1:]
        rest = tail.strip()
        if rest == "":
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                value, i = _block(lines, i, lines[i][0])
            else:
                value = None
            result.append(value)
        elif rest[0] not in "{[" and _split_kv(rest) is not None:
            col = ind + 1 + (len(tail) - len(tail.lstrip()))
            lines[i] = (col, rest, n)
            value, i = _mapping(lines, i, col)
            result.append(value)
        else:
            result.append(_inline(rest, n))
            i += 1
    if i < len(lines) and lines[i][0] > indent:
        raise YamlError("line %d: unexpected indentation" % lines[i][2])
    return result, i


def _mapping(lines, i, indent):
    result = {}
    while i < len(lines) and lines[i][0] == indent:
        ind, text, n = lines[i]
        if _is_seq_item(text):
            raise YamlError("line %d: unexpected list item inside a mapping" % n)
        kv = _split_kv(text)
        if kv is None:
            raise YamlError("line %d: expected 'key: value', got %r" % (n, text))
        key, rest = kv
        if key in result:
            raise YamlError("line %d: duplicate key %r" % (n, key))
        i += 1
        if rest == "":
            if i < len(lines) and lines[i][0] > indent:
                value, i = _block(lines, i, lines[i][0])
            elif i < len(lines) and lines[i][0] == indent and _is_seq_item(lines[i][1]):
                value, i = _sequence(lines, i, indent)
            else:
                value = None
        else:
            value = _inline(rest, n)
        result[key] = value
    if i < len(lines) and lines[i][0] > indent:
        raise YamlError("line %d: unexpected indentation" % lines[i][2])
    return result, i
