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
        regions = list_defs(self.view) or list_blocks(self.view)

        def smart_up(pos):
            target = region_b(regions, pos.begin() - 1) or last(regions)
            return target.begin()

        map_selection(self.view, smart_up)


class SmartDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        regions = list_defs(self.view) or list_blocks(self.view)

        def smart_down(region):
            target = region_f(regions, region.end()) or first(regions)
            return target.begin()

        map_selection(self.view, smart_down)


class ExpandNextWordCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        region = self.view.sel()[-1]
        if region.empty():
            region = word_at(self.view, region.a)
            if region:
                self.view.sel().add(region)
                return

        words = get_words(self.view, region)

        # filter out already selected words
        begins = set(r.begin() for r in self.view.sel())
        words = [w for w in words if w.begin() not in begins]

        next_word = first(r for r in words if r.begin() > region.end()) or first(words)
        if next_word:
            self.view.sel().add(next_word)
            self.view.show(next_word)

class SelectScopeWordsCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        region = self.view.sel()[-1]
        if region.empty():
            region = word_at(self.view, region.a)
            if not region:
                return

        words = get_words(self.view, region)

        # filter by scope
        scope = scope_at(self.view, region.end())
        words = [w for w in words if scope.contains(w)]

        set_selection(self.view, words)

def get_words(view, region):
    word = view.substr(region)
    words = view.find_all(r'\b%s\b' % word)

    # filter out words in strings and comments
    allow_escaped = any(is_escaped(view, r.begin()) for r in view.sel())
    if not allow_escaped:
        words = [w for w in words if not is_escaped(view, w.a)]

    return words


class SelectScopeUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if not hasattr(self.view, '_selection_stack'):
            self.view._selection_stack = []

        # Start stack afresh if nothing is selected
        sel = list(self.view.sel())
        if all(r.empty() for r in sel):
            self.view._selection_stack = []

        # Save current selection
        self.view._selection_stack.append(sel)

        map_selection(self.view, partial(smart_block_at, self.view))

        # If nothing changed remove dup from stack
        if self.view._selection_stack[-1] == self.view.sel():
            self.view._selection_stack.pop()

# NOTE: this is deprecated
class SelectFuncCommand(SelectScopeUpCommand):
    pass

class SelectScopeDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if getattr(self.view, '_selection_stack'):
            set_selection(self.view, self.view._selection_stack.pop())
            self.view.show(self.view.sel())


def smart_block_at(view, region):
    comments_block = comments_block_at(view, region.b)
    block = block_at(view, region.b)
    scope = scope_up(view, region)

    if comments_block and not region.contains(comments_block):
        return comments_block
    elif block and not region.contains(block) and (not scope or scope.a < block.a):
        return block
    else:
        return scope or region

def comments_block_at(view, pos):
    def grab_empty_line_start(region):
        line_start = view.line(region).a
        space = view.find(r'[ \t]+', line_start)
        if space and space.b == region.a:
            return region.cover(space)
        else:
            return region

    clines = list(map(grab_empty_line_start, view.find_by_selector('comment')))

    pos = cursor_pos(view)
    this_line = first((i, r) for i, r in enumerate(clines) if r.contains(pos))
    if this_line:
        i, block = this_line
        for r in clines[i+1:]:
            if r.a == block.b:
                block = block.cover(r)
            else:
                break
        for r in reversed(clines[:i]):
            if r.b == block.a:
                block = block.cover(r)
            else:
                break
        return block


def list_func_defs(view):
    lang = source(view)
    # Sublime doesn't think "function() {}" (mind no space) is a func definition.
    # It however thinks constructor and prototype have something to do with it.
    if lang == 'js':
        # Functions in javascript are often declared in expression manner,
        # we add function binding to prototype or object property as part of declaration.
        funcs = view.find_all(r'([\t ]*(?:\w+ *:|(?:var +)?[\w.]+ *=) *)?function')
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
    funcs = list_func_defs(view)
    if source(view) == 'js':
        return funcs
    classes = list_class_defs(view)
    return order_regions(funcs + classes)


def scope_up(view, region):
    scopes = list(scopes_up(view, region.end()))
    expansion = first(s for s in scopes if s != region and s.contains(region))
    if expansion:
        return expansion
    if region.empty():
        return first(scopes)

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
        # Extend to matching bracket
        start_bracket = view.find(r'{', adef.end(), sublime.LITERAL)
        end_bracket = find_matching_bracket(view, start_bracket)
        adef = adef.cover(end_bracket)

        # Match , or ; in case it's an expression
        punct = view.find(r'\s*[,;]', adef.end())
        if punct and punct.a == adef.b:
            adef = adef.cover(punct)

        return adef
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

def is_comment(view, pos):
    return any(s[0] == 'comment' for s in parsed_scope(view, pos))


if ST3:
    def newline_f(view, pos):
        return view.find_by_class(pos, True, sublime.CLASS_LINE_START)
else:
    def newline_f(view, pos):
        region = view.find(r'\n', pos + 1)
        return region.end()
