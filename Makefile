help:
	@echo Cobalt Build System.\n
	@echo list of commands:
	@echo    install
	@echo    uninstall

install:
	cp -f cobalt /usr/bin/cobalt
	chmod +x /usr/bin/cobalt

uninstall:
	rm -f /usr/bin/cobalt

.PHONY: install
