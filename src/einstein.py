'''
Ordering:

| Brit      | Blue   | Beer   | Blends      | Bird  |
| Dane      | Green  | Coffee | Bluemasters | Cat   |
| German    | Red    | Milk   | Dunhill     | Dog   |
| Norwegian | White  | Tea    | Pall Mall   | Fish  |
| Swede     | Yellow | Water  | Prince      | Horse |

For locations, order is left (1) to right (5)

e.g.
`The Brit lives in the red house' is h1,3
`The Norwegian lives in the first house' is l4,1
'''


def main():
    houses = [[f'h{i},{j}' for j in range(1, 6)] for i in range(1, 6)]
    locations = [[f'l{i},{j}' for j in range(1, 6)] for i in range(1, 6)]
    drinks = [[f'd{i},{j}' for j in range(1, 6)] for i in range(1, 6)]
    smokes = [[f's{i},{j}' for j in range(1, 6)] for i in range(1, 6)]
    pets = [[f'p{i},{j}' for j in range(1, 6)] for i in range(1, 6)]

    all_literals = ([literal for row in houses for literal in row]
                    + [literal for row in locations for literal in row]
                    + [literal for row in drinks for literal in row]
                    + [literal for row in smokes for literal in row]
                    + [literal for row in pets for literal in row])
    literal_to_num = {literal: str(num+1)
                      for num, literal in enumerate(all_literals)}
    print(literal_to_num)

    clauses = []

    # The Brit lives in the red house.
    # h1,3
    clauses.append(literal_to_num['h1,3'])

    # The Swede keeps dogs as pets.
    # p5,3
    clauses.append(literal_to_num['p5,3'])

    # The Dane drinks tea.
    # d2,4
    clauses.append(literal_to_num['d2,4'])

    # The green house is on the left of the white house.
    # (h{a},2 * l{a},{b} * h{c},4) -> l{c},{b+1}
    for a in range(1, 6):
        for b in range(1, 5):
            for c in range(1, 6):
                if a == c:
                    continue
                h1 = literal_to_num[f'h{a},2']
                l1 = literal_to_num[f'l{a},{b}']
                h2 = literal_to_num[f'h{c},4']
                l2 = literal_to_num[f'l{c},{b+1}']
                clauses.append(f'-{h1} -{l1} -{h2} {l2}')

    # The green house's owner drinks coffee.
    # h{a},2 -> d{a},2
    for a in range(1, 6):
        h = literal_to_num[f'h{a},2']
        d = literal_to_num[f'd{a},2']
        clauses.append(f'-{h} {d}')

    # The person who smokes Pall Mall rears birds.
    # s{a},4 -> p{a},1
    for a in range(1, 6):
        s = literal_to_num[f's{a},4']
        p = literal_to_num[f'p{a},1']
        clauses.append(f'-{s} {p}')

    # The owner of the yellow house smokes Dunhill.
    # h{a},5 -> s{a},3
    for a in range(1, 6):
        h = literal_to_num[f'h{a},5']
        s = literal_to_num[f's{a},3']
        clauses.append(f'-{h} {s}')

    # The man living in the center house drinks milk.
    # l{a},3 -> d{a},3
    for a in range(1, 6):
        l = literal_to_num[f'l{a},3']
        d = literal_to_num[f'd{a},3']
        clauses.append(f'-{l} {d}')

    # The Norwegian lives in the first house.
    # l4,1
    clauses.append(literal_to_num['l4,1'])

    # The man who smokes Blends lives next to the one who keeps cats.
    # (s{a},1 * l{a},{b} * p{c},2) -> (l{c},{b-1} + l{c},{b+1})
    for a in range(1, 6):
        for b in range(1, 6):
            for c in range(1, 6):
                if a == c:
                    continue

                s = literal_to_num[f's{a},1']
                l1 = literal_to_num[f'l{a},{b}']
                p = literal_to_num[f'p{c},2']
                if b == 1:
                    l2 = literal_to_num[f'l{c},{b+1}']
                    clauses.append(f'-{s} -{l1} -{p} {l2}')
                elif b == 5:
                    l2 = literal_to_num[f'l{c},{b-1}']
                    clauses.append(f'-{s} -{l1} -{p} {l2}')
                else:
                    l2 = literal_to_num[f'l{c},{b-1}']
                    l3 = literal_to_num[f'l{c},{b+1}']
                    clauses.append(f'-{s} -{l1} -{p} {l2} {l3}')

    # The man who keeps the horse lives next to the man who smokes Dunhill.
    # (p{a},5 * l{a},{b} * s{c},3) -> (l{c},{b-1} + l{c},{b+1})
    for a in range(1, 6):
        for b in range(1, 6):
            for c in range(1, 6):
                if a == c:
                    continue

                p = literal_to_num[f'p{a},5']
                l1 = literal_to_num[f'l{a},{b}']
                s = literal_to_num[f's{c},3']
                if b == 1:
                    l2 = literal_to_num[f'l{c},{b+1}']
                    clauses.append(f'-{p} -{l1} -{s} {l2}')
                elif b == 5:
                    l2 = literal_to_num[f'l{c},{b-1}']
                    clauses.append(f'-{p} -{l1} -{s} {l2}')
                else:
                    l2 = literal_to_num[f'l{c},{b-1}']
                    l3 = literal_to_num[f'l{c},{b+1}']
                    clauses.append(f'-{p} -{l1} -{s} {l2} {l3}')

    # The owner who smokes Bluemasters drinks beer.
    # s{a},2 -> d{a},1
    for a in range(1, 6):
        s = literal_to_num[f's{a},2']
        d = literal_to_num[f'd{a},1']
        clauses.append(f'-{s} {d}')

    # The German smokes Prince.
    # s3,5
    clauses.append(literal_to_num['s3,5'])

    # The Norwegian lives next to the blue house.
    # (l4,{a} * h{b},1) -> (l{b},{a-1} + l{b},{a+1})
    for a in range(1, 6):
        for b in range(1, 6):
            if b == 4:
                continue

            l1 = literal_to_num[f'l4,{a}']
            h = literal_to_num[f'h{b},1']
            if a == 1:
                l2 = literal_to_num[f'l{b},{a+1}']
                clauses.append(f'-{l1} -{h} {l2}')
            elif a == 5:
                l2 = literal_to_num[f'l{b},{a-1}']
                clauses.append(f'-{l1} -{h} {l2}')
            else:
                l2 = literal_to_num[f'l{b},{a-1}']
                l3 = literal_to_num[f'l{b},{a+1}']
                clauses.append(f'-{l1} -{h} {l2} {l3}')

    # The man who smokes Blends has a neighbor who drinks water.
    # (s{a},1 * l{a},{b} * d{c},5) -> (l{c},{b-1} + l{c},{b+1})
    for a in range(1, 6):
        for b in range(1, 6):
            for c in range(1, 6):
                if a == c:
                    continue

                s = literal_to_num[f'p{a},5']
                l1 = literal_to_num[f'l{a},{b}']
                d = literal_to_num[f's{c},3']
                if b == 1:
                    l2 = literal_to_num[f'l{c},{b+1}']
                    clauses.append(f'-{s} -{l1} -{d} {l2}')
                elif b == 5:
                    l2 = literal_to_num[f'l{c},{b-1}']
                    clauses.append(f'-{s} -{l1} -{d} {l2}')
                else:
                    l2 = literal_to_num[f'l{c},{b-1}']
                    l3 = literal_to_num[f'l{c},{b+1}']
                    clauses.append(f'-{s} -{l1} -{d} {l2} {l3}')

    # Only one person per house, one house per person, one person per pet, one
    # pet per person, etc.
    exactly_ones = []
    for kind in ['h', 'l', 'd', 's', 'p']:
        for i in range(5):
            exactly_ones.append([kind + f'{i+1},{j+1}' for j in range(5)])
            exactly_ones.append([kind + f'{j+1},{i+1}' for j in range(5)])
    for exactly_one in exactly_ones:
        literals = [literal_to_num[literal] for literal in exactly_one]
        clauses.append(' '.join(literals))
        for i in range(5):
            for j in range(i+1, 5):
                clauses.append(f'-{literals[i]} -{literals[j]}')

    clauses = [clause + ' 0\n' for clause in clauses]
    with open('einstein.cnf', 'w') as f:
        f.write(f'p cnf {len(all_literals)} {len(clauses)}\n')
        f.writelines(clauses)


if __name__ == '__main__':
    main()
