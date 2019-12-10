#!/usr/bin/env python3

import pysat
import itertools
import random
import sys
from math import sqrt
from pysat.card import *
from pysat.solvers import MinisatGH as Solver
from pysat.formula import CNF

if len(sys.argv) != 2:
    print("Required arguments: puzzle dimension")
    exit(1)

try:
    N = int(sqrt(int(sys.argv[1], 10)))
except:
    print("Cannot parse",sys.argv[1],"as integer")
    exit(1)

F = CNF()

nv = 0
def getVar():
    global nv 
    nv += 1
    return nv

# create a variable for each choice of value (1..n^2) for each cell (1..(n^2)^2)
V_flat = [getVar() for v in range((N**2)**3)]

# shuffle variable order to randomize generated solution
random.shuffle(V_flat)

# reshape to (N**2,N**2,N**2)
def group_by(k, l):
    for i in range(len(l)//k):
        yield l[i*k:(i+1)*k]
V = list(group_by(N**2, list(group_by(N**2, V_flat))))

# Index of last solution variable (rest are added by cardinality encodings)
max_problem_var = nv

enc = EncType.ladder

# Encode constraints for each column
for i in range(N**2):
    for v in range(N**2):
        # Atleast-1 clause
        col = [V[i][j][v] for j in range(N**2)]
        F.append(col)
        # Atmost-1 encoding
        card = pysat.card.CardEnc.atmost(lits=col, top_id=nv, bound=1, encoding=enc)
        F.extend(card.clauses)
        nv = card.nv

# Encode constraints for each row
for j in range(N**2):
    for v in range(N**2):
        # Atleast-1 clause
        row = [V[i][j][v] for i in range(N**2)]
        F.append(row)
        # Atmost-1 encoding
        card = pysat.card.CardEnc.atmost(lits=row, top_id=nv, bound=1, encoding=enc)
        F.extend(card.clauses)
        nv = card.nv

# Encode constraints for each square
for bi in range(N):
    for bj in range(N):
        for v in range(N**2):
            # Atleast-1 clause
            blk = [V[i][j][v] for i in range(bi*N,bi*N+N) for j in range(bj*N,bj*N+N)]
            F.append(blk)
            # Atmost-1 encoding
            card = pysat.card.CardEnc.atmost(lits=blk, top_id=nv, bound=1, encoding=enc)
            F.extend(card.clauses)
            nv = card.nv

# Encode constraints for each cell
for i in range(N**2):
    for j in range(N**2):
        # Atleast-1 clause
        F.append(V[i][j]) 
        # Atmost-1 encoding
        card = pysat.card.CardEnc.atmost(lits=V[i][j], top_id=nv, bound=1, encoding=enc)
        F.extend(card.clauses)
        nv = card.nv

solver = Solver(bootstrap_with=F.clauses,use_timer=True)

# First compute a solution
if solver.solve():
    solution = [v for v in solver.get_model() if v > 0 and v <= max_problem_var]
    S = set(solution)
    for i in range(N**2):
        for j in range(N**2):
            vs = V[i][j]
            trues = [ix+1 for (ix,v) in enumerate(vs) if v in S]
            print("%2d"%trues[0],end="")
        print()
    print(solver.time())

# Try to find an alternate solution (by forbidding original with a clause)
solver.add_clause([-v for v in solution])

untested_clues = solution[:]
random.shuffle(untested_clues)

necessary_clues = []

solver.set_phases(v * random.randint(0,1)*2-1 for v in V_flat)

# Compute a minimal clueset
while len(untested_clues):

    test_clue = untested_clues.pop()

    if solver.solve(assumptions=necessary_clues+untested_clues):
        # Alternate solution exists, keep test_clue 
        necessary_clues.append(test_clue)        
    else:
        # No alternate solutions, drop test_clue
        core = solver.get_core()
        # Remove clues not necessary for deriving unsatisfiability
        untested_clues = [l for l in untested_clues if l in core]
    print("\rClues checked: %3.2f%%" % ((len(solution) - len(untested_clues)) / len(solution) * 100), end="")
print()
print("Checking uniqueness: ",end="")
print("error" if solver.solve(assumptions=necessary_clues) else "OK") # expect false

necessary_clues = set(necessary_clues)
for i in range(N**2):
    for j in range(N**2):
        vs = V[i][j]
        trues = [ix+1 for (ix,v) in enumerate(vs) if v in necessary_clues]
        if len(trues):
            print("%2d"%trues[0],end="")
        else:
            print("  ",end="")
    print()

print("Solver time: %.2fs" % solver.time_accum())
