from typing import Dict, List, Set
from copy import deepcopy


class Solver:
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
            f.write(self.dpll(self.clauses, self.var_index, {0: set()}, 0))

    def cdcl(self) -> str:
        while True:
            self.cur_clauses = deepcopy(self.clauses)
            self.cur_var_index = deepcopy(self.var_index)
            self.decisions = {}
            self.i_graph = {}
            self.level = 0

            prop_result = self.propagate()
            if prop_result:
                if self.level == 0:
                    return 'UNSAT'
                else:
                    new_clause = self.analyze(prop_result)
                    self.clauses.append(new_clause)
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
                    unit_literals.add(next(iter(clause)))
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

    def get_model(self):
        model = [l
                 for level in self.decisions
                 for l in self.decisions[self.level]]
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
        pass

    def dpll(self,
             clauses: List,
             var_index: Dict[int, Set[int]],
             decisions: Dict[int, Set[int]],
             level: int) -> str:
        # propagate
        while (True):
            unit_literals = self.get_unit_literals(clauses)
            if len(unit_literals) == 0:
                break
            for literal in unit_literals:
                self.unit_propagate(literal, clauses, var_index)
                decisions[level].add(literal)

        # unsat
        if self.contains_empty_clause(clauses):
            return 'UNSAT'
        # sat
        if all(clause == [] for clause in clauses):
            assignment = [l for lvl in decisions for l in decisions[lvl]]
            return ' '.join([str(-l) if -l in assignment else str(l)
                             for l in range(1, len(self.var_index)//2 + 1)])

        # choose literal
        next_l = self.choose_literal(clauses)
        next_var_index = deepcopy(var_index)
        next_var_index[next_l].add(len(clauses))
        decisions[level+1] = {next_l}
        next_result = self.dpll(deepcopy(clauses) + [{next_l}],
                                next_var_index,
                                decisions,
                                level+1)
        if next_result == 'UNSAT':
            neg_next_var_index = deepcopy(var_index)
            decisions[level+1] = {-next_l}
            neg_next_var_index[-next_l].add(len(clauses))
            return self.dpll(deepcopy(clauses) + [{-next_l}],
                             neg_next_var_index,
                             decisions,
                             level+1)
        return next_result

    def contains_empty_clause(self, clauses: List) -> bool:
        return set() in clauses

    def get_unit_literals(self, clauses: List) -> Set[int]:
        unit_literals = set()
        for clause in clauses:
            if len(clause) == 1:
                unit_literals.add(next(iter(clause)))
        return unit_literals

    def unit_propagate(self, l: int, clauses: List, var_index: Dict):
        neg_indexes = var_index[-l].copy()
        for i in neg_indexes:
            clauses[i].discard(-l)
        var_index[-l].clear()

        indexes = var_index[l].copy()
        for i in indexes:
            for j in clauses[i]:
                var_index[j].discard(i)
            clauses[i] = []

    def choose_literal(self, clauses):
        for clause in clauses:
            if len(clause):
                return next(iter(clause))
        raise Exception(f'unable to choose literal: {clauses}')
