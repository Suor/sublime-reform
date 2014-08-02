import sublime, sublime_plugin
from .funcy import *

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
        word = self.view.substr(region)

        all_regions = self.view.find_all(r'\b%s\b' % word)
        next_region = region_f(all_regions, region.end()) or first(all_regions)

        set_cursor(self.view, pos + next_region.begin() - region.begin())

class FindWordBackCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pos = cursor_pos(self.view)
        region = word_at(self.view, pos)
        word = self.view.substr(region)

        all_regions = self.view.find_all(r'\b%s\b' % word)
        next_region = region_b(all_regions, region.begin()-1) or last(all_regions)

        set_cursor(self.view, pos + next_region.begin() - region.begin())

class SelectFuncCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # print 1 , asd
        region = func_at(self.view, cursor_pos(self.view))
        # region = blocks(self.view)
        # region = word_expand(self.view, cursor_pos(self.view))
        if region:
            set_selection(self.view, region)
        # print('Test command')


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
    return region_at(blocks(views), pos)

def block_b(view, pos):
    return region_b(blocks(views), pos)

def block_f(view, pos):
    return region_f(blocks(views), pos)

def blocks(view):
    empty_lines = view.find_all(r'^\s*\n')
    return invert_regions(view, empty_lines)


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
    return first(r for r in regions if r.a <= pos < r.b)

def region_b(regions, pos):
    return first(r for r in reversed(regions) if r.a <= pos)

def region_f(regions, pos):
    return first(r for r in regions if pos < r.b)

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


### Utils

def cursor_pos(view):
    return view.sel()[0].b

def set_cursor(view, pos):
    if iterable(pos):
        regions = [sublime.Region(p, p) for p in pos]
    else:
        regions = sublime.Region(pos, pos)
    set_selection(view, regions)

def set_selection(view, region):
    if iterable(region):
        region = list(region)

    view.sel().clear()
    if iterable(region):
        view.sel().add_all(region)
    else:
        view.sel().add(region)
    view.show(view.sel())
