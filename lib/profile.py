import yaml, os, glob
from lib.device import HIDMapperDevice
from lib.mapper import HIDMapper

class HIDMapperProfile (object):

    def __init__ (self, identifier = 'default'):
    
        self._identifier = identifier

        self.name = None
        self.device = None
        self.double_click_timeout = 1000
        self.gestures = None
        self.events = None
        self.mapping = None
        self._gestures_tree = None
    
        # load a profile
        if self._identifier:
            self.load()

    def load (self):
    
        conf = {}
        with open("conf/profiles/%s.yaml" % self._identifier, 'r') as f:
            conf = yaml.safe_load(f)
            
        # Set all properties from the profile
        self.name = conf.get('name')
        
        if conf.get('device'):
            self.device = HIDMapperDevice(conf.get('device'))
        if conf.get('double_click_timeout'):
            self.double_click_timeout = conf.get('double_click_timeout')
        if conf.get('gestures'):
            self.gestures = conf.get('gestures')
        
        # Generate default gestures from the device if needed
        if not self.gestures:
            self.gestures = { k: i+1 for i, k in enumerate(self.get_all_gestures(device = self.device)) }
        
        # Create a dependency tree for all gestures
        self._gestures_tree = self.build_gestures_dependency_tree(self.get_all_gestures())

        if conf.get('events'):
            self.events = conf.get('events')

        # Generate default events if needed
        if not self.events: 
            self.gestures = { k: i+1 for i, k in enumerate(self.get_all_events()) }

        if conf.get('mapping'):
            self.mapping = conf.get('mapping')
        
        # Generate default mapping if needed
        if not self.mapping: 
            self.build_mapping()
            self.save()
        
        return True        
    
    def save (self, save_as = None):
        """
            Save the current profile, optionally with another name
            TODO: Substitute by jinja template
        """
        template = """### AUTOGENERATED PROFILE FILE
# This shouldn't be edited manually

name: {name}

device: {device}

double_click_timeout: {double_click_timeout}

# Each of the gestures included in the profile, and their difficulty
gestures:
{gestures}

# Each of the events that this profile is able to generate, and their weight (usage percentage)
events: 
{events}

# Autogenerated codes to map every event using gestures
mapping:
{mapping}

        """.format(
            name = self.name,
            device = self.device._identifier,
            double_click_timeout = self.double_click_timeout,
            gestures = "\n".join([ "    {}: {}".format(gesture, diff) for gesture, diff in self.gestures.items()]),
            events = "\n".join([ "    {}: {}".format(event, diff) for event, diff in self.events.items()]),
            mapping = "".join([ "    {}: {}".format(event, yaml.dump(gestures)) for event, gestures in self.mapping.items()]),
        )
        name = save_as or self._identifier
        with open("conf/profiles/%s.yaml" % name, 'w') as f:
            f.write(template)

        return True

    def delete (self, filename):
        # TODO
        return True


    def build_mapping (self, method = 'huffman'):
        mapper = HIDMapper()
        
        # Make a mapping for every device, and the join them together, so every code contains gestures 
        # from one device only
        #print("Gestures are", self.gestures)
        #print("Events are", self.events)
        self.mapping = mapper.remap(method, self.gestures, self.events)
        

    def get_all_profiles (self, **attributes):
        """
            Get dictionary with profiles matching the desired attributes
            TODO: Attributes can be:
            - name
            - device
            - gesture
        """
        profiles = {}
        for file_path in glob.glob("conf/profiles/*.yaml"):
            identifier = os.path.splitext(os.path.basename(file_path))[0]
            profiles[identifier] = HIDMapperProfile(identifier)
        return profiles


    def get_all_gestures (self, **attributes):
        """
            Get dictionary with gestures matching the desired attributes
            TODO: Attributes can be:
            - name
            - device
            - gesture
        """
        gestures = {}
        for file_path in glob.glob("gestures/*.yaml"):
            with open(file_path, 'r') as f:
                identifier = os.path.splitext(os.path.basename(file_path))[0]
                gestures.update(yaml.safe_load(f))
        
       
        # Filter by gesture code
        if attributes.get('gesture'):
            if attributes['gesture'] in gestures:
                return { attributes['gesture']: gestures[attributes['gesture']] }
            else:
                raise KeyError("Gesture not found")
        # Filter by device
        if attributes.get('device'):
            device = attributes['device']
            if type(device) is HIDMapperDevice:
                device_gestures = device.gestures.keys()
                filtered_by_device = []
                broken_dep = True
                retries = 100
                while broken_dep and retries > 0:
                    broken_dep = False
                    retries -= 1
                    for i in gestures:
                        if i in device_gestures:
                            filtered_by_device.append(i)
                        elif gestures[i].get('require', []):
                            for j in gestures[i]['require']:
                                if not j in filtered_by_device:
                                    broken_dep = True
                                    break
                            else:
                                filtered_by_device.append(i)
                        else:
                            filtered_by_device.append(i)
                if retries <= 0:
                    print("Probably broken requirements in gestures")
                return { k: v for k, v in gestures.items() if k in filtered_by_device}
            else:
                raise ValueError("get_all_gestures: Not a valid device object given as filter")
        return gestures

    def build_gestures_dependency_tree (self, gestures = None):

        """
            Expands every gesture into a dependency tree
        """
        if not gestures:
            gestures = self.gestures
            
        broken_dep = True
        retries = 100
        dep_tree = {}
        while broken_dep and retries > 0:
            broken_dep = False
            retries -= 1
            for i in gestures:
                if not i in dep_tree:
                    dep_tree[i] = {}
                if gestures[i].get('require', []):
                    for j in gestures[i]['require']:
                        if j not in dep_tree:
                            broken_dep = True
                            continue
                        else:
                            dep_tree[i][j] = dep_tree[j]
                
        if retries <= 0:
            print("Probably broken requirements in gestures")

        return dep_tree

    def get_all_devices (self, **attributes):
        """
            Get dictionary of devices matching the desired attributes
            TODO: Attributes can be:
            - name
            - device
            - gesture
        """
        devices = {}
        for file_path in glob.glob("conf/devices/*.yaml"):
            identifier = os.path.splitext(os.path.basename(file_path))[0]
            devices[identifier] = HIDMapperDevice(identifier)
        return devices

    def reduce_gestures (self, input_gestures, dep_tree = None, output_gestures = None, discarted_gestures = None, level = 0):
        """
            Reduce gestures means, to convert input gestures allowed by a device, into gestures
            allowed by a profile, using gestures_tree to convert them, and giving the higher level
            set of gestures that is equivalent to the input
            1) Get device-filtered input gestures and translate them
            
            Reduce a set of gestures and returns the same set or a smaller one
            Iterate over the dependency tree to substitute input gestures into higher-level ones
            Returns the key for the branch of the tree that includes all the gestures given
        """
        if dep_tree is None:
            dep_tree = self._gestures_tree
        if output_gestures is None:
            output_gestures = set([])
        if discarted_gestures is None:
            discarted_gestures = set([])

        for i in dep_tree:
            #print("Que", i, input_gestures)
            if i in input_gestures:
                #print("Add",i, "to", output_gestures)
                output_gestures.add(i)
            else:
                if dep_tree[i]:
                    if set(input_gestures) >= set(dep_tree[i]):
                        #print("Remove",set(dep_tree[i]), "from", output_gestures)
                        discarted_gestures.update(set(dep_tree[i]))
                        output_gestures.add(i)
                        input_gestures.add(i)
                    self.reduce_gestures(input_gestures, dep_tree[i], output_gestures, discarted_gestures, level+1)
                    
        if level==0:
            #print("Output unfiltered", output_gestures)
            #print("To discard", discarted_gestures)
            output_gestures -= discarted_gestures
            # Get the depth of every gesture in the tree
            gestures_depth = {i:self._get_gesture_depth(i) for i in output_gestures}
            #print("Depths", gestures_depth)
            if gestures_depth:
                max_depth = max(gestures_depth.values())
                output_gestures = set([i for i, depth in gestures_depth.items() if depth == max_depth])
                
        return output_gestures

    def _get_gesture_depth (self, gesture, dep_tree = None):
        depth = 1
        if dep_tree is None:
            dep_tree = self._gestures_tree
        children = dep_tree.get(gesture)
        if children:
            depth += max([self._get_gesture_depth(i, children) for i in children])
        return depth

    def _get_gesture_components (self, gestures):
        """
            Get the basic gestures out of a gesture given
            Basic gestures are the ones that cannot be decomposed
        """
        components = set([])
        dep_tree = self._gestures_tree
        if isinstance(gestures, str):
            gestures = [gestures]
        for gesture in gestures: 
            children = dep_tree.get(gesture)
            if children:
                for i in children:
                    components.update(self._get_gesture_components(i))
            else:
                components.add(gesture)
        
        return components


    def get_gestures_distance (self, gesture1, gesture2):
        """
            Compares two gestures and returns an absolute distance between them
            TODO: 
            1) Get all leaf nodes of both gestures
            2) Compare the affinity between both sets of leaves
            
        """
        c1 = self._get_gesture_components(gesture1)
        c2 = self._get_gesture_components(gesture2)
        #print("Gesture 1: {} -> {}".format(gesture1, ",".join(c1)))
        #print("Gesture 2: {} -> {}".format(gesture2, ",".join(c2)))
        #print("Difference", 1.0*len(c1.symmetric_difference(c2)) / len(c1.union(c2)))
        return 1.0*len(c1.symmetric_difference(c2)) / len(c1.union(c2))
        

    def set_gestures (self, gestures):
        """
            Selects a list of gestures included in the profile
            Gestures are given with a difficulty
        """
        self.gestures = {}


    def set_gesture_difficulty (self, gesture, difficulty):
        """
            Changes difficulty for one of the gestures included in the profile
        """
        self.gestures[gesture] = difficulty
        
