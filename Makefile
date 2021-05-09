.PHONY: default
default: help ;

install:
	cp -f cobalt /usr/local/bin/cobalt
	chmod +x /usr/local/bin/cobalt

uninstall:
	rm -f /usr/local/bin/cobalt

help:
	@echo "Cobalt Build System.\n"
	@echo "list of commands:"
	@echo "\tinstall"
	@echo "\tuninstall"
