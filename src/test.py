import os
import random
import solver
import subprocess
import sys
import time

TEST_CNF_PATH = 'test.cnf'


def main():
    num_vars = int(sys.argv[1])
    num_clauses = int(sys.argv[2])
    n = int(sys.argv[3])
    start = time.process_time()
    for i in range(n):
        with open(TEST_CNF_PATH, 'w') as f:
            f.write('p cnf {} {}\n'.format(num_vars, num_clauses))
            for _ in range(num_clauses):
                for _ in range(3):
                    f.write('{} '.format(random.randint(1, num_vars)
                                         * random.choice([-1, 1])))
                f.write('0\n')

        sat_solver = solver.Solver(TEST_CNF_PATH)
        sat_solver.solve()

        with open('output.txt') as f:
            output = f.read()
            print(output)
            if output == 'UNSAT':
                expected = subprocess.run(
                    "cat " + TEST_CNF_PATH +
                    "| docker run --rm -i msoos/cryptominisat "
                    "| tail -n 1 | awk '{print substr($0, 3, length($0)-4)}'",
                    shell=True,
                    capture_output=True,
                ).stdout.decode('utf-8')
                if expected[:5] == 'UNSAT':
                    continue
                print(expected)
                raise Exception(
                    'Fail on iter {}. Expected: {}. Actual: {}.'.format(
                        i,
                        expected,
                        output
                    ))
            else:
                with open('test.cnf') as f, open('temp.cnf', 'w') as temp:
                    lines = f.readlines()
                    for line in lines:
                        if line[0] == 'p':
                            p = line.split()
                            temp.write(f'p cnf {p[2]} {int(p[3])+int(p[2])}\n')
                        else:
                            temp.write(line)
                    for lit in output.split():
                        temp.write(f'{lit} 0\n')
                expected = subprocess.run(
                    "cat temp.cnf "
                    "| docker run --rm -i msoos/cryptominisat "
                    "| tail -n 1 | awk '{print substr($0, 3, length($0)-4)}'",
                    shell=True,
                    capture_output=True
                ).stdout.decode('utf-8')
                if expected[:5] == 'UNSAT':
                    raise Exception(
                        'Fail on iter {}. '
                        'Expected: UNSAT. Actual: SAT: {}'.format(
                            i,
                            output
                        ))
    print(f'Time elapsed: {time.process_time() - start}')
    os.system('say -v Zarvox And Skynet said, Let there be light: and there was light.')


if __name__ == '__main__':
    main()
