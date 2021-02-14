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


def check():
    def err(s):
        print(f'clutter: {s}')
        print("to reinstall or upgrade clutter, see https://github.com/cluttercode/clutter#installation.")

    try:
        proc = subprocess.run(["clutter", "version"], capture_output=True, text=True)
    except FileNotFoundError:
        err("clutter is not in $PATH.")
        return

    if proc.returncode != 0:
        err("something went wrong with clutter.")
        return

    lines = proc.stdout.split(" ")
    if not lines:
        err("clutter gave out weird version output.")

    ver = lines[0].split(".")
    if len(ver) != 3:
        err("clutter gave out weird version output.")

    if ver[0].startswith('v') or (int(ver[0]) == 0 and int(ver[1]) < 2):
        err("incompatible clutter version - at least 0.2.0 required.")


def _rel_path(path):
    return str(pathlib.PurePath(path).relative_to(os.getcwd()))


def _loc():
    row, col = vim.current.window.cursor
    path = vim.current.buffer.name

    try:
        path = _rel_path(path)
    except ValueError:
        print(f'clutter: buffer must be at path relative to current directory')
        return None

    return Loc(path=path, row=row, col=col)


def _run(opts=[], buffer_stdin=False):
    cmd = ["clutter", "-i", ""] + opts

    stdin = None
    if buffer_stdin:
        stdin = ''.join([f'{l}\n' for l in vim.current.buffer[:]])

    proc = subprocess.run(cmd, capture_output=True, text=True, input=stdin)

    stderr = proc.stderr.strip()

    if proc.returncode != 0:
        print(f'clutter: {stderr}')
        return None

    if stderr:
        print(f'clutter: {stderr}')

    stdout = proc.stdout

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
    return ["r", "--loc", f'{loc.path}:{loc.row}.{loc.col + 1}', '--loc-from-stdin']


def resolve1(which):
    loc = _loc()
    if not loc:
        return

    matches = _run(_resolve_opts(loc) + [f'-{which}', '-c'], True)

    if not matches:
        return

    if len(matches) != 1:
        _render_list(matches, loc)
        return

    first = matches[0]

    if _rel_path(vim.current.buffer.name) != first.path:
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

    _render_list(_run(_resolve_opts(loc), True), loc)


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
