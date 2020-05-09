use num_rational::Ratio;
use ordered_float::OrderedFloat;
use priority_queue::PriorityQueue;

use std::cell::Cell;
use std::cell::RefCell;
use std::collections::HashMap;
use std::collections::HashSet;
use std::rc::Rc;

const BUMP_FACTOR: f64 = 1. / 0.95;

pub struct Solver {
    literals: HashMap<i32, Rc<Lit>>,
    watchers: HashMap<i32, HashSet<usize>>,
    var_order: PriorityQueue<i32, OrderedFloat<f64>>,
    clauses: Vec<Vec<Rc<Lit>>>,
    decisions: HashMap<usize, HashSet<i32>>,
    i_graph: HashMap<i32, (usize, Vec<i32>)>,
    var_inc: f64,
    level: usize,
    cur_watchers: HashMap<i32, HashSet<usize>>,
    cur_var_order: PriorityQueue<i32, OrderedFloat<f64>>,
}

impl Solver {
    pub fn new(input: &str) -> Solver {
        let lines = input.split('\n');

        let mut clauses = Vec::new();
        let mut literals: HashMap<i32, Rc<Lit>> = HashMap::new();

        for line in lines {
            match line.chars().nth(0) {
                Some('p') => {
                    let mut p = line.split_whitespace();
                    p.next();
                    p.next();
                    let num_vars: i32 = p.next().unwrap().parse().unwrap();
                    literals = (-num_vars..=num_vars)
                        .filter(|&i| i != 0)
                        .map(|i| (i, Rc::new(Lit::new(i))))
                        .collect();
                },
                Some('c') => continue,
                Some(_) => {
                    let mut clause = HashSet::new();
                    let mut lits = line.split_whitespace();

                    loop {
                        match lits.next().unwrap().parse().unwrap() {
                            0 => break,
                            i => {clause.insert(i); continue;},
                        }
                    }

                    clauses.push(clause
                                 .iter()
                                 .map(|l| Rc::clone(&literals[l]))
                                 .collect::<Vec<_>>());
                },
                None => continue,
            }
        }

        let mut watchers: HashMap<i32, HashSet<usize>> = literals
            .iter()
            .map(|(&i, _)| (i, HashSet::new()))
            .collect();

        let var_priorities: HashMap<i32, Cell<f64>> = literals
            .iter()
            .map(|(&i, _)| (i, Cell::new(1.)))
            .collect();

        for (i, clause) in clauses.iter().enumerate() {
            for lit in clause {
                var_priorities[&lit.to_int()].replace(
                    var_priorities[&lit.to_int()].get() + 1.
                );
            }

            for j in 0..std::cmp::min(2, clause.len()) {
                let lit = clause[j].to_int();
                watchers.get_mut(&-lit).unwrap().insert(i);
            }
        }

        let mut var_order = PriorityQueue::new();
        for (lit, p) in var_priorities {
            var_order.push(lit, OrderedFloat::from(p.take()));
        }

        Solver {
            literals,
            watchers,
            var_order,
            clauses,
            cur_watchers: HashMap::new(),
            cur_var_order: PriorityQueue::new(),
            decisions: HashMap::new(),
            i_graph: HashMap::new(),
            var_inc: 1.,
            level: 0,
        }
    }

    pub fn solve(mut self) -> String {
        self.restart();

        loop {
            let conflict = self.propagate();
            if let Some(lit) = conflict {
                if self.level == 0 {
                    return "UNSAT".to_owned();
                } else {
                    self.analyze(lit);
                    self.restart();
                }
            } else {
                if self.satisfied() {
                    return self.model();
                } else {
                    self.decide();
                }
            }
        }
    }

