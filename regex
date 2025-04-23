#!/usr/bin/env python3
"""
CSCE355-001, Wiley Austin, Final Project, 4/21/2025

Reads postfix regexes from stdin (one per line), and based on the 
command-line option (--task), outputs either "yes"/"no" (for boolean queries) 
or a transformed regex in prefix form.
"""
import sys

# Data structure for regex syntax tree
class Node:
    def __init__(self, kind, children=None, value=None):
        self.kind = kind          # 'union', 'concat', 'star', 'symbol', 'empty'
        self.children = children or []
        self.value = value        # for 'symbol' nodes

# Parsing postfix regex into syntax tree
def parse_postfix(line):
    stack = []
    for c in line.strip():
        if c == '*':  # Kleene star
            child = stack.pop()
            stack.append(Node('star', [child]))
        elif c == '+':  # Union
            r = stack.pop(); l = stack.pop()
            stack.append(Node('union', [l, r]))
        elif c == '.':  # Concatenation
            r = stack.pop(); l = stack.pop()
            stack.append(Node('concat', [l, r]))
        else:  # Atom: empty set or symbol
            if c == '/':
                stack.append(Node('empty'))
            else:
                stack.append(Node('symbol', value=c))
    return stack[0] if stack else None

# Serialization to prefix form
def to_prefix(node):
    if node.kind == 'empty':
        return '/'
    if node.kind == 'symbol':
        return node.value
    if node.kind == 'union':
        return '+' + to_prefix(node.children[0]) + to_prefix(node.children[1])
    if node.kind == 'concat':
        return '.' + to_prefix(node.children[0]) + to_prefix(node.children[1])
    if node.kind == 'star':
        return '*' + to_prefix(node.children[0])
    raise ValueError(f"Unknown node kind: {node.kind}")

# Boolean queries (Q0--Q6)
def is_empty(node):
    if node.kind == 'empty': return True
    if node.kind == 'symbol': return False
    if node.kind == 'union': return is_empty(node.children[0]) and is_empty(node.children[1])
    if node.kind == 'concat': return is_empty(node.children[0]) or is_empty(node.children[1])
    if node.kind == 'star': return False

def has_epsilon(node):
    if node.kind == 'empty': return False
    if node.kind == 'symbol': return False
    if node.kind == 'union': return has_epsilon(node.children[0]) or has_epsilon(node.children[1])
    if node.kind == 'concat':
        return has_epsilon(node.children[0]) and has_epsilon(node.children[1])
    if node.kind == 'star': return True

def has_nonepsilon(node):
    if node.kind == 'empty': return False
    if node.kind == 'symbol': return True
    if node.kind == 'union':
        return has_nonepsilon(node.children[0]) or has_nonepsilon(node.children[1])
    if node.kind == 'concat':
        s, t = node.children
        return (has_nonepsilon(s) and not is_empty(t)) or (has_epsilon(s) and has_nonepsilon(t))
    if node.kind == 'star':
        return has_nonepsilon(node.children[0])

def uses_symbol(node, sym):
    if node.kind == 'empty': return False
    if node.kind == 'symbol': return node.value == sym
    if node.kind == 'union':
        return uses_symbol(node.children[0], sym) or uses_symbol(node.children[1], sym)
    if node.kind == 'concat':
        s, t = node.children
        return (uses_symbol(s, sym) and not is_empty(t)) or (has_epsilon(s) and uses_symbol(t, sym))
    if node.kind == 'star':
        return uses_symbol(node.children[0], sym)

def is_infinite(node):
    if node.kind == 'empty': return False
    if node.kind == 'symbol': return False
    if node.kind == 'union':
        return is_infinite(node.children[0]) or is_infinite(node.children[1])
    if node.kind == 'concat':
        s, t = node.children
        return (is_infinite(s) and not is_empty(t)) or (is_infinite(t) and not is_empty(s))
    if node.kind == 'star':
        return has_nonepsilon(node.children[0])

