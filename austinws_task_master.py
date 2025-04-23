#!/usr/bin/env python3
"""
CSCE355-001, Wiley Austin, Final Project, 4/21/2025

Reads postfix regexes from stdin (one per line), and based on the
command-line option (--task), outputs either "yes"/"no" (for boolean queries)
or a transformed regex in prefix form.
"""
import sys

class Node:
    def __init__(self, kind, children=None, value=None):
        self.kind = kind          # 'union','concat','star','symbol','empty'
        self.children = children or []
        self.value = value        # only for 'symbol'

def parse_postfix(line):
    stack = []
    for c in line.strip():
        if c == '*':
            c0 = stack.pop()
            stack.append(Node('star', [c0]))
        elif c == '+':
            r, l = stack.pop(), stack.pop()
            stack.append(Node('union', [l, r]))
        elif c == '.':
            r, l = stack.pop(), stack.pop()
            stack.append(Node('concat', [l, r]))
        else:
            if c == '/':
                stack.append(Node('empty'))    # empty‐language
            else:
                stack.append(Node('symbol', value=c)) # reg symbol
    return stack[0] if stack else None

def to_prefix(n):
    if n.kind == 'empty':   return '/'
    if n.kind == 'symbol':  return n.value
    if n.kind == 'union':   return '+' + to_prefix(n.children[0]) + to_prefix(n.children[1])
    if n.kind == 'concat':  return '.' + to_prefix(n.children[0]) + to_prefix(n.children[1])
    if n.kind == 'star':    return '*' + to_prefix(n.children[0])
    raise ValueError(n.kind)

def is_empty(n):
    if   n.kind == 'empty':  return True
    if   n.kind == 'symbol': return False
    if   n.kind == 'union':  return is_empty(n.children[0]) and is_empty(n.children[1])
    if   n.kind == 'concat': return is_empty(n.children[0]) or is_empty(n.children[1])
    if   n.kind == 'star':   return False

def has_epsilon(n):
    if   n.kind == 'empty':  return False
    if   n.kind == 'symbol': return False
    if   n.kind == 'union':  return has_epsilon(n.children[0]) or has_epsilon(n.children[1])
    if   n.kind == 'concat': return has_epsilon(n.children[0]) and has_epsilon(n.children[1])
    if   n.kind == 'star':   return True

def has_nonepsilon(n):
    if   n.kind == 'empty':  return False
    if   n.kind == 'symbol': return True
    if   n.kind == 'union':  
        return has_nonepsilon(n.children[0]) or has_nonepsilon(n.children[1])
    if   n.kind == 'concat':
        s,t = n.children
        return (has_nonepsilon(s) and not is_empty(t)) or (has_epsilon(s) and has_nonepsilon(t))
    if   n.kind == 'star':   return has_nonepsilon(n.children[0])

def uses_symbol(n, sym):
    if   n.kind == 'empty':  return False
    if   n.kind == 'symbol': return n.value == sym
    if   n.kind == 'union':  
        return uses_symbol(n.children[0], sym) or uses_symbol(n.children[1], sym)
    if   n.kind == 'concat':
        s,t = n.children
        return ((uses_symbol(s,sym) and not is_empty(t))
             or (uses_symbol(t,sym) and not is_empty(s)))
    if   n.kind == 'star':   return uses_symbol(n.children[0], sym)

def is_infinite(n):
    if   n.kind == 'empty':  return False
    if   n.kind == 'symbol': return False
    if   n.kind == 'union':  
        return is_infinite(n.children[0]) or is_infinite(n.children[1])
    if   n.kind == 'concat':
        s,t = n.children
        return ((is_infinite(s) and not is_empty(t))
             or (is_infinite(t) and not is_empty(s)))
    if   n.kind == 'star':
        return has_nonepsilon(n.children[0])


def starts_with(n, sym):
    if   n.kind == 'empty':  return False
    if   n.kind == 'symbol': return n.value == sym
    if   n.kind == 'union':
        return starts_with(n.children[0], sym) or starts_with(n.children[1], sym)
    if   n.kind == 'concat':
        s,t = n.children
        # either some string from s starts with sym and t isn't 0,
        # or s can vanish and some string from t starts with sym
        return ((starts_with(s,sym) and not is_empty(t))
             or (has_epsilon(s) and starts_with(t,sym)))
    if   n.kind == 'star':
        return starts_with(n.children[0], sym)

