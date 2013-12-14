# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import re
from itertools import chain, takewhile
from functools import reduce

#  DONE:
#  - Move words and code blocks
#  - Delete block
#  - Select block
#  - Move cursor up and down by functions and classes
#  - Wrap expression in function call
#
# TODO:
#  - like Ctrl+D/Alt-F3 but respect word boundaries and case. Also, select all withing scope
#  - extract subexpression to assignment
#  - unwrap expression in function
#  - Delete empty lines when delete block
#  - Move by blocks not in functions
#  - Separate move cursor/block for function/class?
#  - Better move block commands
#  - Smarter empty line handling when moving blocks
#  - Move functions up and down
#  - Select blocks, scopes, functions and classes
#  - Break long lines
#  - Reform dicts (object literals) from one-line to multi-line and back
#  - Same for calls, calls with keyword arguments, array literals
#  - Break long strings, several variants including switching to multiline separators
#  - Align =, =>, :, \ and other punctuation
#  - Reform multiline list, set, dict comprehensions and generator expressions
#  - Reform for loop to list comprehension
#  - Switch brackets - parentheses - whatever

from .funcy import *
from .viewtools import (
    source,
    cursor_pos, set_cursor,
    word_at, word_after, word_before, swap_regions,
    region_before_pos, region_after_pos,
    full_region, invert_regions, order_regions,

    region_up, region_down
)

# s = u"Привет, весёлые игрушки, мы пришли вас съесть! Бойтесь кровожадных нас, и прячтесь по углам, закрыв глазки!"

# s = u"Привет, весёлые игрушки, мы пришли вас съесть!"               \
#   + u"Бойтесь кровожадных нас, и прячтесь по углам, закрыв глазки!"


class MoveWordRightCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # We go from right to left to correctly handle overlapping regions
        for s in reversed(self.view.sel()):
            pos = s.b
            word1 = word_at(self.view, pos)
            word2 = word_after(self.view, pos)
            swap_regions(self.view, edit, word1, word2)

class MoveWordLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for s in self.view.sel():
            pos = s.b
            word1 = word_at(self.view, pos)
            word2 = word_before(self.view, pos)
            swap_regions(self.view, edit, word2, word1)


class MoveBlockUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        empty_lines = self.view.find_all(r'^\s*\n')
        blocks = invert_regions(self.view, empty_lines)

        pos = cursor_pos(self.view)
        this_block = region_before_pos(blocks, pos)
        prev_block = region_before_pos(blocks, this_block.begin() - 1)
        swap_regions(self.view, edit, prev_block, this_block)
        self.view.show(prev_block)

class MoveBlockDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        empty_lines = self.view.find_all(r'^\s*\n')
        blocks = invert_regions(self.view, empty_lines)

        pos = cursor_pos(self.view)
        this_block = region_before_pos(blocks, pos)
        next_block = region_after_pos(blocks, this_block.end())
        swap_regions(self.view, edit, this_block, next_block)
        self.view.show(next_block)

class DeleteBlockCommand(sublime_plugin.TextCommand):
     def run(self, edit):
        empty_lines = self.view.find_all(r'^\s*\n')
        blocks = invert_regions(self.view, empty_lines)

        pos = cursor_pos(self.view)
        this_block = region_before_pos(blocks, pos)
        self.view.erase(edit, this_block)

class SelectBlockCommand(sublime_plugin.TextCommand):
     def run(self, edit):
        empty_lines = self.view.find_all(r'^\s*\n')
        blocks = invert_regions(self.view, empty_lines)

        pos = cursor_pos(self.view)
        this_block = region_before_pos(blocks, pos)
        set_selection(self.view, this_block)


class SmartUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        funcs = find_functions(self.view)
        classes = self.view.find_by_selector('meta.class')
        regions = order_regions(funcs + classes)

        def smart_up(region):
            target = region_up(regions, region.end())
            if target is not None:
                return target.begin()
            else:
                return region

        map_selection(self.view, smart_up)

class SmartDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        funcs = find_functions(self.view)
        classes = self.view.find_by_selector('meta.class')
        regions = order_regions(funcs + classes)

        def unit_down(region):
            print('region', region)
            target = region_down(regions, region.end())
            if target is not None:
                print('target', target)
                return target.begin()
            else:
                return region

        map_selection(self.view, unit_down)


class EncallCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        new_sels = []
        for s in self.view.sel():
            line = self.view.line(s.b)
            line_str = self.view.substr(line)
            m = match_around(r'[\w\.]+', line_str, s.b - line.begin())
            if m:
                r = sublime.Region(m[0] + line.begin(), m[1] + line.begin())
                s = self.view.substr(r)
                self.view.replace(edit, r, '(%s)' % s)
                new_sels.append(r.begin())

        set_selection(self.view, new_sels)

class ReformTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        new_sels = []
        for s in self.view.sel():
            line = self.view.line(s.b)
            line_str = self.view.substr(line)
            m = match_around(r'[\w\.]+', line_str, s.b - line.begin())
            if m:
                r = sublime.Region(m[0] + line.begin(), m[1] + line.begin())
                s = self.view.substr(r)
                # set_selection(self.view, r)
                self.view.replace(edit, r, '(%s)' % s)
                new_sels.append(r.begin())
            # exprs = re.findall(r'[\w\.]+', line_str)

        # print('hi')
        set_selection(self.view, new_sels)


_re_type = type(re.compile(r''))

def match_around(regex, s, pos):
    if not isinstance(regex, _re_type):
        regex = re.compile(regex)

    p = 0
    m = None
    while p <= pos:
        m = regex.search(s, p)
        if not m or m.start() <= pos <= m.end():
            break
        else:
            p = m.end()

    return (m.start(), m.end()) if m else None



def find_functions(view):
    funcs = view.find_by_selector('meta.function')
    if source(view) == 'python':
        is_lambda = lambda r: view.substr(r).startswith('lambda')
        funcs = lremove(is_lambda, funcs)
    return funcs


def map_selection(view, f):
    set_selection(view, map(f, view.sel()))

def set_selection(view, region):
    if iterable(region):
        region = list(region)

    view.sel().clear()
    if iterable(region):
        view.sel().add_all(region)
    else:
        view.sel().add(region)
    view.show(view.sel())


# TODO: deal with lambdas somehow
def function_up(view, pos):
    func_def = function_def_up(view, pos)

    lang = source(view)
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

def function_def_up(view, pos):
    funcs = view.find_by_selector('meta.function')
    return region_up(funcs, pos)

def indented_up(view, pos):
    line = non_empty_line_up(view, pos)
    return view.indented_region(line.a)

def indented_block_up(view, pos):
    line = non_empty_line_up(view, pos)
    indent = re_find(r'^[ \t]*', view.substr(line))

    if indent:
        proper_indented = lambda l: view.substr(l).startswith(indent)
        lines = chain(
            takewhile(proper_indented, lines_up(view, line.a)),
            takewhile(proper_indented, lines_down(view, line.a)),
        )
        return cover_regions(lines)
    else:
        # No point in selecting everything
        return sublime.Region(pos, pos)

def non_empty_line_up(view, pos):
    return first(l for l in lines_up(view, pos) if not re_test(r'^\s*$', view.substr(l)))

def lines_up(view, pos):
    while pos:
        yield view.full_line(pos)
        pos = view.find_by_class(pos, False, sublime.CLASS_LINE_END)

def lines_down(view, pos):
    while pos < view.size():
        yield view.full_line(pos)
        pos = view.find_by_class(pos, True, sublime.CLASS_LINE_START)

def cover_regions(regions):
    return reduce(sublime.Region.cover, regions)
