import heapq
import operator
import re, math
import itertools

class HIDMNode (object):
    def __init__ (self, children):
        self.children = children
    def __repr__ (self):
        return "HIDMNode(%s)" % ",\n".join([str(i) for i in self.children])

class HIDMapper (object):

    def __init__ (self):
        pass
    
    def remap (self, method, gestures, events):
        if method == 'huffman':
            return self.remap_huffman(gestures, events)
        elif method == 'in_order':
            return self.remap_in_order(gestures, events)      # Events are set in a tree in_order. So every prefix makes a partition
        else:
            return self.remap_histogram(gestures, events)     # Sorted by histogram usage of the events

    def remap_in_order (self, gestures, events):
        events = sorted([(k, v) for k, v in events.items()])
        gestures = [g[1] for g in sorted([(v, k) for k, v in gestures.items()])]

        # Construct the mapping table
        mapping = {}
        codes = itertools.product(
            gestures, 
            repeat = int(math.ceil(math.log(len(events), len(gestures))))
        )
        for event, _ in events:
            code = codes.next()
            mapping[event] = list(code)
        
        #print "Mapping", mapping
        return mapping
            
    def remap_histogram (self, gestures, events):
        events = sorted([(v, k) for k, v in events.items()], reverse=True)
        gestures = [g[1] for g in sorted([(v, k) for k, v in gestures.items()])]

        # Construct the mapping table
        mapping = {}
        codes = itertools.product(
            gestures, 
            repeat = int(math.ceil(math.log(len(events), len(gestures))))
        )
        for _, event in events:
            code = codes.next()
            mapping[event] = list(code)
        
        #print "Mapping", mapping
        return mapping

    def remap_huffman (self, gestures, events):
        """
            Returns a new mapping from gestures (input) into events (output), based on the difficulty of every gesture,
            and the histogram of usage for every event
            gestures: a dictionary containing every gesture input selected in a profile, and its difficulty where 
                difficulty must be > 0
            events: A dictionary with every event that the profile is able to generate, and its aproximate usage
        """
        event_histogram = [(v, k) for k, v in events.items()]
        gestures_difficulty = sorted([(v, k) for k, v in gestures.items()])

        #print("Gestures difficulty", gestures_difficulty)
        #print("Events histogram", event_histogram)

        htree = self.create_tree(len(gestures_difficulty), event_histogram)
        #print("Tree?", htree)
        nodes = self.walk_tree(htree)
        
        #print("Nodes", nodes)
        
        # Reorder codes by complexity
        codes = sorted(
            nodes.values(), 
            key = lambda k: [len(k)]+k
        )
        #print("Ordered codes", codes)
        
        # Get histogram of assigned codes
        code_hist = {}
        for i in codes:
            for j in i:
                if j in code_hist:
                    code_hist[j] += 1.0
                else:
                    code_hist[j] = 1.0
        #print("prefix hist", code_hist)
        #print("Difficulties", gestures_difficulty)
        
        # Reassign codes to maximize ease through all the codes
        sorted_code_hist = sorted(code_hist.iteritems(), key=operator.itemgetter(1), reverse = True)
        #print("Sorted histogram", list(sorted_code_hist))
        
        # Reorder difficulties according to the code histogram
        #gestures_difficulty = sorted([d,  for d in enumerate(gestures_difficulty)])
        
        lut = {code[0]:gestures_difficulty[i][1] for i, code in enumerate(sorted_code_hist)}
        #print("Translation table", lut)
        
        easier_codes = []
        for code in codes:
            easier_codes.append([lut[prefix] for prefix in code])
        #print("Easier  codes", easier_codes)

        #for i, code, easier_code in zip(sorted(event_histogram, reverse=True), codes, easier_codes):
        #    print('{}, {:5.2f}, {} after {}'.format(i[1], i[0], code, easier_code))
        
        # Construct the mapping table
        mapping = {}
        for event, code in zip(sorted(event_histogram, reverse = True), easier_codes):
            mapping[event[1]] = code
        
        #print "Mapping", mapping
        return mapping

    def create_tree (self, num_gestures, freqs):
        q = []
        for i in freqs:
            heapq.heappush(q, i)
        while len(q) > 1:
            children = list(([heapq.heappop(q) for i in range(num_gestures) if len(q)]))
            node = HIDMNode(children)
            heapq.heappush(q, (sum([prob for prob, _ in children]), node))
        return q


    def walk_tree (self, nodes, prefix=[], code={}):
        for idx1, node in enumerate((nodes)):
            if hasattr(node[1], 'children'):
                for idx2, child in enumerate((node[1].children)):
                    if len(nodes) > 1:
                        new_prefix = prefix+[idx1,idx2]
                    else:
                        new_prefix = prefix+[idx2]
                    self.walk_tree([child], new_prefix, code)
            else:
                code[node[1]] = prefix    
        return code

if __name__=='__main__':

    mapper = HIDMapper()
    """
    difficulties = {
        'index': 0.1,
        'middle': 0.2,
        'ring': 0.3,
        'pinky': 0.6,
        'index_middle': 0.7,
        'middle_ring': 0.8,
    }
    freq = {
        'a': 8.167, 'b': 1.492, 'c': 2.782, 'd': 4.253,
        'e': 12.702,'f': 2.228, 'g': 2.015, 'h': 6.094,
        'i': 6.966, 'j': 0.153, 'k': 0.747, 'l': 4.025,
        'm': 2.406, 'n': 6.749, 'o': 7.507, 'p': 1.929, 
        'q': 0.095, 'r': 5.987, 's': 6.327, 't': 9.056, 
        'u': 2.758, 'v': 1.037, 'w': 2.365, 'x': 0.150,
        'y': 1.974, 'z': 0.074 
    }
    """
    difficulties = {'dif': 0.7, 'mid': 0.5, 'eas': 0.2}
    freq = {
        'i': 7.46, 'f': 0.75, 'e': 14.13,'s':  9.61,
        'a': 12.31,'x': 0.74, 'o': 9.28, 'ch': 0.32,
#        'u': 3.05, 'y': 0.69, 'p': 2.58, 'm': 2.62,
#        't': 4.92, 'n': 7.78, 'k': 3.94, '~': 0.24,
#        'b': 1.92, 'r': 6.19, 'd': 4.84, 'rr': 0.64,
#        'g': 0.94, 'l': 5.05 
    }
    
    mapper.remap(difficulties, freq)
    
    