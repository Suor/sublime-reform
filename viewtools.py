"""
A collection of tools to deal with scopes and text in sublime view.
"""
import sublime


### Cursor and selection

def cursor_pos(view):
    return view.sel()[0].b

def set_cursor(view, pos):
    set_selection(view, sublime.Region(pos, pos))

def set_selection(view, region):
    view.sel().clear()
    if iterable(region):
        view.sel().add_all(region)
    else:
        view.sel().add(region)
    view.show(view.sel())


### Regions

def full_region(view):
    return sublime.Region(0, view.size())

def region_before_pos(regions, pos):
    return first(r for r in reversed(list(regions)) if r.begin() <= pos)

def region_after_pos(regions, pos):
    return first(r for r in regions if r.begin() >= pos)

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

