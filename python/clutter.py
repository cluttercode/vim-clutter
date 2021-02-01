from collections import namedtuple
from io import StringIO
import csv
import os
import pathlib
import re
import subprocess

import vim

outpattern = re.compile('^(.*):([0-9]+)\.([0-9]+)-([0-9]+)$')

Entry = namedtuple('Entry', ['name', 'path', 'line', 'col', 'endcol', 'attrs'])

def _run(opts=[]):
    row, col = vim.current.window.cursor

    fn = vim.current.buffer.name

    try:
        fn = pathlib.PurePath(vim.current.buffer.name).relative_to(os.getcwd())
    except ValueError:
        print(f'clutter: buffer must be at path relative to current directory')
        return None

    cmd = ["clutter", "-i", "", "r", "--loc", f'{fn}:{row}.{col + 1}']

    cmd.extend(opts)

    proc = subprocess.run(cmd, capture_output=True)

    stderr = proc.stderr.decode('utf-8').strip()

    if proc.returncode != 0:
        print(f'clutter: {stderr}')
        return None

    if stderr:
        print(f'clutter: {stderr}')

    stdout = proc.stdout.decode('utf-8')

    r = csv.reader(StringIO(stdout), delimiter=' ')

    vim.command('call setloclist(0, [], "f")')
    vim.command('call setloclist(0, [], "r", {"title": "clutter"})')

    matches = []

    for fs in r:
        if len(fs) < 2:
            print(f'warning: invalid output line: "{fs}"')
            continue

        name, loc = fs[0], fs[1]

        m = outpattern.match(loc)
        if not m:
            print(f'warning: invalid output line loc: "{loc}"')
            continue

        fn, lnum, col, endcol = m.groups()

        matches.append(Entry(name=name, path=fn, line=lnum, col=col, endcol=endcol, attrs=fs[2:]))

    return matches


def resolve1(which):
    matches = _run(opts=[f'-{which}'])

    if len(matches) != 1:
        _render_list(matches)
        return

    first = matches[0]

    vim.command(f'keepalt edit {first.path}')
    vim.command(f'{first.line}')
    vim.command(f'normal! {first.col}|')
    vim.command(f'normal! zz')


def resolve_list():
    _render_list(_run())


def _render_list(matches):
    if not matches:
        return

    vim.command('call setloclist(0, [], "f")')
    vim.command('call setloclist(0, [], "r", {"title": "clutter"})')

    for m in matches:
        vim.command(
            'call setloclist(0, [{"filename": "%s", "lnum": %s, "col": %s, "text": "%s %s"}], "a")' % (
                m.path, m.line, m.col, m.name, ' '.join(m.attrs),
            )
        )

    vim.command('lopen')
