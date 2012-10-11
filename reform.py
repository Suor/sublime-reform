# -*- coding: utf-8 -*-
import re
import sublime, sublime_plugin

# s = u"Привет, весёлые игрушки, мы пришли вас съесть! Бойтесь кровожадных нас, и прячтесь по углам, закрыв глазки!"

# s = u"Привет, весёлые игрушки, мы пришли вас съесть!"               \
#   + u"Бойтесь кровожадных нас, и прячтесь по углам, закрыв глазки!"

class ReformCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.view.insert(edit, 0, "Hello, World!")
