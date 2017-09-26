#!/usr/bin/env python
# encoding: utf-8

"""
This module generates documentation for a TextMate bundle by parsing the .tmCommand files.
FIXME: The formatting is slightly messed up (underlined links, extra table header, etc.)
FIXME: Also parse bash/ruby/perl scripts for docstring equivalents
FIXME: List tab-triggers
"""

import os
import re
import json
from subprocess import Popen, PIPE


def parse_keycode(keycode):
    # a => A
    # A => ⇧A
    # ~ => ⌥
    # ^ => ⌃
    # @ => ⌘
    # $ ⌅ ⎋ ⇥
    # *
    mappings = {
        u'~':u'⌥',
        u'^':u'⌃',
        u'@':u'⌘',
        u'\x0A':u'↩',
        u'\x09':u'⇥',
        u'\x1B':u'⎋',
        u' ':u'␣'
    }
    printable = []
    shifted = False
    keycode = list(keycode)
    key = keycode.pop().decode('utf-8')
    key = mappings.get(key, key)
    printable.append(key.upper())
    if key >= 'A' and key <= 'Z':
        shifted = True

    while keycode:
        key = keycode.pop().decode('utf-8')
        printable.append(mappings.get(key, u'¿'))

    if shifted:
        printable.append(u'⇧')

    printable.reverse()

    return printable

def commandlist(cmd_dir):

    def json_from_plist(path):
        p = Popen(['plutil', '-convert', 'json', path, '-o', '-'], stdout=PIPE, stderr=PIPE)
        res, err = p.communicate()
        return json.loads(res) if not err else {}

    commands = [];
    for f in os.listdir(cmd_dir):
        path = os.path.join(cmd_dir, f)
        pl = json_from_plist(path)
        if not pl or pl.get('isDisabled', False):
            continue
        raw_combo = pl.get('keyEquivalent', '')
        name = pl.get('name', 'NONAME')
        docstring = extract_docstring(pl.get('command', ''))
        commands.append((raw_combo, name, docstring))

    return commands

def extract_docstring(string):
    LANG = r'^#!.+[/|\s+]([a-z]+)'
    match = re.match(LANG, string)
    if not match:
        return u''
    lang = match.group(1)
    if lang == 'python':
        return extract_python_docstring(string)
    elif lang in ['ruby', 'bash', 'sh']:
        return extract_comment_docstring(string)
    else:
        return u''

def extract_python_docstring(string):
    DOCSTRING = r'\s*#!.+?python.*?"""(.*?)"""'
    match = re.match(DOCSTRING, string, re.DOTALL)
    return match.group(1) if match else u''

def extract_comment_docstring(string):
    DOCSTRING = r'#!.+\n\n((?:\s*#.*\n)+)'
    match = re.match(DOCSTRING, string, re.MULTILINE)
    if not match:
        return u''
    lines = [line.lstrip('# \t') for line in match.group(1).split('\n')]
    return '\n'.join(lines)

def generate_keyboard_shortcut_docs(cmd_dir):
    # Auto-generate keyboard shortcut list
    print u'<table><tr><th>Keys</th><th>Command</th><th>Comment</th></tr>\n'.encode('utf-8')

    cmds = commandlist(cmd_dir)
    for (raw_combo, cmd_name, docstring) in cmds:
        if not raw_combo:
            continue
        combo = parse_keycode(raw_combo)
        help = u''.join(combo)
        if not help.strip():
            continue
        line = u'<tr><td>%s</td><td>%s</td><td>%s</td></tr>\n' % (help, cmd_name, docstring)

        ## NOTE!
        ## THIS is where we need to ENCODE (= turn a unicode string into bytes)
        ## AND specify the format to use (UTF-8) in the encoding process,
        ## the default encoding is ASCII which is SOO WRONG for unicode strings.
        print line.encode('utf-8')

    print u'</table>'.encode('utf-8')