    fn propagate(&mut self) -> Option<i32> {
        // TODO: change to Vec
        let mut unit_literals = HashSet::new();
        // at the start, the only possibly unit clause is the newly appended
        // clause, unless we are at the first iteration (0th level)
        if self.level == 0 {
            for clause in &self.clauses {
                if clause.is_unit() {
                    let lit = clause[0].to_int();
                    unit_literals.insert(lit);
                    self.decisions.get_mut(&self.level).unwrap().insert(lit);
                    self.i_graph.insert(lit, (self.level, Vec::new()));
                }
            }
        } else {
            let lit = self.decisions[&self.level].iter().next().cloned().unwrap();
            unit_literals.insert(lit);
        }

        while !unit_literals.is_empty() {
            let lit = unit_literals.iter().next().cloned().unwrap();
            unit_literals.remove(&lit);
            self.literals.get_mut(&lit).unwrap().set_true();
            self.literals.get_mut(&-lit).unwrap().set_false();

            let indexes = self.cur_watchers[&lit].clone();
            for i in indexes {
                let clause = &self.clauses[i];
                if clause.is_satisfied() {
                    // nothing to do
                    continue;
                } else if clause.is_unit() {
                    // new unit clause found
                    let unit_lit = clause.get_unset().unwrap().to_int();
                    if self.i_graph.contains_key(&unit_lit) {
                        continue
                    }
                    unit_literals.insert(unit_lit);

                    self.decisions.get_mut(&self.level).unwrap().insert(unit_lit);
                    let reason = clause
                        .iter()
                        .map(|l| l.to_int())
                        .filter(|&l| l != unit_lit)
                        .map(|l| -l)
                        .collect::<Vec<_>>();
                    self.i_graph.insert(unit_lit, (self.level, reason));
                } else if clause.is_conflict() {
                    // conflict found
                    self.decisions.get_mut(&self.level).unwrap().insert(-lit);
                    let reason = clause
                        .iter()
                        .map(|l| l.to_int())
                        .filter(|&l| l != -lit)
                        .map(|l| -l)
                        .collect::<Vec<_>>();
                    self.i_graph.insert(-lit, (self.level, reason));
                    return Some(lit);
                } else {
                    // clause not satisfied, modify watchers
                    let mut clause_iter = clause.iter();
                    let l = loop {
                        let l = clause_iter.next().unwrap();
                        if !l.is_unset() {
                            continue;
                        }
                        let l = l.to_int();
                        if self.cur_watchers[&-l].contains(&i) {
                            continue;
                        }
                        break l;
                    };

                    self.cur_watchers.get_mut(&lit).unwrap().remove(&i);
                    self.cur_watchers.get_mut(&-l).unwrap().insert(i);
                }
            }
        }

        None
    }

    fn satisfied(&self) -> bool {
        self.clauses.iter().all(Clause::is_satisfied)
    }

    fn restart(&mut self) {
        for lit in self.literals.values() {
            lit.unset();
        }
        self.cur_watchers = self.watchers.clone();
        self.cur_var_order = self.var_order.clone();
        self.decisions.insert(0, HashSet::new());
        self.i_graph.clear();
        self.level = 0;
    }

    fn model(&self) -> String {
        (1..=self.literals.len() as i32 / 2)
            .map(|l| if self.i_graph.contains_key(&-l) { -l } else { l })
            .map(|l| l.to_string())
            .collect::<Vec<_>>()
            .join(" ")
    }

    fn decide(&mut self) {
        let lit = loop {
            let next_lit = self.cur_var_order.pop().unwrap().0;
            if self.literals[&next_lit].is_unset() {
                break next_lit;
            }
        };

        self.level += 1;
        self.decisions.insert(self.level, [lit].iter().cloned().collect());
        self.i_graph.insert(lit, (self.level, Vec::new()));
    }

