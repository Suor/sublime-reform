import sublime, sublime_plugin
ST3 = sublime.version() >= '3000'

from functools import partial

try:
    from .funcy import *
    from .viewtools import *
except ValueError: # HACK: for ST2 compatability
    from funcy import *
    from viewtools import *


class ScopesTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print("test")
        # from .viewtools import word_f, cursor_pos
        # set_selection(self.view, word_f(self.view, cursor_pos(self.view)))


class SmartUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # TODO: jump by selectors in css/less/...
        regions = list_defs(self.view)

        def smart_up(pos):
            target = region_b(regions, pos.begin() - 1) or last(regions)
            return target.begin()

        map_selection(self.view, smart_up)


class SmartDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        regions = list_defs(self.view)

        def smart_down(region):
            target = region_f(regions, region.end()) or first(regions)
            return target.begin()

        map_selection(self.view, smart_down)


class SelectScopeUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        map_selection(self.view, partial(scope_up, self.view))

class SelectFuncCommand(SelectScopeUpCommand):
    pass


def list_func_defs(view):
    lang = source(view)
    # Sublime doesn't think "function() {}" (mind no space) is a func definition.
    # It however thinks constructor and prototype have something to do with it.
    if lang == 'js':
        funcs = view.find_all(r'function')
        is_junk = lambda r: is_escaped(view, r.a)
        return lremove(is_junk, funcs)

    funcs = view.find_by_selector('meta.function')
    if lang == 'python':
        is_junk = lambda r: re_test('^(lambda|\s*\@)', view.substr(r))
        funcs = lremove(is_junk, funcs)
    return funcs

def list_class_defs(view):
    return view.find_by_selector('meta.class')

def list_defs(view):
    if view.scope_name(0).startswith('text.'):
        # plain text/markdown/rst
        return list_blocks(view)
    else:
        # programming languages
        funcs = list_func_defs(view)
        if source(view) == 'js':
            return funcs
        classes = list_class_defs(view)
        return order_regions(funcs + classes)


def scope_up(view, region):
    scopes = list(scopes_up(view, region.end()))
    if not scopes:
        return region
    expansion = first(s for s in scopes if s != region and s.contains(region))
    if expansion:
        return expansion
    if region.empty():
        return first(scopes)
    else:
        return region

def scope_at(view, pos):
    scopes = list(scopes_up(view, pos))
    return first(s for s in scopes if s.contains(pos)) or first(scopes)

def scopes_up(view, pos):
    for scope, upper in with_next(_scopes_up(view, pos)):
        yield scope
        if upper and not upper.contains(scope):
            continue

def _scopes_up(view, pos):
    defs = list_defs(view)
    adef = region_b(defs, pos)

    while adef:
        scope = _expand_def(view, adef)
        yield scope
        adef = region_b(defs, adef.begin() - 1)

def _expand_def(view, adef):
    lang = source(view, adef.begin())

    if lang == 'python':
        next_line = newline_f(view, adef.end())
        return adef.cover(view.indented_region(next_line))
    elif lang == 'js':
        # Functions in javascript are often declared in expression manner,
        # we add function binding to prototype or object property as part of declaration.
        ls = view.substr(line_start(view, adef.begin()))
        prefix = re_find(r'\s*(?:\w+\s*:|[\w.]+\s*=)\s*$', ls)
        if prefix:
            adef.a -= len(prefix)

        # Extend to matching bracket
        start_bracket = view.find(r'{', adef.end(), sublime.LITERAL)
        end_bracket = find_matching_bracket(view, start_bracket)
        return adef.cover(end_bracket)
    else:
        # Heuristics based on indentation for all other languages
        next_line = newline_f(view, adef.end())
        indented = view.indented_region(next_line)
        last_line = view.line(indented.end())
        return adef.cover(last_line)


def find_matching_bracket(view, bracket):
    count = 1
    while count > 0 and bracket.a != -1:
        bracket = view.find(r'[{}]', bracket.b)
        if not is_escaped(view, bracket.a):
            if view.substr(bracket) == '{':
                count += 1
            else:
                count -= 1
    return bracket

def is_escaped(view, pos):
    return any(s[0] in ('comment', 'string') for s in parsed_scope(view, pos))


if ST3:
    def newline_f(view, pos):
        return view.find_by_class(pos, True, sublime.CLASS_LINE_START)
else:
    def newline_f(view, pos):
        region = view.find(r'\n', pos + 1)
        return region.end()
