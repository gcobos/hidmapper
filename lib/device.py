import yaml
from itertools import chain

class HIDMapperDevice (object):

    def __init__ (self, identifier):
    
        self._identifier = identifier
        
        self.name = None
        self.description = None
        self.author = None
        self.devices = None # Physical devices
        self.gestures = None
        #self.gestures_lut = None
    
        # load the device given
        if self._identifier:
            self.load()

    def load (self):
    
        conf = {}
        with open("conf/devices/%s.yaml" % self._identifier, 'r') as f:
            conf = yaml.safe_load(f)
            
        # Set all properties from the device
        if conf.get('name'):
            self.name = conf.get('name')
        if conf.get('description'):
            self.description = conf.get('description')
        if conf.get('author'):
            self.author = conf.get('author')
        if conf.get('devices'):
            self.devices = conf.get('devices')
        if conf.get('gestures'):
            self.gestures = conf.get('gestures')

        return True        
    
    def save (self, save_as = None):
        """
            Save a device definition, optionally with another name
            TODO: Substitute by jinja template
        """
        template = """### AUTOGENERATED DEVICE DEFINITION

name: {name}
description: {description}
author: {author}

# List of physical devices defined by id
devices: {devices}


# A list of gestures that can be generated by this device, and the set of events that form them
# This gestures can be generated using the event recorder utility.

gestures: {gestures}
        """.format(
            name = self.name,
            description = self.description,
            author = self.author,
            devices = self.devices,
            gestures = self.gestures,
        )
        name = save_as or self._identifier
        with open("conf/devices/%s.yaml" % name, 'w') as f:
            f.write(template)

        return True

    def delete (self, name):
        # TODO
        return True

    def get_events_supported (self):
        """
            Get the list of events that must be captured from the device
            A dictionary with status (pressed/released) for all the events that must be captured
        """
        return tuple(tuple(i.split(':',i.count(':')-1)) for i in set(chain(*self.gestures.values())))

    @property
    def gestures_lut (self):
        """
            Create a gestures lookup-table to make easier to find by their event list
        """
        lut = {}
        for gesture, event_names in self.gestures.items():
            if not event_names:
                raise ValueError("Device gesture doesn't have a list of events")
            if len(event_names) == 1:
                lut[tuple(event_names[0].split(':',event_names[0].count(':')-1))] = gesture
            else:
                parent = lut
                for i in event_names[:-1]:
                    child = {}
                    parent[tuple(i.split(':',i.count(':')-1))] = child
                    parent = child
                child[tuple(event_names[-1].split(':',event_names[-1].count(':')-1))] = gesture
            
        return lut
        
        