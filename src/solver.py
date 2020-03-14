from typing import Dict, List, Set
from copy import deepcopy


class Solver:
    def __init__(self, dimacs_path):
        with open(dimacs_path) as f:
            lines = f.read().splitlines()
            lines = [line for line in lines if line[0] != 'c']
        p = lines[0].split()
        self.num_vars = int(p[2])
        self.num_clauses = int(p[3])
        self.clauses = [{int(x) for x in clause.split()[:-1]}
                        for clause in lines[1:]]
        self.var_index = dict()
        for i, clause in enumerate(self.clauses):
            for literal in clause:
                if literal in self.var_index:
                    self.var_index[literal].add(i)
                else:
                    self.var_index[literal] = {i}

    def solve(self):
        with open('output.txt', 'w') as f:
            f.write(self.dpll(self.clauses, self.var_index, {0: set()}, 0))

    def dpll(self,
             clauses: List,
             var_index: Dict[int, Set[int]],
             decisions: Dict[int, Set[int]],
             level: int) -> str:
        while (True):
            unit_literals = self.get_unit_literals(clauses)
            if len(unit_literals) == 0:
                break
            for literal in unit_literals:
                self.unit_propagate(literal, clauses, var_index)
                decisions[level].add(literal)
        if self.contains_empty_clause(clauses):
            return 'UNSAT'
        if all(clause == [] for clause in clauses):
            assignment = [l for lvl in decisions for l in decisions[lvl]]
            return ' '.join([str(-l) if -l in assignment else str(l)
                             for l in range(1, self.num_vars+1)])
        next_l = self.choose_literal(clauses)
        next_var_index = deepcopy(var_index)
        if next_l in next_var_index:
            next_var_index[next_l].add(len(clauses))
        else:
            next_var_index[next_l] = {len(clauses)}
        decisions.update({level+1: {next_l}})
        next_result = self.dpll(deepcopy(clauses) + [{next_l}],
                                next_var_index,
                                decisions,
                                level+1)
        if next_result == 'UNSAT':
            neg_next_var_index = deepcopy(var_index)
            decisions.update({level+1: {-next_l}})
            if -next_l in neg_next_var_index:
                neg_next_var_index[-next_l].add(len(clauses))
            else:
                neg_next_var_index[-next_l] = {len(clauses)}
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
        if -l in var_index:
            neg_indexes = var_index[-l].copy()
            for i in neg_indexes:
                clauses[i].discard(-l)
            var_index[-l].clear()

        if l in var_index:
            indexes = var_index[l].copy()
            for i in indexes:
                for j in clauses[i]:
                    var_index[j].discard(i)
                clauses[i] = []

    def choose_literal(self, clauses):
        for clause in clauses:
            if len(clause):
                return next(iter(clause))
        raise Exception('unable to choose literal: {}'.format(clauses))
