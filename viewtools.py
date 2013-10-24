"""
A collection of tools to deal with scopes and text in sublime view.
"""
import sublime


### Cursor and regions

def cursor_pos(view):
    return view.sel()[0].begin()

def region_before_pos(regions, pos):
    return first(r for r in reversed(list(regions)) if r.begin() <= pos)

def line_start(view, pos=None):
    if pos is None:
        pos = cursor_pos(view)
    line = view.line(pos)
    return sublime.Region(line.begin(), pos)

def line_start_str(view):
    return view.substr(line_start(view))


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
