.PHONY: install uninstall

install:
	cp -f cobalt /usr/bin/cobalt
	chmod +x /usr/bin/cobalt

uninstall:
	rm -f /usr/bin/cobalt

help:
	@echo Cobalt Build System.
	@echo
	@echo list of commands:
	@echo    install
	@echo    uninstall
