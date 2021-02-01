from io import StringIO
import csv
import os
import pathlib
import re
import subprocess

import vim

csv.register_dialect('clutter', delimiter=' ')

outpattern = re.compile('^(.*):([0-9]+)\.([0-9]+)-[0-9]+$')

def resolve():
    row, col = vim.current.window.cursor

    fn = pathlib.PurePath(vim.current.buffer.name).relative_to(os.getcwd())

    cmd = ["clutter", "-i", "", "r", "--loc", f'{fn}:{row}.{col + 1}']
    proc = subprocess.run(cmd, capture_output=True)

    stderr = proc.stderr.decode('utf-8').strip()

    if proc.returncode != 0:
        print(f'clutter: {stderr}')
        return

    if stderr:
        print(f'clutter: {stderr}')

    stdout = proc.stdout.decode('utf-8')

    r = csv.reader(StringIO(stdout), delimiter=' ')

    vim.command('call setloclist(0, [], "f")')
    vim.command('call setloclist(0, [], "r", {"title": "clutter"})')

    for fs in r:
        if len(fs) != 2:
            print(f'warning: invalid output line: "{fs}"')
            continue

        name, loc = fs

        m = outpattern.match(loc)
        if not m:
            print(f'warning: invalid output line loc: "{loc}"')
            continue

        fn, lnum, col = m.groups()

        vim.command(
            'call setloclist(0, [{"filename": "%s", "lnum": %s, "col": %s, "text": "%s"}], "a")' % (
                fn, lnum, col, name
            )
        )

    vim.command('lopen')
