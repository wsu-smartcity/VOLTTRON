#!/bin/sh

echo $CWD

# The context should already have been activated at this point.
tree .

pip install pytest pytest-bdd pytest-cov

py.test
