import sublime, sublime_plugin
from .funcy import *

from .viewtools import (
    cursor_pos, set_cursor, set_selection, map_selection,
    source,
    order_regions,
)


# Free Ctrl-*:
# - Ctrl-K (heavily used)
# - Ctrl-,
# - Ctrl-'
# Less used:
# - Ctrl-E
#
#
#  TODO:
#  (separate for each language)
#  - detect function
#  - detect function scope (func - name - decorators)
#  - detect class
#  - detect class scope
#  - detect block
#  - detect paragraph (in text or comments)
#  - choose between paragraph, block, function or class automatically
#  (language independent)
#  - select scope
#  - delete scope
#  - Ctrl-D enchanced
#  - select all in scope


class ScopesTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print('test')


class FindWordForwardCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pos = cursor_pos(self.view)
        region = word_at(self.view, pos)
        if not region:
            return
        word = self.view.substr(region)

        all_regions = self.view.find_all(r'\b%s\b' % word)
        next_region = region_f(all_regions, region.end()) or first(all_regions)

        set_cursor(self.view, next_region.begin())

class FindWordBackCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pos = cursor_pos(self.view)
        region = word_at(self.view, pos)
        if not region:
            return
        word = self.view.substr(region)

        all_regions = self.view.find_all(r'\b%s\b' % word)
        next_region = region_b(all_regions, region.begin() - 1) or last(all_regions)

        set_cursor(self.view, next_region.begin())


class SmartUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # TODO: jump by selectors in css/less/...
        funcs = find_functions(self.view)
        classes = self.view.find_by_selector('meta.class')
        regions = order_regions(funcs + classes)

        def smart_up(pos):
            target = region_b(regions, pos.begin() - 1) or last(regions)
            return target.begin()

        map_selection(self.view, smart_up)

class SmartDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        funcs = find_functions(self.view)
        classes = self.view.find_by_selector('meta.class')
        regions = order_regions(funcs + classes)

        def smart_down(region):
            target = region_f(regions, region.end()) or first(regions)
            return target.begin()

        map_selection(self.view, smart_down)



class SelectFuncCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        blocks = [func_at(self.view, p) for p in list_cursors(self.view)]
        set_selection(self.view, blocks)

class SelectBlockCommand(sublime_plugin.TextCommand):
     def run(self, edit):
        blocks = [block_at(self.view, p) for p in list_cursors(self.view)]
        set_selection(self.view, blocks)


def list_cursors(view):
    return [s.b for s in view.sel()]


def word_at(view, pos):
    if view.classify(pos) & (512 | sublime.CLASS_WORD_START | sublime.CLASS_WORD_END):
        return view.word(pos)

def word_b(view, pos):
    if view.classify(pos) & sublime.CLASS_WORD_START:
        pos -= 1
    start = view.find_by_class(pos, False, sublime.CLASS_WORD_START)
    return view.word(start)

def word_f(view, pos):
    if view.classify(pos) & sublime.CLASS_WORD_START:
        start = pos
    else:
        start = view.find_by_class(pos, True, sublime.CLASS_WORD_START)
    return view.word(start)


def line_at(view, pos):
    return view.line(pos)

def line_start(view, pos):
    line = view.line(pos)
    return sublime.Region(line.begin(), pos)

def line_end(view, pos):
    line = view.line(pos)
    return sublime.Region(pos, line.end())


def block_at(view, pos):
    return region_at(blocks(view), pos)

def block_b(view, pos):
    return region_b(blocks(view), pos)

def block_f(view, pos):
    return region_f(blocks(view), pos)

def blocks(view):
    empty_lines = view.find_all(r'^\s*\n')
    return invert_regions(view, empty_lines)


def find_functions(view):
    funcs = view.find_by_selector('meta.function')
    if source(view) == 'python':
        is_junk = lambda r: re_test('^(lambda|\s*\@)', view.substr(r))
        funcs = lremove(is_junk, funcs)
    return funcs

def func_at(view, pos):
    defs = _func_defs(view)
    if source(view, pos) == 'python':
        is_junk = lambda r: re_test('^(lambda|\s*\@)', view.substr(r))
        defs = lremove(is_junk, defs)
    func_def = region_b(defs, pos)

    lang = source(view, pos)
    if lang == 'python':
        next_line = view.find_by_class(func_def.end(), True, sublime.CLASS_LINE_START)
        return func_def.cover(view.indented_region(next_line))
    elif lang == 'js':
        start_bracket = view.find(r'{', func_def.end(), sublime.LITERAL)
        end_bracket = find_matching_bracket(view, start_bracket)
        return func_def.cover(end_bracket)
    else:
        return func_def

def find_matching_bracket(view, bracket):
    count = 1
    while count > 0 and bracket.a != -1:
        bracket = view.find(r'[{}]', bracket.b)
        if view.substr(bracket) == '{':
            count += 1
        else:
            count -= 1
    return bracket

def _func_defs(view):
    return view.find_by_selector('meta.function')


### Regions

def region_at(regions, pos):
    return first(r for r in regions if r.begin() <= pos <= r.end())

def region_b(regions, pos):
    return first(r for r in reversed(regions) if r.begin() <= pos)

def region_f(regions, pos):
    return first(r for r in regions if pos < r.begin())

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