def ends_with(n, sym):
    if   n.kind == 'empty':  return False
    if   n.kind == 'symbol': return n.value == sym
    if   n.kind == 'union':
        return ends_with(n.children[0], sym) or ends_with(n.children[1], sym)
    if   n.kind == 'concat':
        s,t = n.children
        return ((ends_with(t,sym) and not is_empty(s))
             or (has_epsilon(t) and ends_with(s,sym)))
    if   n.kind == 'star':
        return ends_with(n.children[0], sym)

# ---- other transforms unchanged ----

def simplify(n):
    if n.kind == 'union':
        l = simplify(n.children[0]); r = simplify(n.children[1])
        n = Node('union',[l,r])
    elif n.kind == 'concat':
        l = simplify(n.children[0]); r = simplify(n.children[1])
        n = Node('concat',[l,r])
    elif n.kind == 'star':
        c = simplify(n.children[0])
        n = Node('star',[c])

    # (R*)* ⇒ R*
    if n.kind=='star' and n.children[0].kind=='star':
        return simplify(n.children[0])
    # 0+R ⇒ R, R+0 ⇒ R
    if n.kind=='union':
        l,r = n.children
        if l.kind=='empty': return simplify(r)
        if r.kind=='empty': return simplify(l)
    # 0 dot R ⇒ ∅, R dot 0 ⇒ 0, 0* ⇒ ε etc.
    if n.kind=='concat':
        l,r = n.children
        if l.kind=='empty' or r.kind=='empty':
            return Node('empty')
        if l.kind=='star' and l.children[0].kind=='empty':
            return simplify(r)
        if r.kind=='star' and r.children[0].kind=='empty':
            return simplify(l)
    # (0+R)* ⇒ R*, (R+0)* ⇒ R*
    if n.kind=='star' and n.children[0].kind=='union':
        l,r = n.children[0].children
        if l.kind=='star' and l.children[0].kind=='empty':
            return simplify(Node('star',[r]))
        if r.kind=='star' and r.children[0].kind=='empty':
            return simplify(Node('star',[l]))
    return n

def reverse(n):
    if   n.kind=='empty':   return Node('empty')
    if   n.kind=='symbol':  return Node('symbol',value=n.value)
    if   n.kind=='union':
        l,r = n.children
        return Node('union',[reverse(l),reverse(r)])
    if   n.kind=='concat':
        l,r = n.children
        return Node('concat',[reverse(r),reverse(l)])
    if   n.kind=='star':
        return Node('star',[reverse(n.children[0])])

def not_using(n, sym):
    if n.kind=='empty':   return Node('empty')
    if n.kind=='symbol':
        return Node('empty') if n.value==sym else Node('symbol',value=n.value)
    if n.kind in ('union','concat'):
        l = not_using(n.children[0],sym)
        r = not_using(n.children[1],sym)
        return Node(n.kind,[l,r])
    if n.kind=='star':
        c = not_using(n.children[0],sym)
        return Node('star',[c])

def prefixes(n):
    if n.kind=='empty':   return Node('empty')
    if n.kind=='symbol':
        return Node('union',[Node('symbol',value=n.value),
                             Node('star',[Node('empty')])])
    if n.kind=='union':
        l,r = n.children
        return Node('union',[prefixes(l),prefixes(r)])
    if n.kind=='concat':
        s,t = n.children
        if is_empty(t): return Node('empty')
        return Node('union',[prefixes(s),
                             Node('concat',[s,prefixes(t)])])
    if n.kind=='star':
        s = n.children[0]
        if is_empty(s):
            return Node('star',[Node('empty')])
        return Node('concat',[Node('star',[s]),prefixes(s)])

def bs_for_a(n, sym='a', b_sym='b'):
    if n.kind=='empty':   return Node('empty')
    if n.kind=='symbol':
        if n.value==sym:
            return Node('star',[Node('symbol',value=b_sym)])
        return Node('symbol',value=n.value)
    if n.kind in ('union','concat'):
        l = bs_for_a(n.children[0],sym,b_sym)
        r = bs_for_a(n.children[1],sym,b_sym)
        return Node(n.kind,[l,r])
    if n.kind=='star':
        c = bs_for_a(n.children[0],sym,b_sym)
        return Node('star',[c])

