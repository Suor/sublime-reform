import re
import sublime, sublime_plugin

class SelectFuncCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        region = self.func_region()
        if region:
            self.view.sel().clear()
            self.view.sel().add(region)
            self.view.show(region)


    def func_region(self):
        regions = python_find(self.view)
        current_region = select_current(self.view, regions)
        if current_region:
            return expand_indented(self.view, current_region)

    @property
    def syntax(self):
        syntax_file = self.view.settings().get('syntax')
        if not syntax_file:
            return None
        else:
            return re.search(r'(\w+)\.\w+$', syntax_file).group(1).lower()


# Find regions funcs
def find_functions(view):
    return view.find_by_selector('meta.function')

def python_find(view):
    is_lambda = lambda r: view.substr(r).startswith('lambda')
    return remove(is_lambda, find_functions(view))

# Expand funcs
def expand_indented(view, region):
    indented = view.indented_region(region.end() + 1)
    return region.cover(indented)

def select_current(view, regions):
    pos = view.sel()[0].begin()
    before_pos = lambda r: r.begin() <= pos
    return last(before_pos, regions)

### Tools

from itertools import ifilter

def first(cond, coll):
    return next(ifilter(cond, coll), None)

def last(cond, coll):
    return first(cond, reversed(coll))

def remove(cond, coll):
    return filter(complement(cond), coll)

def complement(func):
    return lambda *a, **kw: not func(*a, **kw)
