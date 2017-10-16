import sublime, sublime_plugin
ST3 = sublime.version() >= '3000'

from functools import partial, reduce
from itertools import takewhile

try:
    from .funcy import *
    from .viewtools import *
except ValueError: # HACK: for ST2 compatability
    from funcy import *
    from viewtools import *


class TestCommandCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass


class ScopesTestCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print("test")
        # print(list_defs(self.view))

        # scopes = [_expand_def(view, adef) for adef in list_defs(view)]
        scopes = list_defs(self.view)
        set_selection(self.view, scopes)
        return

        pos = cursor_pos(self.view)
        scope = region_b(scopes, pos)
        print(scope)
        scope = _expand_def(self.view, scope)
        set_selection(self.view, [scope])
        # # from .viewtools import word_f, cursor_pos
        # # set_selection(self.view, word_f(self.view, cursor_pos(self.view)))
        # # print(self.view.find_by_selector('meta.function'))
        # # block = scope_up(self.view, self.view.sel()[0])
        # # set_selection(self.view, block)
        # # set_selection(self.view, list_defs(self.view))
        # # ls = self.view.find_by_class(pos, False, sublime.CLASS_LINE_START)
        # ls = newline_f(self.view, pos)
        # set_selection(self.view, ls)


class SmartUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        regions = order_regions(list_defs(self.view) + list_blocks(self.view))
        map_selection(self.view, partial(smart_up, regions))

class SmartDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        regions = order_regions(list_defs(self.view) + list_blocks(self.view))
        map_selection(self.view, partial(smart_down, regions))

class DefUpCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        # TODO: jump by selectors in css/less/...
        regions = list_defs(self.view) or list_blocks(self.view)
        map_selection(self.view, partial(smart_up, regions))

class DefDownCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        regions = list_defs(self.view) or list_blocks(self.view)
        map_selection(self.view, partial(smart_down, regions))

def smart_up(regions, current):
    target = region_b(regions, current.begin() - 1) or last(regions)
    return target.begin()

def smart_down(regions, current):
    target = region_f(regions, current.end()) or first(regions)
    return target.begin()


class DeleteBlockCommand(sublime_plugin.TextCommand):
     def run(self, edit):
        pos = cursor_pos(self.view)
        comments_block = comments_block_at(self.view, pos)
        # Skip one line comments
        if comments_block and self.view.substr(comments_block).count('\n') == 1:
            comments_block = None
        block = comments_block or block_at(self.view, pos)

        ex_block = expand_min_gap(self.view, block)
        new_pos = ex_block.begin() - 1 if ex_block.begin() < block.begin() else ex_block.end()
        set_cursor(self.view, new_pos)
        self.view.erase(edit, ex_block)


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
        # TODO: make this not include decorators in python
        region = self.view.sel()[-1]
        if region.empty():
            region = word_at(self.view, region.a)
            if not region:
                return

        words = get_words(self.view, region)

        # filter by scope
        scope = scope_at(self.view, region.end()) or block_at(self.view, region.end())
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


class InlineExprCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()[0]
        pos = sel.begin()
        line = self.view.line(pos)
        line_str = self.view.substr(line)

        try:
            var, expr = re_find(r'^\s*(\w+)\s*=\s*(.*)$', line_str)
        except TypeError:
            return
        scope = scope_at(self.view, pos) or sublime.Region(0, self.view.size())
        var_regions = self.view.find_all(r'\b%s\b' % var)
        var_regions = [r for r in var_regions if scope.contains(r)]
        for r in reversed(var_regions):
            self.view.replace(edit, r, expr)
        self.view.erase(edit, self.view.full_line(pos))


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

        map_selection(self.view, partial(smart_region_up, self.view))

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


def smart_region_up(view, region):
    comments_block = comments_block_at(view, region.b)
    block = smart_block_at(view, region.begin())
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
    this_line = first((i, r) for i, r in enumerate(clines) if r.contains(pos) and r.b != pos)
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


def smart_block_at(view, pos):
    lang = source(view)
    block = block_at(view, pos)

    # Close non-pairing curlies
    curlies = count_curlies(view, block)
    if curlies > 0:
        curly = find_closing_curly(view, block.end(), count=curlies)
        if curly is not None:
            return block.cover(view.full_line(curly))
    elif curlies < 0:
        curly = find_opening_curly(view, block.begin(), count=curlies)
        if curly is not None:
            return block.cover(view.full_line(curly))
    return block


def list_func_defs(view):
    lang = source(view)
    if lang in ('cs', 'java'):
        return view.find_by_selector('meta.method.identifier')

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
    lang = source(view)
    if lang in ('cs', 'java'):
        return view.find_by_selector('meta.class.identifier')
    else:
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
    scopes = scopes_up(view, pos)
    return first(s for s in scopes if s.contains(pos))

def scopes_up(view, pos):
    for scope, upper in with_next(_scopes_up(view, pos)):
        yield scope
        if upper and not upper.contains(scope):
            continue

def _scopes_up(view, pos):
    scopes = [_expand_def(view, adef) for adef in list_defs(view)]

    scope = region_b(scopes, pos)
    while scope:
        yield scope
        scope = region_b(scopes, scope.begin() - 1)


def _expand_def(view, adef):
    lang = source(view, adef.begin())

    if lang == 'python':
        next_line = newline_f(view, adef.end())
        adef = adef.cover(view.indented_region(next_line))
        prefix = re_find(r'^[ \t]*', view.substr(view.line(adef.begin())))
        while True:
            p = line_b_begin(view, adef.begin())
            if p is None:
                break
            line_b_str = view.substr(view.line(p))
            if line_b_str.startswith(prefix) and re_test(r'meta.(annotation|\w+.decorator)',
                    scope_name(view, p + len(prefix))):
                adef = adef.cover(sublime.Region(p, p))
            else:
                break
        return adef
    elif lang in ('js', 'cs', 'java'):
        # Extend to matching bracket
        start_bracket = view.find(r'{', adef.end(), sublime.LITERAL)
        end_bracket = find_closing_curly(view, start_bracket.b)
        adef = adef.cover(view.full_line(end_bracket))

        # Match , or ; in case it's an expression
        if lang == 'js':
            punct = view.find(r'\s*[,;]', adef.end())
            if punct and punct.a == adef.b:
                adef = adef.cover(punct)
        else:
            adef = adef.cover(view.line(adef.begin()))

        return adef
    else:
        # Heuristics based on indentation for all other languages
        next_line = newline_f(view, adef.end())
        indented = view.indented_region(next_line)
        last_line = view.line(indented.end())
        return adef.cover(last_line)
