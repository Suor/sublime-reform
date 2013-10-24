import re
import sublime, sublime_plugin

from .viewtools import region_before_pos, cursor_pos


SELECT_STACK = []


class SelectFuncCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        SELECT_STACK.append(list(self.view.sel()))

        region = self.func_region()
        if region:
            self.view.sel().clear()
            self.view.sel().add(region)
            self.view.show(region)

    def func_region(self):
        regions = python_find(self.view)
        current_region = region_before_pos(regions, cursor_pos(self.view))
        if current_region:
            return expand_indented(self.view, current_region)


class SelectDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if SELECT_STACK:
            regions = SELECT_STACK.pop()
            self.view.sel().clear()
            self.view.sel().add_all(regions)
            self.view.show(self.view.sel())


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


### Tools

def remove(cond, seq):
    return filter(complement(cond), seq)

def complement(func):
    return lambda *a, **kw: not func(*a, **kw)
