import math

def separa(dados, n):
    table = []
    base = []
    for i, palavra in enumerate(dados):
        base.append(palavra)
        if (i+1) % n == 0:
            table.append(base)
            base = []

    return table


dados = ['sad', 'sdkas','sad', 'sdkas','sad', 'sdkas','sad', 'sdkas','sad',
         'sdkas','sad', 'sdkas','sad', 'sdkas','sad', 'sdjasd', 'kajdk', 'kas']
n = math.floor(math.sqrt(len(dados)))
table = separa(dados, n)

if len(table) == n:
    print(table)
else:
    print('error')
    print(table)
