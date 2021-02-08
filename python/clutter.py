from collections import namedtuple
from io import StringIO
import csv
import os
import pathlib
import re
import subprocess

import vim

# [# test #]
# [# test #]
# [# test #]

outpattern = re.compile('^(.*):([0-9]+)\.([0-9]+)-([0-9]+)$')

Entry = namedtuple('Entry', ['name', 'path', 'line', 'col', 'endcol', 'attrs'])

Loc = namedtuple('Loc', ['path', 'row', 'col'])


def _loc():
    row, col = vim.current.window.cursor
    path = vim.current.buffer.name

    try:
        path = str(pathlib.PurePath(path).relative_to(os.getcwd()))
    except ValueError:
        print(f'clutter: buffer must be at path relative to current directory')
        return None

    return Loc(path=path, row=row, col=col)


def _run(opts=[]):
    cmd = ["clutter", "-i", ""] + opts

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

        lnum, col, endcol = int(lnum), int(col), int(endcol)

        matches.append(Entry(name=name, path=fn, line=lnum, col=col, endcol=endcol, attrs=fs[2:]))

    return matches


def _resolve_opts(loc):
    return ["r", "--loc", f'{loc.path}:{loc.row}.{loc.col + 1}']


def resolve1(which):
    loc = _loc()
    if not loc:
        return

    matches = _run(_resolve_opts(loc) + [f'-{which}', '-c'])

    if not matches:
        return

    if len(matches) != 1:
        _render_list(matches, loc)
        return

    first = matches[0]

    try:
        vim.command(f'keepalt edit {first.path}')
    except vim.error as e:
        # Check for ATTENTION (maybe opening a file that is already opened).
        if e.args and e.args[0].find(':E325:') == -1:
            raise

    vim.command(f'{first.line}')
    vim.command(f'normal! {first.col}|')
    vim.command(f'normal! zz')


def resolve_list():
    loc = _loc()
    if not loc:
        return

    _render_list(_run(_resolve_opts(loc)), loc)


def search(mode, args):
    cmd = ['s']

    if mode:
        cmd.append(f'-{mode}')

    cmd.extend(args)

    _render_list(_run(cmd))


def _render_list(matches, loc=None):
    if not matches:
        print('clutter: no matches')
        return

    vim.command('call setloclist(0, [], "f")')
    vim.command('call setloclist(0, [], "r", {"title": "clutter"})')

    i = 1
    for m in matches:
        vim.command(
            'call setloclist(0, [{"filename": "%s", "lnum": %s, "col": %s, "text": "%s %s"}], "a")' % (
                m.path, m.line, m.col, m.name, ' '.join(m.attrs),
            )
        )

        if loc and m.path == loc.path and m.line == loc.row and m.col <= loc.col <= m.endcol:
            vim.command('call setloclist(0, [], "a", {"idx": %d})' % i)

        i += 1

    vim.command('lopen')
