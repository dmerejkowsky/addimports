IFDEF = "#ifdef"
IFNDEF = "#ifndef"
INCL = "#include"
DOS_EOL = "\r\n"
UNIX_EOL = "\n"


class Adder:
    def __init__(self, buffer, *, lang):
        self.source = CSource(buffer)

    def add_import(self, fix):
        to_insert = f"#include {fix}"
        text = self.source.get()
        pos = self.source.find_insert_pos()
        newline = self.source.get_newline()
        new_text = text[:pos] + newline + to_insert + newline + text[pos:]
        return new_text


def fix_include(s):
    if not s.startswith("#include"):
        s = "#include " + s
    return s


class CSource:
    def __init__(self, text):
        self.text = text
        self.newline = self.discover_newline()

        self.memo_has_ifdef = self.has(IFDEF)
        self.memo_has_ifndef = self.has(IFNDEF)
        self.memo_has_include = self.has(INCL)

    def get(self):
        return self.text

    def get_newline(self):
        return self.newline

    def has(self, text):
        return text in self.text

    def first(self, text):
        try:
            return self.text.index(text)
        except ValueError:
            return -1

    def has_ifdef(self):
        return self.memo_has_ifdef

    def has_ifndef(self):
        return self.memo_has_ifndef

    def has_include(self):
        return self.memo_has_include

    def first_ifdef(self):
        return self.first(IFDEF)

    def first_ifndef(self):
        return self.first(IFNDEF)

    def first_include(self):
        return self.first(INCL)

    def next_include(self, pos):
        try:
            return self.text[pos + 1 :].index(INCL)
        except ValueError:
            return -1

    def first_include_after_ifdef(self):
        return self.first_include_after_word(IFDEF)

    def first_include_after_ifndef(self):
        return self.first_include_after_word(IFNDEF)

    def the_rest(self, pos):
        return CSource(self.text[pos:])

    def discover_newline(self):
        if "\r\n" in self.text:
            return "\r\n"
        else:
            return "\n"

    def has_ifdef_before(self, pos):
        found = self.first_ifdef()
        return (found != -1) and (found < pos)

    def first_include_after_word(self, word):
        if not self.has_include() and not self.has(word):
            return 0
        if self.has_include() and not self.has(word):
            return self.first_include()

        pos = self.first(word)
        tail = self.the_rest(pos)
        if tail.has_include():
            return pos + tail.first_include()
        return pos

    def end_of_line(self, pos):
        tail = self.the_rest(pos + 1)
        npos = tail.first(self.newline)
        if npos != -1:
            return pos + 1 + npos
        return 0

    def find_insert_pos(self):  # noqa: C901
        has_include = 1
        has_ifdef = 2
        has_ifndef = 4

        n = 0
        if self.has_include():
            n |= has_include

        if self.has_ifdef():
            n |= has_ifdef

        if self.has_ifndef():
            n |= has_ifndef

        pos = 0

        if n == has_include:
            pos = self.first_include()
        elif n == has_ifdef:
            pos = self.first_ifdef()
        elif n == has_ifndef:
            pos = self.first_ifndef()
        elif n == has_ifdef | has_ifndef:
            pos = min(self.first_ifdef(), self.first_ifndef())
        elif n == has_include | has_ifdef:
            pos = self.first_include_after_ifdef()
        elif n == has_include | has_ifndef:
            pos = self.first_include_after_ifndef()
        elif n == has_include | has_ifndef | has_ifndef:
            pos = min(
                self.first_include_after_ifdef(), self.first_include_after_ifndef()
            )
        else:
            return 0

        return self.end_of_line(pos)
