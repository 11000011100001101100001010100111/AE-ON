import os; 
def t(p, l=0):
    for f in sorted(os.listdir(p)):
        d = os.path.join(p, f)
        print('  ' * l + ('┗━ ' if l > 0 else '') + f)
        if os.path.isdir(d): t(d, l + 1)
t(os.path.expanduser('~/talon_alta'))
