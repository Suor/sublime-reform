import sublime, sublime_plugin
from .funcy import *


class ScopesTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # print 1 , asd
        region = block_at(self.view, cursor_pos(self.view))
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



### Utils

def cursor_pos(view):
    return view.sel()[0].b

def set_selection(view, region):
    if iterable(region):
        region = list(region)

    view.sel().clear()
    if iterable(region):
        view.sel().add_all(region)
    else:
        view.sel().add(region)
    view.show(view.sel())
