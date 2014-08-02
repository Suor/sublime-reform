# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import re


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
    cursor_pos,
    map_selection, set_selection,

    word_at, word_after, word_before, swap_regions,
    region_before_pos, region_after_pos,
    invert_regions,

    expand_min_gap
)


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
        self.view.erase(edit, expand_min_gap(self.view, this_block))


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


class ExtractExprCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # Get expression
        sel = self.view.sel()[0]
        pos = sel.begin()
        expr = self.view.substr(sel)

        # Prepare new line
        line = self.view.line(pos)
        line_str = self.view.substr(line)
        prefix = re_find(r'^\s*', line_str)
        exracted_line = '{} = {}\n'.format(prefix, expr)

        # Modify text
        self.view.insert(edit, line.begin(), exracted_line)

        # Create cursor for name
        name_pos = line.begin() + len(prefix)
        self.view.sel().add(sublime.Region(name_pos, name_pos))


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
