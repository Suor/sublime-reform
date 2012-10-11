import re
import sublime, sublime_plugin

# TODO:
#   - don't spoil anything when out of scope
#   - preserve cursor position
#   - support css comments
#   - support css hacks
#   - text-wrapping variant

class CssReformCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        sel = self.view.sel()
        pos = sel[0].begin()

        # word = self.view.word(pos)
        # sublime.message_dialog(self.view.substr(word))
        # return

        scope = find_scope(self.view, pos)
        if not scope:
            return

        props_scope = step_in(scope)
        css = self.view.substr(props_scope)
        props = parse_props(css)

        if in_one_line(self.view, scope):
            indent = self.view.settings().get('tab_size', 4)
            new_css = column_props(props, indent)
        else:
            new_css = line_props(props)
        self.view.replace(edit, scope, new_css)

        sel.clear()
        sel.add(props_scope.begin())


def column_props(props, indent):
    template = ' ' * indent + '%s: %s;\n'
    css = ''.join(template % pair for pair in props)
    return '{\n%s}' % css

def line_props(props):
    css = '; '.join('%s: %s' % pair for pair in props)
    return '{%s}' % css

def parse_props(css):
    # NOTE: wastes anything unmatched, can miss some text,
    #       css comments also work weird
    """
    css     = (comment | rule | junk)*
    comment = "/*" .* "*/"
    rule    = name ":" values (";" | $ | "/*")
    name    = \S+
    values  = (comment | value)+
    value   = ???
    junk    = \S+
    """
    return re.findall(r'([\w-]+)\s*:\s*([^;}]+?)\s*(?:[;}]|$)', css)


def in_one_line(view, region):
    begin_rc = view.rowcol(region.begin())
    end_rc   = view.rowcol(region.end())
    return begin_rc[0] == end_rc[0]

def step_in(region):
    return sublime.Region(region.begin() + 1, region.end() - 1)


def find_scope(view, pos):
    # BUG: works weird when not in scope
    start = find_back(view, pos, '{')
    end = find_forward(view, pos, r'\}')
    if not start or not end:
        return None
    return sublime.Region(start, end + 1)

# NOTE: these two functions are asymmetric, watch out!
def find_forward(view, pos, pattern):
    result = view.find(pattern, pos)
    return result.begin() if result else None

def find_back(view, pos, s):
    to_pos = sublime.Region(0, pos)
    text = view.substr(to_pos)
    result_pos = text.rfind(s)
    return None if result_pos < 0 else result_pos


