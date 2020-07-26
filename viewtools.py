"""
A collection of tools to deal with scopes and text in sublime view.
"""
import sublime
ST3 = sublime.version() >= '3000'

try:
    from .funcy import *
except ValueError: # HACK: for ST2 compatability
    from funcy import *


### Cursor and selection

def cursor_pos(view):
    return view.sel()[0].b

def list_cursors(view):
    return [s.b for s in view.sel()]

def set_cursor(view, pos):
    if iterable(pos):
        regions = [sublime.Region(p, p) for p in pos]
    else:
        regions = sublime.Region(pos, pos)
    set_selection(view, regions)

def map_selection(view, f):
    set_selection(view, map(f, view.sel()))

def set_selection(view, region):
    # NOTE: we need to materialize a possible iterator beore clearing selection,
    #       as mapping selection is a common techique.
    if iterable(region):
        region = list(region)

    view.sel().clear()
    add_selection(view, region)
    view.show(view.sel())

def add_selection(view, region):
    if iterable(region):
        if ST3:
            view.sel().add_all(list(region))
        else:
            # .add_all() doesn't work with python lists in ST2
            for r in region:
                view.sel().add(r)
    else:
        view.sel().add(region)


### Words

if ST3:
    def word_at(view, pos):
        if view.classify(pos) & (512 | sublime.CLASS_WORD_START | sublime.CLASS_WORD_END):
            return view.word(pos)

    def word_b(view, pos):
        start = view.find_by_class(pos - 1, False, sublime.CLASS_WORD_START)
        return view.word(start)

    def word_f(view, pos):
        start = view.find_by_class(pos, True, sublime.CLASS_WORD_START)
        return view.word(start)
else:
    def _word_at(view, pos):
        word = view.word(pos)
        return word, re_test(r'^\w+$', view.substr(word))

    def word_at(view, pos):
        word, is_word = _word_at(view, pos)
        if is_word:
            return word

    def word_b(view, pos):
        pos -= 1
        is_word = False
        while pos and not is_word:
            word, is_word = _word_at(view, pos - 1)
            if is_word:
                return word
            else:
                pos = word.begin()

    def word_f(view, pos):
        start = view.find(r'\b\w', pos + 1)
        return view.word(start)


### Lines

def line_at(view, pos):
    return view.line(pos)

def line_start(view, pos):
    line = view.line(pos)
    return sublime.Region(line.begin(), pos)

def line_end(view, pos):
    line = view.line(pos)
    return sublime.Region(pos, line.end())

def list_lines_b(view, pos):
    while pos:
        yield view.full_line(pos)
        pos = view.find_by_class(pos, False, sublime.CLASS_LINE_END)

def list_lines_f(view, pos):
    while pos < view.size():
        yield view.full_line(pos)
        pos = view.find_by_class(pos, True, sublime.CLASS_LINE_START)

if ST3:
    def line_b_begin(view, pos):
        if view.classify(pos) & sublime.CLASS_LINE_START:
            return newline_b(view, pos)
        else:
            return newline_b(view, newline_b(view, pos))

    def newline_b(view, pos):
        if pos > 0:
            return view.find_by_class(pos, False, sublime.CLASS_LINE_START)

    def newline_f(view, pos):
        if pos < view.size():
            return view.find_by_class(pos, True, sublime.CLASS_LINE_START)
else:
    def line_b_begin(view, pos):
        line_start = view.line(pos).begin()
        return newline_b(view, min(pos, line_start))

    def newline_b(view, pos):
        if pos > 0:
            return view.line(pos - 1).begin()

    def newline_f(view, pos):
        if pos < view.size():
            region = view.find(r'^', pos + 1)
            return region.end()


### Blocks

def block_at(view, pos):
    return region_at(list_blocks(view), pos)

def block_b(view, pos):
    return region_b(list_blocks(view), pos)

def block_f(view, pos):
    return region_f(list_blocks(view), pos)

def list_blocks(view):
    empty_lines = view.find_all(r'^\s*\n')
    return invert_regions(view, empty_lines)


### Regions

def region_at(regions, pos):
    return first(r for r in regions if r.begin() <= pos <= r.end())

def region_b(regions, pos):
    return first(r for r in reversed(regions) if r.begin() <= pos)

def region_f(regions, pos):
    return first(r for r in regions if pos < r.begin())


def full_region(view):
    return sublime.Region(0, view.size())

def shifted_region(region, shift):
    return sublime.Region(region.a + shift, region.b + shift)


