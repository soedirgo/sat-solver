from copy import deepcopy
from fractions import Fraction


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

    level: Current decision level.'''

    def __init__(self, dimacs_path):
        with open(dimacs_path) as f:
            lines = f.read().splitlines()
            lines = [line for line in lines if line[0] != 'c']
        p = lines[0].split()
        num_vars = int(p[2])
        self.literals = {i: Lit(i)
                         for i in range(-num_vars, num_vars+1)
                         if i != 0}
        self.clauses = [Clause(list({self.literals[int(x)]
                                     for x in clause.split()[:-1]}))
                        for clause in lines[1:]]
        self.var_index = {i: set()
                          for i in range(-num_vars, num_vars+1)
                          if i != 0}
        for i, clause in enumerate(self.clauses):
            for lit in clause:
                self.var_index[lit.to_int()].add(i)

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
            for clause in self.clauses:
                if len(clause) == 1:
                    lit = clause[0].to_int()
                    unit_literals.add(lit)
                    self.decisions[self.level].add(lit)
                    self.i_graph[lit] = (self.level, [])
        else:
            lit = next(iter(self.decisions[self.level]))
            unit_literals.add(lit)

        while len(unit_literals) > 0:
            l = unit_literals.pop()
            self.literals[l].set_true()
            self.literals[-l].set_false()

            neg_indexes = self.cur_var_index[-l].copy()
            for i in neg_indexes:
                clause = self.clauses[i]
                if clause.is_satisfied():
                    continue

                if len(clause) == 1:
                    # new unit clause found
                    unit_lit = clause.get_unset().to_int()
                    if unit_lit in self.i_graph:
                        continue
                    unit_literals.add(unit_lit)

                    self.decisions[self.level].add(unit_lit)
                    reason = [-lit.to_int()
                              for lit in self.clauses[i]
                              if lit.to_int() != unit_lit]
                    self.i_graph[unit_lit] = (self.level, reason)
                elif clause.is_empty():
                    # conflict found
                    reason = [-lit.to_int()
                              for lit in self.clauses[i]]
                              # if lit.to_int() != -l]
                    self.i_graph[-l] = (self.level, reason)
                    return l
            self.cur_var_index[-l].clear()

            indexes = self.cur_var_index[l].copy()
            for idx in indexes:
                for lit in self.clauses[idx]:
                    self.cur_var_index[lit.to_int()].discard(idx)

        return False

    def satisfied(self):
        for clause in self.clauses:
            if not clause.is_satisfied():
                return False
        return True
        # return all(clause.is_satisfied() for clause in self.clauses)

    def restart(self):
        for lit in self.literals.values():
            lit.unset()
        self.cur_var_index = deepcopy(self.var_index)
        self.decisions = {0: set()}
        self.i_graph = {}
        self.level = 0

    def get_model(self):
        model = [l for l in self.i_graph]
        return ' '.join([str(-l) if -l in model else str(l)
                         for l in range(1, len(self.literals)//2 + 1)])

    def decide(self):
        next_lit = 0
        for clause in self.clauses:
            for lit in clause:
                if lit.is_false():
                    continue
                if lit.to_int() not in self.i_graph:
                    next_lit = lit.to_int()
                    break
            if next_lit:
                break
        if not next_lit:
            raise Exception(f'unable to choose literal')

        self.level += 1
        self.decisions[self.level] = {next_lit}
        self.i_graph[next_lit] = (self.level, [])

    def analyze(self, l):
        # find first unique implication point (1-UIP)

        uips = set()
        weights = {lit: Fraction() for lit in self.decisions[self.level]}

        def explore(lit, weight):
            weights[lit] += weight
            # next_lits = [next_lit
            #              for next_lit in self.i_graph[lit][1]
            #              if self.i_graph[next_lit][0] == self.level]
            next_lits = []
            for next_lit in self.i_graph[lit][1]:
                if self.i_graph[next_lit][0] == self.level:
                    next_lits.append(next_lit)
            for next_lit in next_lits:
                explore(next_lit, weight / len(next_lits))

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

        lit = l
        while True:
            for next_lit in self.i_graph[lit][1]:
                if self.i_graph[next_lit][0] == self.level:
                    lit = next_lit
                    break
            if lit in uips:
                fuip = lit
                break

        # find cut
        new_clause = {-fuip}

        def find_cut(lit):
            if self.i_graph[lit][0] != self.level:
                new_clause.add(-lit)
                return
            if lit == fuip:
                return

            for next_lit in self.i_graph[lit][1]:
                find_cut(next_lit)

        find_cut(l)
        find_cut(-l)

        self.clauses.append(Clause([self.literals[lit] for lit in new_clause]))
        new_clause_idx = len(self.clauses) - 1
        for lit in new_clause:
            self.var_index[lit].add(new_clause_idx)


class Clause:
    def __init__(self, lits):
        self.lits = lits

    def __getitem__(self, key):
        return self.lits[key]

    def __len__(self):
        return sum(lit.is_unset() for lit in self.lits)

    def __iter__(self):
        yield from self.lits

    def is_satisfied(self):
        return any(lit.is_true() for lit in self.lits)

    def is_empty(self):
        return all(lit.is_false() for lit in self.lits)

    def get_unset(self):
        for lit in self.lits:
            if lit.is_unset():
                return lit


class Lit:
    def __init__(self, lit):
        self.lit = lit
        self.value = 0

    def set_true(self):
        self.value = 1

    def set_false(self):
        self.value = -1

    def unset(self):
        self.value = 0

    def is_true(self):
        return self.value == 1

    def is_false(self):
        return self.value == -1

    def is_unset(self):
        return self.value == 0

    def to_int(self):
        return self.lit


if __name__ == '__main__':
    s = Solver('test.cnf')
    s.solve()
