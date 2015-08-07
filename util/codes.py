#!/usr/bin/python

import heapq
import operator
import re

# Difficulty of every gesture, always > 0
DIFFICULTY=[1, 2] #, 3] #, 5, 4, 5, 6]

# Spanish symbols
freq = [   
    (7.46, 'i'), (0.75, 'f'), (14.13, 'e'), ( 9.61, 's'),
    (12.31, 'a'), (0.74, 'x'), (9.28, 'o'), (0.32, 'ch'),
    (3.05, 'u'), (0.69, 'y'), (2.58, 'p'), (2.62, 'm'),
    (4.92, 't'), (7.78, 'n'), (3.94, 'k'), (0.24, '~'),
#    (1.92, 'b'), (6.19, 'r'), (4.84, 'd'), (0.64, 'rr'),
#    (0.94, 'g'), (5.05, 'l') 
]

# English symbols
freq2 = [
    (8.167, 'a'), (1.492, 'b'), (2.782, 'c'), (4.253, 'd'),
    (12.702, 'e'),(2.228, 'f'), (2.015, 'g'), (6.094, 'h'),
    (6.966, 'i'), (0.153, 'j'), (0.747, 'k'), (4.025, 'l'),
    (2.406, 'm'), (6.749, 'n'), (7.507, 'o'), (1.929, 'p'), 
    (0.095, 'q'), (5.987, 'r'), (6.327, 's'), (9.056, 't'), 
    (2.758, 'u'), (1.037, 'v'), (2.365, 'w'), (0.150, 'x'),
    (1.974, 'y'), (0.074, 'z') 
]

class HNode (object):
    def __init__ (self, children):
        self.children = children
    def __repr__ (self):
        return "HNode(%s)" % ",\n".join([str(i) for i in self.children])

def create_tree (freqs):
    q = []
    for i in freqs:
        heapq.heappush(q, i)
    while len(q) > 1:
        children = list(reversed([heapq.heappop(q) for i in range(len(DIFFICULTY)) if len(q)]))
        node = HNode(children)
        heapq.heappush(q, (sum([prob for prob, _ in children]), node))
    return q

# Recursively walk the tree down to the leaves, assigning a code value to each symbol
def walk_tree (nodes, prefix="", code={}):
    for idx1, node in enumerate(reversed(nodes)):
        if hasattr(node[1], 'children'):
            for idx2, child in enumerate(reversed(node[1].children)):
                if len(nodes) > 1:
                    new_prefix = prefix+str(idx1)+str(idx2)
                else:
                    new_prefix = prefix+str(idx2)
                walk_tree([child], new_prefix, code)
        else:
            code[node[1]] = prefix    
    return code

def get_difficulty (codes):
    d = 0
    for code in codes:
        d += sum([DIFFICULTY[int(i)] for i in str(code)])
    return d

htree = create_tree(freq)
#print("HTree",  htree)
nodes = walk_tree(htree)
#print("Nodes", nodes)

# Reorder codes by difficulty
codes = sorted(nodes.values(), key=lambda k: int('1'+k))
#print("Codes", codes)

# Get histogram of assigned codes
code_hist = {}
for i in codes:
    for j in i:
        if j in code_hist:
            code_hist[j] += 1.0/DIFFICULTY[int(j)]
        else:
            code_hist[j] = 1.0/DIFFICULTY[int(j)]
#print("Codes hist", code_hist)

# Reassign codes to maximize ease through all the codes
sorted_code_hist = sorted(code_hist.iteritems(), key=operator.itemgetter(1))
print "Sorted istogram", list(reversed(sorted_code_hist))
lut = {str(i):v[0] for i, v in enumerate(reversed(sorted_code_hist))}
#print "Translation table", lut

replaces = re.compile('|'.join(lut.keys()))
new_codes = []
for code in codes:
    new_codes.append(replaces.sub(lambda m: lut[m.group(0)], code))
#sorted_code_hist_final = sorted(code_hist.iteritems(), key=operator.itemgetter(1))

print "Easier codes", new_codes

for i, code, new_code in zip(sorted(
freq, reverse=True), codes, new_codes):
    print('{}, {:5.2f}, {} after {}'.format(i[1], i[0], code, new_code))
print("Difficulty before {} after {}".format(get_difficulty(codes), get_difficulty(new_codes)))
