#!/bin/sh
(cd Docs && sphinx-apidoc -o . ../Code)
(cd Docs && make html)

# firefox Code/Docs/_build/html/index.html
# ln Code/Docs/_build/html/index.html documentation.html
