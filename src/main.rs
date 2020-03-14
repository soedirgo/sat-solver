use structopt::StructOpt;

use std::collections::{BTreeSet, HashSet};

#[derive(StructOpt)]
struct Cli {
    #[structopt(parse(from_os_str), default_value = "src/test.cnf")]
    dimacs_path: std::path::PathBuf,
}

#[derive(Debug)]
struct Solver {
    num_vars: u32,
    num_clauses: u32,
    clauses: HashSet<BTreeSet<i32>>,
}

impl Solver {
    fn solve(&mut self) {
        println!();
    }

    fn dpll(&mut self) {
        println!();
    }

    fn contains_empty_clause(&mut self) {
        println!();
    }

    fn get_unit_clauses(&mut self) {
        println!();
    }

    fn unit_propagate(&mut self) {
        println!();
    }

    fn get_pure_literals(&mut self) {
        println!();
    }

    fn choose_literal(&mut self) {
        println!();
    }
}

fn main() -> Result<(), std::io::Error> {
    let args = Cli::from_args();
    let content = std::fs::read_to_string(&args.dimacs_path)?;
    for line in content.lines() {
        println!("{}", line);
    }

    let solver = Solver {
        num_vars: 3,
        num_clauses: 10,
        clauses: HashSet::new(),
    };
    println!("{:?}", solver);

    Ok(())
}
