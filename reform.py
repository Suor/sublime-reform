# -*- coding: utf-8 -*-
import re
import sublime, sublime_plugin

from .viewtools import (
    set_selection, cursor_pos, set_cursor,
    word_at, word_after, word_before, swap_regions,
    region_before_pos, region_after_pos,
    invert_regions
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

class MoveBlockDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        empty_lines = self.view.find_all(r'^\s*\n')
        blocks = invert_regions(self.view, empty_lines)

        pos = cursor_pos(self.view)
        this_block = region_before_pos(blocks, pos)
        next_block = region_after_pos(blocks, this_block.end())
        swap_regions(self.view, edit, this_block, next_block)


class ReformTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        empty_lines = self.view.find_all(r'^\s*\n')
        blocks = invert_regions(self.view, empty_lines)

        pos = cursor_pos(self.view)
        this_block = region_before_pos(blocks, pos)
        next_block = region_after_pos(blocks, this_block.end())
        # set_selection(self.view, [this_block, next_block])
        swap_regions(self.view, edit, this_block, next_block)

# TODO
#  - Move functions up and down
#  - Break long lines
#  - Reform dicts (object literals) from one-line to multi-line and back
#  - Same for calls, calls with keyword arguments, array literals
#  - Break long strings, several variants including switching to multiline separators
#  - Align =, =>, :, \ and other punctuation
#  - Reform multiline list, set, dict comprehensions and generator expressions
#  - Reform for loop to list comprehension
#  - Switch brackets - parentheses - whatever
#
#  - Move words, code blocks and such
