# Reform

This thing enables you to move through and reform your code like magic.
At least it aims to do it :)

Here is a list of supported commands:

Command           | Key binding<sup>*</sup> | Description
----------------- | ------------ | ---------------------------------------------------------------
find_word_up      | ctrl+up      | Jump to previous occurrence of a word at cursor
find_word_down    | ctrl+down    | Jump to next occurrence of a word at cursor
smart_down        | alt+down     | Jump to next function or class declaration
smart_up          | alt+up       | Jump to previous function or class declaration
move_word_right   | ctrl+alt+/   | Swap word at cursor with a next one
move_word_left    | ctrl+alt+.   | Swap word at cursor with a previous one
select_block      | --           | Select block<sup>1</sup> at cursor
move_block_up     | ctrl+alt+;   | Swap block with a previous one
move_block_down   | ctrl+alt+'   | Swap block with a next one
delete_block      | ctrl+alt+d   | Delete block at cursor with appropriate empty lines
select_scope_up   | ctrl+shift+; | Select function/class at cursor, select enclosing one on next hit<sup>2</sup>
extract_expr      | alt+enter    | Extract selected expression into an assignment<sup>3</sup>


<sup>*</sup> Current key bindings are very experimental, especially on OS X. <br>
<sup>1</sup> Block is a blob of text surrounded with empty lines. <br>
<sup>2</sup> Works for python, js. Tries to work for other languages. <br>
<sup>3</sup> Works for python, js, ruby, php (and any languages with no keyword to define var).<br>


## Installation

- [Install Package Control](https://sublime.wbond.net/installation).
- Bring up the Command Palette with Ctrl+Shift+p (Cmd+Shift+p on OS X).
- Select "Package Control: Install Package" (it'll take a few seconds).
- Select or type in "Reform" when the list appears.


## TODO

I have plans. Here is a list if you want to help and looking where to start:

- Move functions up and down.
- Select scopes, functions and classes.
- Like Ctrl+D/Alt-F3 but respect word boundaries, case, scopes.
- Select all words withing scope, all references to same name.
- Break long lines.
- Break long strings, several variants including switching to multiline separators.
- Reform dicts (object literals) from one-line to multi-line and back.
- Same for calls, calls with keyword arguments, array literals.
- Reform multiline list, set, dict comprehensions and generator expressions.
- Align =, =>, :, \ and other punctuation
- Switch brackets, parentheses, whatever.
- Move blocks respecting functions.

Also, support for more programming languages for language-dependent commands will help.
