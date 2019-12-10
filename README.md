# sudokugen

Command-line tools for generating sudoku puzzles 
of variable size with unique solutions with no redundant hints.

Implemented in python using SAT and SMT solvers.

## SAT 

To use, install the [PySAT](https://pysathq.github.io/) toolkit

`pip install python-sat`

then run 

`python3 sat-gen.py n`

to compute a n-by-n puzzle.

## SMT 

First install the [PySMT](https://github.com/pysmt/pysmt) library

`pip install pysmt`

and then an SMT solver (e.g. Z3)

`pysmt install --z3`

then run 

`python3 smt-gen.py n`

to compute a n-by-n puzzle.
