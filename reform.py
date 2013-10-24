# -*- coding: utf-8 -*-
import re
import sublime, sublime_plugin

# s = u"Привет, весёлые игрушки, мы пришли вас съесть! Бойтесь кровожадных нас, и прячтесь по углам, закрыв глазки!"

# s = u"Привет, весёлые игрушки, мы пришли вас съесть!"               \
#   + u"Бойтесь кровожадных нас, и прячтесь по углам, закрыв глазки!"

class ReformCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.insert(edit, 0, "Hello, World!")

# TODO
#  - Move functions up and down
#  - Break long lines
#  - Reform dicts (object literals) from one-line to multi-line and back
#  - Same for calls, calls with keyword arguments, array literals
#  - Break long strings, several variants including switching to multiline separators
#  - Align =, =>, :, \ and other punctuation
#  - Reform multiline list, set, dict comprehensions and generator expressions
#  - Reform for loop to list comprehension
#  - Switch brackets - parentheses - whatever
