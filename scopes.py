import sublime, sublime_plugin
from .funcy import *

try:
    from .funcy import *
    from .viewtools import (
        list_cursors, set_selection, map_selection,
        source,
        region_f, region_b,
        order_regions,
    )
except ValueError: # HACK: for ST2 compatability
    from funcy import *
    from viewtools import (
        list_cursors, set_selection, map_selection,
        source,
        region_f, region_b,
        order_regions,
    )


class ScopesTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print("test")


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
        # TODO: skip brackets in comments and strings
        bracket = view.find(r'[{}]', bracket.b)
        if view.substr(bracket) == '{':
            count += 1
        else:
            count -= 1
    return bracket

def _func_defs(view):
    return view.find_by_selector('meta.function')
