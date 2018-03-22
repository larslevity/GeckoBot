#!/bin/bash

bold=$(tput bold)
normal=$(tput sgr0)

set -e

echo "${bold}pep8 --show-source --show-pep8 --exclude='Code/Docs' Code${normal}"
pep8 --show-source --show-pep8 --exclude='Code/Docs' Code

echo "${bold}pylint --rcfile='.pylintrc' --ignore=__pycache__ Code/Src code/*.py${normal}"
pylint --rcfile='.pylintrc' --ignore=__pycache__ Code/Src Code/*.py


echo "${bold}python -m doctest src/*.py${normal}"
(cd Code && python -m doctest src/*.py)
echo "${bold}python -m doctest src/*/*.py${normal}"
(cd Code && python -m doctest src/*/*.py)

echo "${bold}(cd Code && nosetests --with-coverage --cover-package=src --cover-tests --cover-min-percentage=95 Src/Test/*.py)${normal}"
(cd Code && nosetests --with-coverage --cover-package=src --cover-tests --cover-min-percentage=95 Src/Test/*.py)
