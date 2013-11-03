# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import re
from itertools import chain, takewhile
from functools import reduce

#  DONE:
#  - Move words and code blocks
#  - Delete block
#
# TODO:
#  - Better move block commands
#  - Delete empty lines when delete block
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

from .viewtools import (
    source,
    set_selection, cursor_pos, set_cursor,
    word_at, word_after, word_before, swap_regions,
    region_before_pos, region_after_pos,
    full_region, invert_regions
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

class ReformTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pos = cursor_pos(self.view)
        block = indented_up(self.view, pos)
        print(block)
        # empty_lines = self.view.find_all(r'^\s*\n')
        # blocks = invert_regions(self.view, empty_lines)

        # this_block = region_before_pos(blocks, pos)
        # # next_block = region_after_pos(blocks, this_block.end())
        set_selection(self.view, block)
        # swap_regions(self.view, edit, this_block, next_block)

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
    return region_before_pos(funcs, pos)

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


### funcy seqs

def first(seq):
    return next(iter(seq), None)


### funcy strings

from operator import methodcaller

def _make_getter(regex):
    if regex.groups == 0:
        return methodcaller('group')
    elif regex.groups == 1 and regex.groupindex == {}:
        return methodcaller('group', 1)
    elif regex.groupindex == {}:
        return methodcaller('groups')
    elif regex.groups == len(regex.groupindex):
        return methodcaller('groupdict')
    else:
        return identity

_re_type = type(re.compile(r''))

def _prepare(regex, flags):
    if not isinstance(regex, _re_type):
        regex = re.compile(regex, flags)
    return regex, _make_getter(regex)


def re_all(regex, s, flags=0):
    return list(re_iter(regex, s, flags))

def re_find(regex, s, flags=0):
    return re_finder(regex, flags)(s)

def re_test(regex, s, flags=0):
    return re_tester(regex, flags)(s)


def re_finder(regex, flags=0):
    regex, getter = _prepare(regex, flags)
    return lambda s: iffy(getter)(regex.search(s))

def re_tester(regex, flags=0):
    return lambda s: bool(re.search(regex, s, flags))


### funcy funcs

EMPTY = object()

def identity(x):
    return x

def iffy(pred, action=EMPTY, default=identity):
    if action is EMPTY:
        return iffy(bool, pred)
    else:
        return lambda v: action(v)  if pred(v) else           \
                         default(v) if callable(default) else \
                         default
