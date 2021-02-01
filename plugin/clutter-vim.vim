if !has("python3")
    echo "vim has to be compiled with +python3 to run this"
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
EOF

function! Resolve()
    python3 clutter.resolve()
endfunction

command! -nargs=0 Resolve call Resolve()

map <Leader>cr :Resolve<CR>

let g:clutter_plugin_loaded = 1
