#!/usr/bin/env python3

import pysat
import itertools
from pysat.card import *
from pysat.solvers import MinisatGH as Solver
from pysat.formula import CNF
import random

N = 3

F = CNF()

nv = 0
def getVar():
    global nv 
    nv += 1
    return nv

# create a variable for each choice of value (1..n^2) for each cell (1..(n^2)^2)
V_flat = [getVar() for v in range((N**2)**3)]

# reshape to (N**2,N**2,N**2)
def group_by(k, l):
    for i in range(len(l)//k):
        yield l[i*k:(i+1)*k]
V = list(group_by(N**2, list(group_by(N**2, V_flat))))

# Index of last solution variable (rest are added by cardinality encodings)
max_problem_var = nv

#V = [[[getVar() for v in range(N**2)] for j in range(N**2)] for i in range(N**2)]
#V_flat = list(itertools.chain(*itertools.chain(*V)))

enc = EncType.ladder

# Encode constraints for each column
for i in range(N**2):
    for v in range(N**2):
        # Atleast-1 clause
        col = [V[i][j][v] for j in range(N**2)]
        F.append(col)
        # Atmost-1 encoding
        print(col)
        print(nv)
        print(enc)
        col = [int(i) for i in col]
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

def random_polarity(): return random.randint(0,1)*2 - 1
pols = [v * random_polarity() for v in V_flat]
solver.set_phases(pols)

# First compute a solution
if solver.solve():
    solution = [v for v in solver.get_model() if v > 0 and v <= max_problem_var]
    S = set(solution)
    for i in range(N**2):
        for j in range(N**2):
            vs = V[i][j]
            trues = [ix+1 for (ix,v) in enumerate(vs) if v in S]
            print(trues[0],end="")
        print()
    print(solver.time())

# Try to find an alternate solution (by forbidding original with a clause)
solver.add_clause([-v for v in solution])

untested_clues = solution[:]
#random.shuffle(untested_clues)

necessary_clues = []

# Compute a minimal clueset
while len(untested_clues):

    test_clue = untested_clues.pop()

    if solver.solve(assumptions=necessary_clues+untested_clues):
        # 
        necessary_clues.append(test_clue)        
    else:
        # test_clue not necessary
        print("UNSAT")
        core = solver.get_core()
        print(len(core))
        t = len(untested_clues)
        untested_clues = [l for l in untested_clues if l in core]
        if t != len(untested_clues):
            print("# dropped", t - len(untested_clues))


    print("# confirmed", len(necessary_clues))
    print("# left", len(untested_clues))

print(solver.solve(assumptions=necessary_clues)) # expect false

#print(necessary_clues)
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

