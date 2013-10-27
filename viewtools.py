"""
A collection of tools to deal with scopes and text in sublime view.
"""
import sublime


### Cursor and regions

def cursor_pos(view):
    return view.sel()[0].end()

def region_before_pos(regions, pos):
    return first(r for r in reversed(list(regions)) if r.begin() <= pos)

def line_start(view, pos=None):
    if pos is None:
        pos = cursor_pos(view)
    line = view.line(pos)
    return sublime.Region(line.begin(), pos)

def line_start_str(view):
    return view.substr(line_start(view))

def word_at(view, pos):
    if view.classify(pos) & sublime.CLASS_WORD_START:
        start = pos
    else:
        start = view.find_by_class(pos, False, sublime.CLASS_WORD_START)
    return view.word(start)

def word_after(view, pos):
    start = view.find_by_class(pos, True, sublime.CLASS_WORD_START)
    return view.word(start)


def swap_regions(view, edit, region1, region2):
    assert region1.b <= region2.a

    # hide selection before move and save shifted position to set it after
    sel = view.sel()
    regions = []
    for region in sel:
        if region1.contains(region):
            sel.subtract(region)
            regions.append(shifted_region(region, region2.b - region1.b))

    # swap text
    str1 = view.substr(region1)
    str2 = view.substr(region2)
    view.replace(edit, region2, str1)
    view.replace(edit, region1, str2)

    # set cursor position/selection to match moved regions
    sel.add_all(regions)


def shifted_region(region, shift):
    return sublime.Region(region.a + shift, region.b + shift)


# def word_at_pos(view, pos=None):
#     if pos is None:
#         pos = cursor_pos(view)
#     line = view.line()
#

### Selection

def set_selection(view, region):
    view.sel().clear()
    if iterable(region):
        view.sel().add_all(region)
    else:
        view.sel().add(region)
    view.show(view.sel())


### Scope

def scope_name(view):
    return view.scope_name(cursor_pos(view))

def parsed_scope(view):
    return parse_scope(scope_name(view))

def source(view):
    return first(vec[1] for vec in parsed_scope(view) if vec[0] == 'source')

def parse_scope(scope_name):
    return [name.split('.') for name in scope_name.split()]


### Funcy tools

def first(seq):
    return next(iter(seq), None)

from collections import Iterable

def isa(*types):
    return lambda x: isinstance(x, types)

iterable = isa(Iterable)
