.PHONY: nop
nop:
	echo nop

.PHONY: link
link:
	ln -s "$(shell pwd)" ~/.vim/bundle/vim-clutter

.PHONY: unlink
unlink:
	rm -f ~/.vim/bundle/vim-clutter
