# Reform

[![Join the chat at https://gitter.im/Suor/sublime-reform](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Suor/sublime-reform?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

This thing enables you to move through and reform your code like magic.
At least it aims to do it :)

Here is a list of supported commands:

Command           | Key<sup>*</sup> | Description
----------------- | ------------ | ---------------------------------------------------------------
find_word_up      | ctrl+up      | Jump to previous occurrence of a word at cursor
find_word_down    | ctrl+down    | Jump to next occurrence of a word at cursor
def_up            | alt+up       | Jump to previous function or class declaration
def_down          | alt+down     | Jump to next function or class declaration
smart_up          | alt+[        | Jump to previous declaration or block<sup>2</sup>
smart_down        | alt+]        | Jump to next declaration or block<sup>2</sup>
move_word_right   | ctrl+alt+/   | Swap word at cursor with a next one
move_word_left    | ctrl+alt+.   | Swap word at cursor with a previous one
move_block_up     | ctrl+alt+;   | Swap block with a previous one
move_block_down   | ctrl+alt+'   | Swap block with a next one
expand_next_word  | alt+d        | Expand selection to next word matching one at cursor<sup>1</sup>
select_scope_words| alt+shift+d  | Select words in function scope matching word at cursor<sup>1,3</sup>
select_scope_up   | ctrl+shift+; | Select block<sup>2</sup>/function/class at cursor, select enclosing one on next hit<sup>3</sup>
select_scope_down | ctrl+shift+' | Undo last select_scope_up
delete_block      | ctrl+alt+d   | Delete block at cursor with appropriate adjusting empty lines
extract_expr      | alt+enter    | Extract selected expression into an assignment<sup>4</sup>
inline_expr       | alt+=        | Inline variable defined on line at cursor


<sup>*</sup> Current key bindings are very experimental, especially on OS X. <br>
<sup>1</sup> Matches only whole words, case-sensitive, comments and strings are skipped. <br>
<sup>2</sup> Block is a adjacent commented lines or a blob of text surrounded with empty lines. <br>
<sup>3</sup> Works for python, js, plain text. Tries to work for other languages. <br>
<sup>4</sup> Works for python, js, ruby, php (and any languages with no keyword to define var).<br>


## Installation

- [Install Package Control](https://sublime.wbond.net/installation).
- Bring up the Command Palette with Ctrl+Shift+p (Cmd+Shift+p on OS X).
- Select "Package Control: Install Package" (it'll take a few seconds).
- Select or type in "Reform" when the list appears.


## TODO

I have plans. Here is a list if you want to help and looking where to start:

- Move functions up and down.
- Better select words in scope: expand to next scope on subsequent hit, autodetect name scope.
- Break long lines.
- Break long strings, several variants including switching to multiline separators.
- Reform dicts (object literals) from one-line to multi-line and back.
- Same for calls, calls with keyword arguments, array literals.
- Reform multiline list, set, dict comprehensions and generator expressions.
- Align =, =>, :, \ and other punctuation
- Switch brackets, parentheses, whatever.
- Move blocks respecting functions.

Also, support for more programming languages for language-dependent commands will help.