def starts_with(node, sym):
    if node.kind == 'empty': return False
    if node.kind == 'symbol': return node.value == sym
    if node.kind == 'union':
        return starts_with(node.children[0], sym) or starts_with(node.children[1], sym)
    if node.kind == 'concat':
        s, t = node.children
        return starts_with(s, sym) or (has_epsilon(s) and starts_with(t, sym))
    if node.kind == 'star':
        return starts_with(node.children[0], sym)

def ends_with(node, sym):
    return starts_with(reverse(node), sym)

# Transformations
def simplify(node):
    # simplify children
    if node.kind == 'union' or node.kind == 'concat':
        left = simplify(node.children[0])
        right = simplify(node.children[1])
        node = Node(node.kind, [left, right])
    elif node.kind == 'star':
        child = simplify(node.children[0])
        node = Node('star', [child])
    # apply bottom-up rules
    # 1. s** -> s*
    if node.kind == 'star' and node.children[0].kind == 'star':
        return node.children[0]
    # 2. ∅+s -> s, s+∅ -> s
    if node.kind == 'union':
        l, r = node.children
        if l.kind == 'empty': return r
        if r.kind == 'empty': return l
    # 3. ∅s -> ∅, s∅ -> ∅
    if node.kind == 'concat':
        l, r = node.children
        if l.kind == 'empty' or r.kind == 'empty':
            return Node('empty')
    # 4. ∅*s -> s, s∅* -> s
    if node.kind == 'concat':
        l, r = node.children
        if l.kind == 'star' and l.children[0].kind == 'empty': return r
        if r.kind == 'star' and r.children[0].kind == 'empty': return l
    # 5. (s+∅*)* or (∅*+s)* -> s*
    if node.kind == 'star':
        c = node.children[0]
        if c.kind == 'union':
            l, r = c.children
            if l.kind == 'star' and l.children[0].kind == 'empty':
                return Node('star', [r])
            if r.kind == 'star' and r.children[0].kind == 'empty':
                return Node('star', [l])
    return node

def reverse(node):
    if node.kind == 'empty':
        return Node('empty')
    if node.kind == 'symbol':
        return Node('symbol', value=node.value)
    if node.kind == 'union':
        l, r = node.children
        return Node('union', [reverse(l), reverse(r)])
    if node.kind == 'concat':
        l, r = node.children
        return Node('concat', [reverse(r), reverse(l)])
    if node.kind == 'star':
        return Node('star', [reverse(node.children[0])])

def not_using(node, sym):
    if node.kind == 'empty': return Node('empty')
    if node.kind == 'symbol':
        return Node('empty') if node.value == sym else Node('symbol', value=node.value)
    if node.kind in ('union', 'concat'):
        l = not_using(node.children[0], sym)
        r = not_using(node.children[1], sym)
        return Node(node.kind, [l, r])
    if node.kind == 'star':
        c = not_using(node.children[0], sym)
        return Node('star', [c])

def prefixes(node):
    if node.kind == 'empty':
        return Node('empty')
    if node.kind == 'symbol':
        return Node('union', [Node('symbol', value=node.value), Node('star', [Node('empty')])])
    if node.kind == 'union':
        l, r = node.children
        return Node('union', [prefixes(l), prefixes(r)])
    if node.kind == 'concat':
        s, t = node.children
        if is_empty(t):
            return Node('empty')
        s_p = prefixes(s)
        t_p = prefixes(t)
        return Node('union', [s_p, Node('concat', [s, t_p])])
    if node.kind == 'star':
        s = node.children[0]
        if is_empty(s):
            return Node('star', [Node('empty')])
        return Node('concat', [Node('star', [s]), prefixes(s)])

def bs_for_a(node, sym='a', b_sym='b'):
    if node.kind == 'empty': return Node('empty')
    if node.kind == 'symbol':
        if node.value == sym:
            return Node('star', [Node('symbol', value=b_sym)])
        return Node('symbol', value=node.value)
    if node.kind in ('union', 'concat'):
        l = bs_for_a(node.children[0], sym, b_sym)
        r = bs_for_a(node.children[1], sym, b_sym)
        return Node(node.kind, [l, r])
    if node.kind == 'star':
        c = bs_for_a(node.children[0], sym, b_sym)
        return Node('star', [c])

