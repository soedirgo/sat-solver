extern crate clap;
use clap::{ Arg, App };

use std::fs;

use sat_solver::Solver;

fn main() {
    let matches = App::new("CNF SAT Solver")
        .version("0.1.0")
        .author("Bobbie Soedirgo <bobbie@soedirgo.dev>")
        .about("CDCL SAT solver for instances in DIMACS CNF format")
        .arg(Arg::with_name("input")
             .value_name("FILE")
             .help("Path of .cnf input file")
             .takes_value(true)
             .required(true))
        .arg(Arg::with_name("output")
             .short("o")
             .long("output")
             .value_name("FILE")
             .help("Path of output file, prints to standard output if unspecified")
             .takes_value(true)
             .required(false))
        .get_matches();

    let cnf = fs::read_to_string(matches.value_of("input").unwrap())
        .expect("Failed reading from file");

    let solver = Solver::new(&cnf);

    let result = format!("{}", solver.solve());

    if matches.is_present("output") {
        fs::write(matches.value_of("output").unwrap(), result).unwrap();
    } else {
        println!("{}", result)
    }
}
