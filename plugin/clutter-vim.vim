if !has("python3")
    echo "clutter required vim has to be compiled with +python3 to run"
    finish
endif

if exists('g:clutter_plugin_loaded')
    finish
endif

let s:plugin_root_dir = fnamemodify(resolve(expand('<sfile>:p')), ':h')

python3 << EOF
import sys
from os.path import normpath, join
import vim
plugin_root_dir = vim.eval('s:plugin_root_dir')
python_root_dir = normpath(join(plugin_root_dir, '..', 'python'))
sys.path.insert(0, python_root_dir)
import clutter

clutter.check()
EOF

function! ResolveList()
    python3 clutter.resolve_list()
endfunction

function! ResolveNext()
    python3 clutter.resolve1('n')
endfunction

function! ResolvePrev()
    python3 clutter.resolve1('p')
endfunction

function! SearchExact(...)
    python3 clutter.search('', vim.eval('a:000'))
endfunction

function! SearchGlob(...)
    python3 clutter.search('g', vim.eval('a:000'))
endfunction

function! SearchRegexp(...)
    python3 clutter.search('e', vim.eval('a:000'))
endfunction

command! -nargs=0 ClutterResolveList call ResolveList()
command! -nargs=0 ClutterResolveNext call ResolveNext()
command! -nargs=0 ClutterResolvePrev call ResolvePrev()
command! -nargs=* ClutterSearchExact call SearchExact(<f-args>)
command! -nargs=* ClutterSearchGlob call SearchGlob(<f-args>)
command! -nargs=* ClutterSearchRegexp call SearchRegexp(<f-args>)

map <Leader>cl :ClutterResolveList<CR>
map <Leader>cp :ClutterResolvePrev<CR>
map <Leader>cn :ClutterResolveNext<CR>

let g:clutter_plugin_loaded = 1
