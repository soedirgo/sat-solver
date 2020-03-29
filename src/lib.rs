#![allow(dead_code)]

use ordered_float::OrderedFloat;
use priority_queue::PriorityQueue;

use std::collections::HashMap;
use std::cell::Cell;
use std::rc::Rc;

const BUMP_FACTOR: f64 = 1 as f64 / 0.95;

pub struct Solver {
    literals: HashMap<i32, Rc<Lit>>,
    watchers: HashMap<i32, Vec<usize>>,
    clauses: Vec<Vec<Rc<Lit>>>,
    var_order: PriorityQueue<i32, OrderedFloat<f64>>,
    var_inc: f64,
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
                    let mut clause = Vec::new();
                    let mut lits = line.split_whitespace();

                    loop {
                        match lits.next().unwrap().parse().unwrap() {
                            0 => break,
                            i => clause.push(Rc::clone(&literals[&i])),
                        }
                    }

                    clauses.push(clause);
                },
                None => continue,
            }
        }

        let mut watchers: HashMap<i32, Vec<usize>> = literals
            .iter()
            .map(|(&i, _)| (i, Vec::new()))
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
                watchers.get_mut(&-lit).unwrap().push(i);
            }
        }

        let mut var_order = PriorityQueue::new();
        for (lit, p) in var_priorities {
            var_order.push(lit, OrderedFloat::from(p.take()));
        }

        Solver {
            literals,
            watchers,
            clauses,
            var_order,
            var_inc: 1.,
        }
    }

    pub fn solve(&self) -> String {
        println!("literals");
        println!("{:?}", self.literals);
        println!();
        println!("watchers");
        println!("{:?}", self.watchers);
        println!();
        println!("clauses");
        println!("{:?}", self.clauses);
        println!();
        println!("var_order");
        println!("{:?}", self.var_order);
        println!();
        "something".to_owned()
    }
}

#[derive(Debug)]
struct Lit {
    lit: i32,
    value: Cell<i8>,
}

trait Clause {
    fn is_satisfied(&self) -> bool;
    fn is_empty(&self) -> bool;
    fn is_unit(&self) -> bool;
    fn get_unset(&self) -> Option<Rc<Lit>>;
}

impl Clause for Vec<Rc<Lit>> {
    fn is_satisfied(&self) -> bool {
        self.iter().any(|lit| lit.is_true())
    }

    fn is_empty(&self) -> bool {
        self.iter().all(|lit| lit.is_true())
    }

    fn is_unit(&self) -> bool {
        self.iter().filter(|&lit| lit.is_true()).count() == 1
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