def insert_symbol(node, sym):
    if node.kind == 'empty': return Node('empty')
    if node.kind == 'symbol':
        c = node.value
        ac = Node('concat', [Node('symbol', value=sym), Node('symbol', value=c)])
        ca = Node('concat', [Node('symbol', value=c), Node('symbol', value=sym)])
        return Node('union', [ac, ca])
    if node.kind == 'union':
        l, r = node.children
        return Node('union', [insert_symbol(l, sym), insert_symbol(r, sym)])
    if node.kind == 'concat':
        s, t = node.children
        s_p = insert_symbol(s, sym)
        t_p = insert_symbol(t, sym)
        part1 = Node('concat', [s_p, t])
        part2 = Node('concat', [s, t_p])
        part3 = Node('concat', [Node('concat', [s, Node('symbol', value=sym)]), t])
        return Node('union', [part1, Node('union', [part2, part3])])
    if node.kind == 'star':
        s = node.children[0]
        s_p = insert_symbol(s, sym)
        return Node('concat', [Node('concat', [Node('star', [s]), s_p]), Node('star', [s])])

def strip_symbol(node, sym):
    if node.kind == 'empty': return Node('empty')
    if node.kind == 'symbol':
        if node.value == sym:
            return Node('star', [Node('empty')])
        return Node('empty')
    if node.kind == 'union':
        l, r = node.children
        return Node('union', [strip_symbol(l, sym), strip_symbol(r, sym)])
    if node.kind == 'concat':
        s, t = node.children
        s_p = strip_symbol(s, sym)
        t_p = strip_symbol(t, sym)
        if has_epsilon(s):
            return Node('union', [Node('concat', [s_p, t]), t_p])
        return Node('concat', [s_p, t])
    if node.kind == 'star':
        s = node.children[0]
        return Node('concat', [strip_symbol(s, sym), Node('star', [s])])

# Command-line interface and main loop
def parse_args():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} --<task> [symbol]", file=sys.stderr)
        sys.exit(1)
    flag = sys.argv[1]
    if not flag.startswith('--'):
        print(f"Expected --<task>, got {flag}", file=sys.stderr)
        sys.exit(1)
    task = flag[2:]
    sym = None
    # tasks requiring a symbol argument
    symbol_tasks = {'uses', 'not-using', 'starts-with', 'ends-with', 'insert', 'strip'}
    if task in symbol_tasks:
        if len(sys.argv) < 3:
            print(f"Task '{task}' requires a symbol argument", file=sys.stderr)
            sys.exit(1)
        sym = sys.argv[2]
    return task, sym


def main():
    task, sym = parse_args()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        tree = parse_postfix(line)
        if task == 'no-op':
            out = to_prefix(tree)
        elif task == 'simplify':
            out = to_prefix(simplify(tree))
        elif task == 'empty':
            out = 'yes' if is_empty(tree) else 'no'
        elif task == 'has-epsilon':
            out = 'yes' if has_epsilon(tree) else 'no'
        elif task == 'has-nonepsilon':
            out = 'yes' if has_nonepsilon(tree) else 'no'
        elif task == 'uses':
            out = 'yes' if uses_symbol(tree, sym) else 'no'
        elif task == 'not-using':
            out = to_prefix(not_using(tree, sym))
        elif task == 'infinite':
            out = 'yes' if is_infinite(tree) else 'no'
        elif task == 'starts-with':
            out = 'yes' if starts_with(tree, sym) else 'no'
        elif task == 'reverse':
            out = to_prefix(reverse(tree))
        elif task == 'ends-with':
            out = 'yes' if ends_with(tree, sym) else 'no'
        elif task == 'prefixes':
            out = to_prefix(prefixes(tree))
        elif task == 'bs-for-a':
            out = to_prefix(bs_for_a(tree))
        elif task == 'insert':
            out = to_prefix(insert_symbol(tree, sym))
        elif task == 'strip':
            out = to_prefix(strip_symbol(tree, sym))
        else:
            print(f"Unknown task '{task}'", file=sys.stderr)
            sys.exit(1)
        print(out)

if __name__ == '__main__':
    main()