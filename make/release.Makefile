ifndef MK_RELEASE
MK_RELEASE=1

include make/ci.py.Makefile

build: clean
	poetry build

publish: build
	poetry publish

endif
