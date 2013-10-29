# -*- coding: utf-8 -*-
import re
import sublime, sublime_plugin

from .viewtools import set_selection, cursor_pos, word_at, word_after, swap_regions

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


class ReformTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()
        for region in sel:
            sel.subtract(region)
            sel.add(sublime.Region(region.a + 1, region.b + 1))

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
