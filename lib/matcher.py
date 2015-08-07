import operator
import re
import yaml
import time
import itertools
from difflib import get_close_matches
from profile import HIDMapperProfile

class Matcher (object):

    def __init__ (self, profile):
        self._profile = profile
        self._prefixes = []     # Create an empty list to hold the list of unprocessed prefixes
        self._codes_tree = {}
        self._min_length = 0
        self._max_length = 0
        """
            TODO: 
            Mantener un arbol de busqueda desde cada posible raiz, hasta cada nodo hoja, y buscar por probabilidad
            Para buscar, tengo que tener la probabilidad de cada prefijo, a partir del histograma de eventos y el mapping
            La probabilidad de un prefijo es, la suma de las probabilidades de cada uno de los eventos en que aparece el
            prefijo (en el mapping)

            Reglas: 
            - Los codigos no se solapan nunca
            - Para que un codigo sea confirmado, tiene que ser el primer codigo que encaja y cierra
            - 
        """
        for event_code, seq in self._profile.mapping.items():
            parent = self._codes_tree
            if self._min_length==0 or len(seq) < self._min_length:
                self._min_length=len(seq)
            if len(seq) > self._max_length:
                self._max_length=len(seq)
            for i, gesture in enumerate(seq):
                if not gesture in parent:
                    parent[gesture] = {}
                parent = parent[gesture]
            parent[gesture] = {'event': event_code, 'probability': self._profile.events[event_code]}
        
        #print("Min and max", self._min_length, self._max_length)
        #print("Tree matcher", self._codes_tree)
        
        #print("Tree profile", self._profile._gestures_tree)

    def add_prefix (self, timestamp, set_of_gestures):
        """
            Adds a set of gestures as a candidate to form a gesture code
        """
        #print("{1} (received at {0:2f})".format(timestamp%1000,",".join([i.replace("hand_tap_", "").replace("_vs_thumb", "") for i in set_of_gestures])))
        #print(",".join([i.replace("hand_tap_", "").replace("_vs_thumb", "") for i in set_of_gestures]))
        self._prefixes.append(set_of_gestures)


    def get_matching_codes (self):
        """
            Returns a list of gesture codes that were validated, and empties the queue of prefixes
            up to the end of the last code recognized
        """
        matches = []
        if len(self._prefixes) < self._min_length:
            return matches
        n = self._max_length
        while n >= self._min_length:
            for gestures in itertools.product(*self._prefixes[-n:]):
                #print("!y", gestures)
        
                candidates = get_close_matches(gestures, self._profile.mapping.values(), 1, 1.0)  # Exact match
                event = None
                if candidates:
                    event = [ e for e, g in self._profile.mapping.items() if g==candidates[0]]
                    if event:
                        if not (n < len(self._prefixes) and self._get_partial_candidates(n)):
                            matches.append((candidates[0], event[0]))
                            self._prefixes = []
                            return matches
            n-=1
            
        if len(self._prefixes) > self._max_length and not matches:
            print("Probably wrong code. Clear first prefix")
            for i in [",".join([i.replace("hand_tap_", "").replace("_vs_thumb", "") for i in gestures]) for gestures in self._prefixes]:
                print(i),
            #self._prefixes = self._prefixes[1:]
            self._prefixes = []
        return matches

    def _get_partial_candidates (self, n):
        """
            Get a list of partial candidates (not completed)
        """
        partial = []
        for gestures in itertools.product(*self._prefixes):
            parent = self._codes_tree
            for prefix in gestures:
                if prefix not in parent:
                    continue
                if 'event' in parent[prefix]:
                    continue
                partial = parent[prefix].keys()
                parent = parent[prefix]
        return partial
            

if __name__=='__main__':

    profile = HIDMapperProfile('default')
    matcher = Matcher(profile)

    prefixes = [
        ['g0', 'g3'],
        ['g2', 'g2'],
        ['g3', 'g1'],
        ['g4', 'g1'],
        ['g1', 'g4'],
        ['g0', 'g1'],
        ['g2', 'g0'],
        ['g0', 'g2'],
    ]
    for prefix in prefixes:
        matcher.add_prefix(0, prefix)

    print("Matching codes", matcher.get_matching_codes())
    
    
    