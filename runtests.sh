#!/bin/bash
#PKGDB_CONFIG=../tests/pkgdb_test.cfg PYTHONPATH=pkgdb nosetests \

PYTHONPATH=pkgdb ./nosetests \
--with-coverage --cover-erase --cover-package=pkgdb2 $*
