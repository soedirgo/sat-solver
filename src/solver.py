from copy import deepcopy
from fractions import Fraction
from queue import Queue


class Solver:
    '''CNF-solver implementation. Uses CDCL and restarts.

    Important components:

    clauses: The clause database, including learnt clauses.

    var_index: For each literal, we keep an index of all clauses in which the
    literal occurs. Used in unit propagation.

    cur_clauses: Current set of clauses, affected by propagation.

    cur_var_index: Current var_index, affected by propagation.

    decisions: Stores all variable assignments.

    i_graph: Implication graph. Stores reasons for each literal, i.e. variable
    assignments that imply the assignment of the literal. Used in clause
    learning.

    level: Current decision level.
    '''
    def __init__(self, dimacs_path):
        with open(dimacs_path) as f:
            lines = f.read().splitlines()
            lines = [line for line in lines if line[0] != 'c']
        p = lines[0].split()
        num_vars = int(p[2])
        self.clauses = [{int(x)
                         for x in clause.split()[:-1]}
                        for clause in lines[1:]]
        self.var_index = {i: set()
                          for i in range(-num_vars, num_vars+1)
                          if i != 0}
        for i, clause in enumerate(self.clauses):
            for l in clause:
                self.var_index[l].add(i)

    def solve(self):
        with open('output.txt', 'w') as f:
            f.write(self.cdcl())

    def cdcl(self) -> str:
        '''
        CDCL:
        loop
            propagate
            if conflict:
                if conflict at top level:
                    UNSAT
                else:
                    analyze
                    backtrack
            else:
                if all variables are assigned:
                    return model
                else:
                    decide

        (adapted from `http://minisat.se/downloads/MiniSat.pdf`)
        '''
        self.restart()
        while True:
            conflict = self.propagate()
            if conflict:
                if self.level == 0:
                    return 'UNSAT'
                else:
                    self.analyze(conflict)
                    self.restart()
            else:
                if self.satisfied():
                    return self.get_model()
                else:
                    self.decide()

    def propagate(self):
        unit_literals = set()
        # at the start, the only possibly unit clause is the newly appended
        # clause, unless we are at the first iteration (0th level)
        if self.level == 0:
            for clause in self.cur_clauses:
                if len(clause) == 1:
                    unit_l = next(iter(clause))
                    unit_literals.add(unit_l)
                    self.decisions[self.level].add(unit_l)
                    self.i_graph[unit_l] = (self.level, set())
        else:
            last_clause = self.cur_clauses[-1]
            unit_literals.add(next(iter(last_clause)))

        while len(unit_literals) > 0:
            l = unit_literals.pop()

            neg_indexes = self.cur_var_index[-l].copy()
            for i in neg_indexes:
                clause = self.cur_clauses[i]
                clause.discard(-l)
                if len(clause) == 1:
                    # new unit clause found
                    unit_l = next(iter(clause))
                    if unit_l in self.i_graph:
                        continue
                    unit_literals.add(unit_l)

                    self.decisions[self.level].add(unit_l)
                    reason = [-lit for lit in self.clauses[i] if lit != unit_l]
                    self.i_graph[unit_l] = (self.level, reason)
                elif len(clause) == 0:
                    # conflict found
                    reason = [-lit for lit in self.clauses[i] if lit != -l]
                    self.i_graph[-l] = (self.level, reason)
                    return l
            self.cur_var_index[-l].clear()

            indexes = self.cur_var_index[l].copy()
            for idx in indexes:
                for lit in self.cur_clauses[idx]:
                    self.cur_var_index[lit].discard(idx)
                self.cur_clauses[idx] = []

        return False

    def satisfied(self):
        return all(clause == [] for clause in self.cur_clauses)

    def restart(self):
        self.cur_clauses = deepcopy(self.clauses)
        self.cur_var_index = deepcopy(self.var_index)
        self.decisions = {0: set()}
        self.i_graph = {}
        self.level = 0

    def get_model(self):
        model = [l for l in self.i_graph]
        return ' '.join([str(-l) if -l in model else str(l)
                         for l in range(1, len(self.var_index)//2 + 1)])

    def decide(self):
        next_l = 0
        for clause in self.cur_clauses:
            for l in clause:
                next_l = next(iter(clause))
                break
            if next_l:
                break
        if not next_l:
            raise Exception(f'unable to choose literal: {self.cur_clauses}')

        self.level += 1
        self.decisions[self.level] = {next_l}
        self.i_graph[next_l] = (self.level, set())
        self.cur_clauses.append({next_l})
        self.cur_var_index[next_l].add(len(self.cur_clauses) - 1)

    def analyze(self, l):
        # find first unique implication point (1-UIP)

        # paths = []

        # def explore(lit, path):
        #     if self.i_graph[lit][0] != self.level:
        #         return
        #     if len(self.i_graph[lit][1]) == 0:
        #         paths.append(path)
        #         return
        #     for next_lit in self.i_graph[lit][1]:
        #         explore(next_lit, path + [next_lit])

        # explore(l, [l])
        # explore(-l, [-l])

        # lits_in_level = [lit for lit in self.decisions[self.level]]
        # uips = [lit for lit in lits_in_level
        #         if all(lit in path for path in paths)]
        # path = paths[0]
        # for lit in path:
        #     if lit in uips:
        #         fuip = lit
        #         break

        uips = set()

        def explore(lit, weight):
            weights[lit] += weight
            next_lits = [next_lit
                         for next_lit in self.i_graph[lit][1]
                         if self.i_graph[next_lit][0] == self.level]
            for next_lit in next_lits:
                explore(next_lit, weight / len(next_lits))

        weights = {lit: Fraction() for lit in self.decisions[self.level]}
        explore(l, Fraction(1.))

        for lit in weights.keys():
            if weights[lit] == Fraction(1.):
                uips.add(lit)
        uips.discard(l)

        weights = {lit: Fraction() for lit in self.decisions[self.level]}
        explore(-l, Fraction(1.))

        for lit in weights.keys():
            if weights[lit] == Fraction(1.) and lit in uips:
                continue

            uips.discard(lit)

        # lit = l
        # while True:
        #     for next_lit in self.i_graph[lit][1]:
        #         if self.i_graph[next_lit][0] == self.level:
        #             lit = next_lit
        #             break
        #     if lit in uips:
        #         fuip = lit
        #         break

        # find cut
        new_clause = set()

        def find_cut(lit):
            if self.i_graph[lit][0] != self.level:
                new_clause.add(-lit)
                return
            if lit == fuip:
                new_clause.add(-fuip)
                return
            for next_lit in self.i_graph[lit][1]:
                find_cut(next_lit)

        find_cut(l)
        find_cut(-l)
        self.clauses.append(new_clause)
        new_clause_idx = len(self.clauses) - 1
        for lit in new_clause:
            self.var_index[lit].add(new_clause_idx)

if __name__ == '__main__':
    s = Solver('test.cnf')
    s.solve()
    s = Solver('test.cnf')
    s.solve()
