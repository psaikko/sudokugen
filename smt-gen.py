#!/usr/bin/env python3

import sys
import random
from math import sqrt
from timeit import default_timer as timer

from pysmt.shortcuts import *
from pysmt.typing import INT
from pysmt.oracles import get_logic

if len(sys.argv) != 2:
    print("Required arguments: puzzle dimension")
    exit(1)

try:
    n = int(sys.argv[1])
except:
    print("Cannot parse",sys.argv[1],"as integer")
    exit(1)

start = timer()
sn = int(sqrt(n))

# Define symbols and domains for the problem
rows = [[Symbol("%d,%d" % (i,j), INT) for j in range(n)] for i in range(n)]
cols = list(zip(*rows))
blocks = [[rows[ii][jj] for ii in range(i*sn, (i+1)*sn) for jj in range(j*sn, (j+1)*sn)] for i in range(sn) for j in range(sn)]
symbols = [s for row in rows for s in row]
domains = And(And(GE(s, Int(1)), LE(s, Int(n))) for s in symbols)

# Construct SMT constraints for rows, columns, blocks
rows_constraints = And(ExactlyOne(Equals(Int(v), s) for s in row) for row in rows for v in range(1,n+1))
cols_constraints = And(ExactlyOne(Equals(Int(v), s) for s in col) for col in cols for v in range(1,n+1))
blocks_constraints = And(ExactlyOne(Equals(Int(v), s) for s in block) for block in blocks for v in range(1,n+1))
constraints = And(rows_constraints, cols_constraints, blocks_constraints)

backend = "z3" #["msat","cvc4","z3","yices"]
solver = Solver(name=backend)
formula = And(domains, constraints)
solver.add_assertion(formula)

print("Building formula: %.2fs" % (timer() - start))

# First compute the solution
start = timer()
solver.solve()

print("Generating solution: %.2fs" % (timer() - start))

# Print the solution 
for row in rows:
    print([solver.get_py_value(s) for s in row])

solution = [solver.get_value(s) for s in symbols]

# Try to find a solution which is not the original
not_solution = Not(And(Equals(v, s) for (v,s) in zip(solution, symbols)))
solver.add_assertion(not_solution)

F = And(domains,constraints)
A = [Equals(v, s) for (v,s) in zip(solution, symbols)]
random.shuffle(A)
M = []

# Destructive MUS algorithm:
# Find a minimal subset of A that entails a unique solution
while len(A):
    test = A.pop()
    if solver.solve(assumptions=A+M):
        M.append(test)
    else:
        pass
    print("\rClues checked: %3.2f%%" % ((n*n - len(A)) / (n*n) * 100), end="")
print()

# Extract hint values from symbols 
puzzle = [[" "]*n for _ in range(n)]
for hint in M:
    val, sym = hint.args()
    coords = sym.symbol_name()
    x,y = list(map(int, coords.split(",")))
    puzzle[y][x] = str(val)

for row in puzzle:
    print("".join("%2s" % i for i in row))