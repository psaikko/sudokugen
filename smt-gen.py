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

rows = [[Symbol("%d,%d" % (i,j), INT) for j in range(n)] for i in range(n)]
cols = list(zip(*rows))
blocks = [[rows[ii][jj] for ii in range(i*sn, (i+1)*sn) for jj in range(j*sn, (j+1)*sn)] for i in range(sn) for j in range(sn)]

symbols = [s for row in rows for s in row]
domains = And(And(GE(s, Int(1)), LE(s, Int(n))) for s in symbols)

rows_constraints = And(ExactlyOne(Equals(Int(v), s) for s in row) for row in rows for v in range(1,n+1))
cols_constraints = And(ExactlyOne(Equals(Int(v), s) for s in col) for col in cols for v in range(1,n+1))
blocks_constraints = And(ExactlyOne(Equals(Int(v), s) for s in block) for block in blocks for v in range(1,n+1))
constraints = And(rows_constraints, cols_constraints, blocks_constraints)

#hints = And(And(Equals(symbol, Int(value)) for (symbol, value) in zip(symbols, values) if value != 0) for (symbols, values) in zip(rows, instance))

#["msat","cvc4","z3","yices"]
backend = "z3"
solver = Solver(name=backend)
formula = And(domains, constraints)
solver.add_assertion(formula)

print("Building formula: %.2fs" % (timer() - start))

start = timer()
solver.solve()

print("Generating solution: %.2fs" % (timer() - start))

for row in rows:
    print([solver.get_py_value(s) for s in row])

solution = [solver.get_value(s) for s in symbols]

not_solution = Not(And(Equals(v, s) for (v,s) in zip(solution, symbols)))

F = And(domains,constraints)
A = [Equals(v, s) for (v,s) in zip(solution, symbols)]

# imp_symbols = [Symbol("I%d" % i, BOOL) for i in range(len(symbols))]
# solver2 = Solver(name="z3")
# k_symbol = Symbol("k", INT)
# impls = And(Implies(i, a) for (i,a) in zip(imp_symbols, A))
# k_hints = Equals( k_symbol, Plus(Ite(a, Int(1), Int(0)) for a in imp_symbols) )
# Q = And(k_hints, Not(Exists(symbols, And(impls, F, not_solution))))
# solver2.add_assertion(Q)
# for k in range(len(A)):
#     k_constr = Equals(k_symbol, Int(k))
#     if solver2.solve(assumptions=[k_constr]):
#         print(k, True)
#         for i in range(n):
#              print([int(solver2.get_py_value(imp_symbols[i*n+m])) for m in range(n)])
#         break
#     else:
#         print(k, False)

solver.add_assertion(not_solution)

A = [Equals(v, s) for (v,s) in zip(solution, symbols)]
random.shuffle(A)
M = []

while len(A):
    test = A.pop()
    if solver.solve(assumptions=A+M):
        M.append(test)
    else:
        pass
    print("\rClues checked: %3.2f%%" % ((n*n - len(A)) / (n*n) * 100), end="")
print()

puzzle = [[" "]*n for _ in range(n)]
for hint in M:
    val, sym = hint.args()
    coords = sym.symbol_name()
    x,y = list(map(int, coords.split(",")))
    puzzle[y][x] = str(val)

for row in puzzle:
    print("".join("%2s" % i for i in row))