def insert_symbol(n, sym):
    a = Node('symbol',value=sym)
    if n.kind=='empty':
        return Node('empty')

    if n.kind=='symbol':
        b = Node('symbol',value=n.value)
        return Node('union',[
            Node('concat',[a,b]),
            Node('concat',[b,a])
        ])

    if n.kind=='union':
        l,r = n.children
        return Node('union',[
            insert_symbol(l,sym),
            insert_symbol(r,sym)
        ])

    if n.kind=='concat':
        l,r = n.children
        return Node('union',[
            Node('concat',[insert_symbol(l,sym), r]),
            Node('concat',[l, insert_symbol(r,sym)])
        ])

    if n.kind=='star':
        a     = Node('symbol', value=sym)
        child = n.children[0]
        # wrap *around* the entire R* node
        rstar = Node('star', [n])            # (R*)*
        ins   = insert_symbol(child, sym)
        inner = Node('concat', [
            Node('concat',[rstar, ins]),
            rstar
        ])
        return Node('union', [ a, inner ])

    raise ValueError(n.kind)

def strip_symbol(n, sym):
    if n.kind=='empty': return Node('empty')
    if n.kind=='symbol':
        if n.value==sym:
            return Node('star',[Node('empty')])
        return Node('empty')
    if n.kind=='union':
        l,r = n.children
        return Node('union',[strip_symbol(l,sym), strip_symbol(r,sym)])
    if n.kind=='concat':
        s,t = n.children
        s2 = strip_symbol(s,sym)
        t2 = strip_symbol(t,sym)
        if has_epsilon(s):
            return Node('union',[
                Node('concat',[s2, t]),
                t2
            ])
        return Node('concat',[s2,t])
    if n.kind=='star':
        s = n.children[0]
        return Node('concat',[strip_symbol(s,sym), Node('star',[s])])

def parse_args():
    if len(sys.argv)<2:
        print(f"Usage: {sys.argv[0]} --<task> [symbol]",file=sys.stderr)
        sys.exit(1)
    flag = sys.argv[1]
    if not flag.startswith('--'):
        print(f"Expected --<task>, got {flag}",file=sys.stderr)
        sys.exit(1)
    task = flag[2:]
    sym = None
    if task in {'uses','not-using','starts-with','ends-with','insert','strip'}:
        if len(sys.argv)<3:
            print(f"Task '{task}' requires a symbol argument",file=sys.stderr)
            sys.exit(1)
        sym = sys.argv[2]
    return task, sym

def main():
    task, sym = parse_args()
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        tree = parse_postfix(line)
        if   task=='no-op':         out = to_prefix(tree)
        elif task=='simplify':      out = to_prefix(simplify(tree))
        elif task=='empty':         out = 'yes' if is_empty(tree) else 'no'
        elif task=='has-epsilon':   out = 'yes' if has_epsilon(tree) else 'no'
        elif task=='has-nonepsilon':out = 'yes' if has_nonepsilon(tree) else 'no'
        elif task=='uses':          out = 'yes' if uses_symbol(tree,sym) else 'no'
        elif task=='not-using':     out = to_prefix(not_using(tree,sym))
        elif task=='infinite':      out = 'yes' if is_infinite(tree) else 'no'
        elif task=='starts-with':   out = 'yes' if starts_with(tree,sym) else 'no'
        elif task=='reverse':       out = to_prefix(reverse(tree))
        elif task=='ends-with':     out = 'yes' if ends_with(tree,sym) else 'no'
        elif task=='prefixes':      out = to_prefix(prefixes(tree))
        elif task=='bs-for-a':      out = to_prefix(bs_for_a(tree))
        elif task=='insert':        out = to_prefix(insert_symbol(tree,sym))
        elif task=='strip':         out = to_prefix(strip_symbol(tree,sym))
        else:
            print(f"Unknown task '{task}'",file=sys.stderr)
            sys.exit(1)
        print(out)

if __name__ == '__main__':
    main()
