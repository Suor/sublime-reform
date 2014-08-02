"""
A collection of tools to deal with scopes and text in sublime view.
"""
import sublime
from .funcy import *


### Cursor and selection

def cursor_pos(view):
    return view.sel()[0].b

def set_cursor(view, pos):
    if iterable(pos):
        regions = [sublime.Region(p, p) for p in pos]
    else:
        regions = sublime.Region(pos, pos)
    set_selection(view, regions)

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


### Regions

def full_region(view):
    return sublime.Region(0, view.size())

def region_up(regions, pos):
    return first(r for r in reversed(list(regions)) if r.end() < pos)

def region_down(regions, pos):
    return first(r for r in regions if r.begin() > pos)

def region_before_pos(regions, pos):
    return first(r for r in reversed(list(regions)) if r.begin() <= pos)

def region_after_pos(regions, pos):
    return first(r for r in regions if r.begin() >= pos)


def order_regions(regions):
    order = lambda r: (r.begin(), r.end())
    return sorted(regions, key=order)

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


def word_at(view, pos):
    if view.classify(pos) & sublime.CLASS_WORD_START:
        start = pos
    else:
        start = view.find_by_class(pos, False, sublime.CLASS_WORD_START)
    return view.word(start)

def word_after(view, pos):
    start = view.find_by_class(pos, True, sublime.CLASS_WORD_START)
    return view.word(start)

def word_before(view, pos):
    end = view.find_by_class(pos, False, sublime.CLASS_WORD_END)
    return view.word(end)


def swap_regions(view, edit, region1, region2):
    assert region1.b <= region2.a

    # hide selection before move and save shifted position to set it after
    sel = view.sel()
    regions = []
    for region in sel:
        if region1.contains(region):
            sel.subtract(region)
            regions.append(shifted_region(region, region2.b - region1.b))
        elif region2.contains(region):
            sel.subtract(region)
            regions.append(shifted_region(region, region1.a - region2.a))

    # swap text
    str1 = view.substr(region1)
    str2 = view.substr(region2)
    view.replace(edit, region2, str1)
    view.replace(edit, region1, str2)

    # set cursor position/selection to match moved regions
    sel.add_all(regions)

def shifted_region(region, shift):
    return sublime.Region(region.a + shift, region.b + shift)


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


### Smarts


def expand_min_gap(view, region):
    """
    Expands region so that it will cover minimum gap of empty lines around it.
    """
    empty_lines = view.find_all(r'^\s*\n')
    empty_neighbours = [r for r in empty_lines
                          if r.end() == region.begin() or r.begin() == region.end()]

    if not empty_neighbours:
        return region
    elif len(empty_neighbours) == 1:
        return region.cover(empty_neighbours[0])
    else:
        min_gap = min(empty_neighbours, key=lambda r: view.substr(r).count('\n'))
        return region.cover(min_gap)
