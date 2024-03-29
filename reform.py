# -*- coding: utf-8 -*-
import sublime, sublime_plugin
import re

try:
    from .funcy import *
    from .viewtools import (
        cursor_pos, list_cursors, set_cursor,
        set_selection,
        source,

        word_at, word_b, word_f,
        block_at, list_blocks,
        region_at, region_b, region_f,
        swap_regions,
        expand_min_gap,
    )
except ValueError: # HACK: for ST2 compatability
    from funcy import *
    from viewtools import (
        cursor_pos, list_cursors, set_cursor,
        set_selection,
        source,

        word_at, word_b, word_f,
        block_at, list_blocks,
        region_at, region_b, region_f,
        swap_regions,
        expand_min_gap,
    )


### Word commands

# TODO: alter word boundaries on context,
#       e.g. if it's a css class then "-"" should be word symbol
class FindWordDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pos = cursor_pos(self.view)
        region = word_at(self.view, pos)
        if not region:
            return
        word = self.view.substr(region)

        all_regions = self.view.find_all(r'\b%s\b' % word)
        next_region = region_f(all_regions, region.end()) or first(all_regions)

        set_cursor(self.view, next_region.begin())


class FindWordUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pos = cursor_pos(self.view)
        region = word_at(self.view, pos)
        if not region:
            return
        word = self.view.substr(region)

        all_regions = self.view.find_all(r'\b%s\b' % word)
        next_region = region_b(all_regions, region.begin() - 1) or last(all_regions)

        set_cursor(self.view, next_region.begin())


class MoveWordRightCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # We go from right to left to correctly handle overlapping regions
        for pos in reversed(list_cursors(self.view)):
            word1 = word_at(self.view, pos)
            word2 = word_f(self.view, pos)
            swap_regions(self.view, edit, word1, word2)


class MoveWordLeftCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for pos in list_cursors(self.view):
            word1 = word_at(self.view, pos)
            word2 = word_b(self.view, word1.begin())
            swap_regions(self.view, edit, word2, word1)


### Block commands

class MoveBlockUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        blocks = list_blocks(self.view)
        this_block = region_at(blocks, cursor_pos(self.view))
        if not this_block:
            return
        prev_block = region_b(blocks, this_block.begin() - 1)
        if not prev_block:
            return

        swap_regions(self.view, edit, prev_block, this_block)
        self.view.show(prev_block)


class MoveBlockDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        blocks = list_blocks(self.view)
        this_block = region_at(blocks, cursor_pos(self.view))
        if not this_block:
            return
        next_block = region_f(blocks, this_block.end())
        if not next_block:
            return

        swap_regions(self.view, edit, this_block, next_block)
        self.view.show(next_block)


### Other commands

class EncallCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        new_sels = []
        for s in self.view.sel():
            line = self.view.line(s.b)
            line_str = self.view.substr(line)
            m = match_around(r'[\w\.]+', line_str, s.b - line.begin())
            if m:
                r = sublime.Region(m[0] + line.begin(), m[1] + line.begin())
                if self.view.substr(r.end()) == '(':
                    closing = find_matching_paren(self.view, sublime.Region(r.end(), r.end()+1))
                    r = r.cover(closing)
                s = self.view.substr(r)
                self.view.replace(edit, r, '(%s)' % s)
                new_sels.append(r.begin())

        set_selection(self.view, new_sels)

from .scopes import is_escaped

def find_matching_paren(view, paren):
    count = 1
    while count > 0 and paren.a != -1:
        paren = view.find(r'[()]', paren.b)
        if not is_escaped(view, paren.a):
            if view.substr(paren) == '(':
                count += 1
            else:
                count -= 1
    return paren


class ExtractExprCommand(sublime_plugin.TextCommand):
    TEMPLATES = {
        'js': ('let  = {0};\n', 4),
        'php': (' = {0};\n', 0),
        'nut': ('local  = {0};\n', 6),
    }
    DEFAULT = (' = {0}\n', 0)

    def run(self, edit):
        # Get expression
        sel = self.view.sel()[0]
        pos = sel.begin()
        expr = self.view.substr(sel)

        # Prepare new line
        line = self.view.line(pos)
        line_str = self.view.substr(line)
        prefix = re_find(r'^\s*', line_str)
        template, cursor_shift = self.TEMPLATES.get(source(self.view, pos), self.DEFAULT)
        exracted_line = prefix + template.format(expr)

        # Modify text
        self.view.insert(edit, line.begin(), exracted_line)

        # Create cursor for name
        name_pos = line.begin() + len(prefix) + cursor_shift
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