    fn analyze(&mut self, lit: i32) {
        // find first unique implication point (1-UIP)
        let mut uips = HashSet::new();
        let weights = self.decisions[&self.level]
            .iter()
            .map(|&l| (l, Ratio::<i128>::new(0, 1)))
            .collect::<HashMap<_, _>>();
        let weights_ref = Rc::new(RefCell::new(weights));

        fn explore(lit: i32,
                   weight: Ratio<i128>,
                   weights: Rc<RefCell<HashMap<i32, Ratio<i128>>>>,
                   i_graph: &HashMap<i32, (usize, Vec<i32>)>,
                   level: usize) {
            *weights.borrow_mut().get_mut(&lit).unwrap() += weight;
            let next_lits = i_graph[&lit].1
                                         .iter()
                                         .filter(|&l| i_graph[l].0 == level)
                                         .collect::<Vec<_>>();
            for &l in &next_lits {
                explore(*l,
                        weight / next_lits.len() as i128,
                        Rc::clone(&weights),
                        i_graph,
                        level,
                );
            }
        }

        explore(lit,
                Ratio::new(1, 1),
                Rc::clone(&weights_ref),
                &self.i_graph,
                self.level);

        for l in weights_ref.borrow().keys() {
            if weights_ref.borrow()[l] == Ratio::new(1, 1) {
                uips.insert(*l);
            }
        }
        uips.remove(&lit);

        let weights = self.decisions[&self.level]
            .iter()
            .map(|&l| (l, Ratio::new(0, 1)))
            .collect::<HashMap<_, _>>();
        let weights_ref = Rc::new(RefCell::new(weights));

        explore(-lit,
                Ratio::new(1, 1),
                Rc::clone(&weights_ref),
                &self.i_graph,
                self.level);

        for l in weights_ref.borrow().keys() {
            if weights_ref.borrow()[l] == Ratio::new(1, 1) && uips.contains(l) {
                continue;
            }

            uips.remove(l);
        }

        let mut l = lit;
        let fuip = loop {
            for &next_l in &self.i_graph[&l].1 {
                if self.i_graph[&next_l].0 == self.level {
                    l = next_l;
                    break;
                }
            }
            if uips.contains(&l) {
                break l;
            }
        };

        // find cut
        let new_clause = [-fuip].iter().cloned().collect();
        let new_clause_ref = Rc::new(RefCell::new(new_clause));

        fn find_cut(lit: i32,
                    new_clause: Rc<RefCell<HashSet<i32>>>,
                    i_graph: &HashMap<i32, (usize, Vec<i32>)>,
                    level: usize,
                    fuip: i32) {
            if i_graph[&lit].0 != level {
                new_clause.borrow_mut().insert(-lit);
                return;
            }
            if lit == fuip {
                return;
            }

            for &l in &i_graph[&lit].1 {
                find_cut(
                    l,
                    Rc::clone(&new_clause),
                    i_graph,
                    level,
                    fuip
                );
            }
        }

        find_cut(lit, Rc::clone(&new_clause_ref), &self.i_graph, self.level, fuip);
        find_cut(-lit, Rc::clone(&new_clause_ref), &self.i_graph, self.level, fuip);

        // add clause
        let clause = new_clause_ref.borrow().clone();
        self.clauses.push(
            clause
                .iter()
                .map(|&l| Rc::clone(&self.literals[&l]))
                .collect::<Vec<_>>()
        );
        let clause_idx = self.clauses.len() - 1;
        let mut clause_iter = clause.iter();
        for _ in 0..std::cmp::min(2, clause.len()) {
            let lit = -clause_iter.next().unwrap();
            self.watchers
                .get_mut(&lit)
                .unwrap()
                .insert(clause_idx);
        }

        self.var_inc *= BUMP_FACTOR;
        for lit in clause {
            if let None = self.cur_var_order.get_priority(&lit) {
                continue;
            }

            let new_p = OrderedFloat::from(self.cur_var_order
                                           .get_priority(&lit)
                                           .unwrap()
                                           .into_inner()
                                           + self.var_inc);

            self.cur_var_order.change_priority(
                &lit,
                new_p
            );

            self.var_inc *= BUMP_FACTOR;
            if new_p.into_inner() * self.var_inc > 1e100 {
                self.var_inc *= 1e-100;

                for (_, p) in &mut self.cur_var_order {
                    *p = OrderedFloat::from(p.into_inner() * 1e-100);
                }
            }
        }
    }
}

trait Clause {
    fn is_satisfied(&self) -> bool;
    fn is_conflict(&self) -> bool;
    fn is_unit(&self) -> bool;
    fn get_unset(&self) -> Option<Rc<Lit>>;
}

impl Clause for Vec<Rc<Lit>> {
    fn is_satisfied(&self) -> bool {
        self.iter().any(|lit| lit.is_true())
    }

    fn is_conflict(&self) -> bool {
        self.iter().all(|lit| lit.is_false())
    }

    fn is_unit(&self) -> bool {
        self.iter().filter(|&lit| lit.is_unset()).count() == 1
    }

    fn get_unset(&self) -> Option<Rc<Lit>> {
        for lit in self {
            if lit.is_unset() {
                return Some(Rc::clone(lit));
            }
        }

        None
    }
}

struct Lit {
    lit: i32,
    value: Cell<i8>,
}

impl Lit {
    fn new(lit: i32) -> Lit {
        Lit { lit, value: Cell::new(0) }
    }

    fn set_true(&self) {
        self.value.set(1)
    }

    fn set_false(&self) {
        self.value.set(-1)
    }

    fn unset(&self) {
        self.value.set(0)
    }

    fn is_true(&self) -> bool {
        self.value.get() == 1
    }

    fn is_false(&self) -> bool {
        self.value.get() == -1
    }

    fn is_unset(&self) -> bool {
        self.value.get() == 0
    }

    fn to_int(&self) -> i32 {
        self.lit
    }
}

impl std::fmt::Debug for Lit {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        self.lit.fmt(f)
    }
}