def order_regions(regions):
    order = lambda r: (r.begin(), r.end())
    return sorted(regions, key=order)

def invert_regions(view, regions):
    # NOTE: regions should be non-overlapping and ordered,
    #       no check here for performance reasons
    start = 0
    end = view.size()
    result = []

    for r in regions:
        if r.a > start:
            result.append(sublime.Region(start, r.a))
        start = r.b

    if start < end:
        result.append(sublime.Region(start, end))

    return result

def swap_regions(view, edit, region1, region2):
    assert region1.b <= region2.a

    # hide selection before move and save shifted position to set it after
    sel = view.sel()
    regions = []
    for region in sel:
        if region1.contains(region):
            sel.subtract(region)
            regions.append(shifted_region(region, region2.b - region1.b))
        elif region2.contains(region):
            sel.subtract(region)
            regions.append(shifted_region(region, region1.a - region2.a))

    # swap text
    str1 = view.substr(region1)
    str2 = view.substr(region2)
    view.replace(edit, region2, str1)
    view.replace(edit, region1, str2)

    # set cursor position/selection to match moved regions
    add_selection(view, regions)

def cover_regions(regions):
    return reduce(lambda a, b: a.cover(b), regions)


### Scope

def scope_name(view, pos=None):
    if pos is None:
        pos = cursor_pos(view)
    return view.scope_name(pos)

def parsed_scope(view, pos=None):
    return parse_scope(scope_name(view, pos))

def source(view, pos=None):
    return first(vec[1] for vec in parsed_scope(view, pos) if vec[0] == 'source')

def parse_scope(scope_name):
    return [name.split('.') for name in scope_name.split()]

def is_escaped(view, pos):
    return any(s[0] in ('comment', 'string') for s in parsed_scope(view, pos))

def is_comment(view, pos):
    return any(s[0] == 'comment' for s in parsed_scope(view, pos))

def scope_re(view, pos, pattern):
    scope_lines = scope_name(view, pos).split()
    return any(re.search(pattern, line) for line in scope_lines)


### Smarts

def expand_min_gap(view, region):
    """
    Expands region so that it will cover minimum gap of empty lines around it.
    """
    empty_lines = view.find_all(r'^\s*\n')
    empty_neighbours = [r for r in empty_lines
                          if r.end() == region.begin() or r.begin() == region.end()]

    if not empty_neighbours:
        return region
    elif len(empty_neighbours) == 1:
        if is_view_bordering(view, region):
            return region.cover(empty_neighbours[0])
        else:
            return region
    else:
        min_gap = min(reversed(empty_neighbours), key=lambda r: view.substr(r).count('\n'))
        return region.cover(min_gap)

def is_view_bordering(view, region):
    return region.begin() == 0 or region.end() == view.size()


# String things

def find_iter(view, pattern, pos_or_region):
    region = pos_or_region if isinstance(pos_or_region, sublime.Region) else \
             sublime.Region(pos_or_region, view.size())
    start, end = region.begin(), region.end()
    found = sublime.Region(start, start)
    while found.a != -1:
        found = view.find(pattern, found.b)
        if found.b > end:
            break
        if not is_escaped(view, found.a):
            yield found


def count_curlies(view, region):
    curlies = count_reps(map(view.substr, find_iter(view, r'[{}]', region)))
    return curlies['{'] - curlies['}']

def find_closing_curly(view, pos, count=1):
    for curly in find_iter(view, r'[{}]', pos):
        count += 1 if view.substr(curly) == '{' else -1
        if count == 0:
            return curly


def find_opening_curly(view, pos, count=-1):
    for curly in _find_iter_back(view, r'[{}]', pos):
        count += 1 if view.substr(curly) == '{' else -1
        if count == 0:
            return curly


def _find_iter_back(view, pattern, pos):
    regex = re.compile(pattern)
    for line in _iter_lines_back(view, pos):
        base = line.begin()
        s = view.substr(line)
        for start, end in reversed(list(_re_iter_spans(regex, s))):
            if not is_escaped(view, base + start):
                yield sublime.Region(base + start, base + end)

def _iter_lines_back(view, pos):
    yield line_start(view, pos)
    pos = line_b_begin(view, pos)
    while pos is not None:
        line = view.full_line(pos)
        yield line
        pos = newline_b(view, pos)

def _re_iter_spans(pattern, s):
    regex = re.compile(pattern)
    p = 0
    while p < len(s):
        m = regex.search(s, p)
        if m is None:
            break
        _, e = span = m.span()
        yield span
        p = e + 1
