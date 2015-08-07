#!/usr/bin/python2

from evdev import ecodes

def list_event_names (codetype = None, event_code = 0):
    events = []
    if codetype is not None:
        if isinstance(codetype,list):
            codetypes = codetype
        else:
            codetypes = [codetype]
    else:
        codetypes = ecodes.EV
    for ev_type in codetypes:
        if not ev_type in ecodes.bytype:
            continue
        for ev_code in ecodes.bytype[ev_type]:
            if event_code and event_code != ev_code:
                continue
            names = ecodes.bytype[ev_type][ev_code]
            if not isinstance(names, list):
                names = [names]
            for name in names:
                key = "{},{}".format(ev_type, ev_code)
                value = "{}:{}".format(ecodes.EV[ev_type], name)
                if isinstance(value, list):
                    events.append((value[0], key))
                else:
                    events.append((value, key))

    return events

if __name__=='__main__':
    #print ecodes.keys
    for name in list_event_names(): #ecodes.EV_KEY):
        print('    "'+name[0]+'": 0.0')