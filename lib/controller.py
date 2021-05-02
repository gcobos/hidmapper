import sys, re, time, traceback
from gevent import spawn, sleep
from collections import deque
from gevent.select import select
from evdev import InputDevice, list_devices, categorize, UInput, ecodes
from lib.device import HIDMapperDevice
from lib.profile import HIDMapperProfile
from lib.matcher import Matcher

class HIDMapperController (object):

    def __init__ (self):
        self._profile = None
        self._running = False
        self._input_devices = None
        self._file_descriptors = None
        self._allowed_event_types = None
        self._event_status = None
        self._gesture_codes = deque()
        self._last_queued = None
        self._virtual_input = None
        self._matcher = None

    @property
    def profile (self, profile_obj):
        self._profile=profile_obj

    @profile.setter
    def profile (self, profile_obj):
        self._profile=profile_obj

    def _prepare_device (self):
        #print("device: %s" % self._profile.device.name)
        self._event_status = {key:0 for key in self._profile.device.get_events_supported()}
        #print("Events supported",self._event_status)
        self._allowed_event_types = set([getattr(ecodes,i[-1].split(':')[0]) for i in self._event_status])
        self._input_devices = map(InputDevice, self._profile.device.devices)
        self._file_descriptors = { dev.fd: i for i, dev in enumerate(self._input_devices) }
        
        print("Mappings for '" + self._profile.name+"' " + '-'*30)
        for k,v in sorted(self._profile.mapping.items()):
            print(str(k.replace("EV_KEY:KEY_","").replace("ENTER","<-'").replace("APOSTROPHE","'").replace(",","")).lower().rjust(20)+" as "+(', '.join(v)).replace("r_hand_tap_", "").replace("_vs_thumb", ""))
            
        # Prepare virtual device for event injection
        capabilities = {}
        for ev_chain in self._profile.mapping:
            for k in re.split('[+,]', ev_chain):
                et, ec = k.split(':', 1)
                etype = ecodes.ecodes[et]
                if etype in capabilities:
                    capabilities[etype].append(ecodes.ecodes[ec])
                else:
                    capabilities[etype] = [ ecodes.ecodes[ec] ]
        #print("Capabilities", capabilities)
        self._virtual_input = UInput(events = capabilities)

        # Prepare matcher
        self._matcher = Matcher(self._profile)


    def start (self):
        """
            Start capturing from the device(s) of the current profile
        """
        self._prepare_device()
        try:
            for dev in self._input_devices: dev.grab()
        except Exception as e:
            print("Unable to grab device", e)
        self._running = True
        
        spawn(self._capture_loop)
        spawn(self._process_loop)
        sleep(0)

        
    def stop (self):
        """
            Stop capturing and release the device(s)
        """
        self._running = False 
        try:
            for dev in self._input_devices: dev.ungrab()
        except:
            pass
    
        if self._virtual_input:
            self._virtual_input.close()


    def _capture_loop (self):
        try:
            devices = {dev.fd : dev for dev in self._input_devices}
            while self._running:
                r,_,_ = select(devices, [], [], timeout=self._profile.double_click_timeout/1000.0)
                for fd in r:
                    for event in devices[fd].read():
                        #print("Lo que", event)
                        if self.is_allowed_event(event, fd):
                            event_code = self.get_event_code(event, fd)
                            if event.value == 1:
                                #print("Pressed!", event_code)
                                self.set_event_status(event_code, 1)
                                #print("Statuses", self._event_status)
                                self._store_gestures()
                                                                
                            elif event.value == 0:
                                #print("Released!", event_code)
                                self.set_event_status(event_code, 0)
                                #print("Statuses", self._event_status)
                                #self._store_gestures()
                            else:
                                print("What is this?",event)
        except:
            self._running = False
            traceback.print_exc()


    def _store_gestures (self):
        """
            Fetch current gestures, select those allowed in the profile and store them in the queue of gesture codes
        """

        filtered_gestures = set([
            gesture for gesture in self.get_current_gestures() if gesture in self._profile.gestures
        ])
        if not filtered_gestures:
            return

        if filtered_gestures != self._last_queued:
            distance = 1.0
            if self._last_queued:
                distance = self._profile.get_gestures_distance(filtered_gestures, self._last_queued)
                #print("Distance is", distance)
            self._last_queued = filtered_gestures

            if distance <= 0.5:
                try:
                    timestamp, last_queued = self._gesture_codes.pop()
                    #print("Time interval", time.time() - timestamp)
                    if time.time() - timestamp > self._profile.double_click_timeout/6000.0:
                        self._gesture_codes.append((timestamp, last_queued))
                except IndexError:
                    pass #print("Empty queue!")

        self._gesture_codes.append((time.time(), filtered_gestures))


    def _process_loop (self):
        """
            TODO: Process the queue of gestures and inject remapped events
        """
        while self._running:
            try:
                timestamp, prefixes = self._gesture_codes.pop()
                reduced = self._profile.reduce_gestures(prefixes)
                self._matcher.add_prefix(timestamp, reduced)

                # With every possible option if any...
                for candidate, output_event in self._matcher.get_matching_codes():
                    #print("Candidate(s)",candidate, "would generate events(s)", output_event)
                    self._inject_event(output_event)
            except IndexError:
                pass
            except:
                print("Processing error")
                traceback.print_exc()

            sleep(self._profile.double_click_timeout/5000.0)


    def _inject_event (self, event_codes):
        """
            Insert one or several events in the virtual input
            event_code is a string, normally, that contains an event, like 'EV_KEY:KEY_A'
            event_code can have a sequence of events, like 'EV_KEY:KEY_A,EV_KEY:KEY_B,EV_KEY:KEY_C'
            event_code can contain chained events, to make combination of keys, like: 'EV_KEY:KEY_LEFTCTRL+EV_KEY:KEY_C'
        """
        if isinstance(event_codes, str):
            event_codes = event_codes.split(",")
        for event_code_combo in event_codes:
            for operation in [1, 0]:
                for event_code in event_code_combo.split("+"):
                    if isinstance(event_code, str):
                        event_code = event_code.split(':')
                    if len(event_code) == 1 and ':' in event_code[0]:
                        event_code = event_code[0].split(':')
                    etype = ecodes.ecodes[event_code[0]]
                    ecode = ecodes.ecodes[event_code[1]]
                    
                    #names = ecodes.bytype[etype][ecode]
                    #if not isinstance(names, list):
                    #    names = [names]
                    #print("Inject event {} {}".format(names[0], "pressed" if operation==1 else "released"))
                    
                    self._virtual_input.write(etype, ecode, operation)  # pressed
        self._virtual_input.syn()

    def find_event_keys (self, event_code, where):
        """
            param event_code: Event code to search (as a tuple)
            param where: A dictionary whose keys are event codes
            Search and returns a list of matching keys for an event code, in the dictionary or list 'where'
        """
        matches = []
        event_keys = [event_code]
        if len(event_code) < 2:
            for dev_num, _ in enumerate(self._file_descriptors):
                event_keys.append(('DEV_%d' % dev_num, event_code[0]))
        else:
            event_keys.append((event_code[1],))
        for ev in event_keys:
            if ev in where:
                matches.append(ev)
        return matches


    def is_allowed_event (self, event, fd = None):
        """
            Decide if the controller must capture this event or not 
        """
        if event.type in self._allowed_event_types:
            event_code = self.get_event_code(event)
            if fd is not None:
                key1 = ('DEV_%d' % self._file_descriptors[fd], event_code[0])
                key2 = event_code
                return key1 in self._event_status or key2 in self._event_status
            else:
                if not event_code in self._event_status:
                    for dev_num, _ in enumerate(self._file_descriptors):
                        key = ('DEV_%d' % dev_num, event_code[0])
                        if key in self._event_status:
                            return True
                else:
                    return True
        
        return False


    def get_event_code (self, event, fd = None):
        """
            Returns the event code (type+code), prefixed by the device if 'fd' is present
        """
        name = ecodes.bytype[event.type][event.code]
        #print("Event code from", event, "is", name)
        if isinstance(name, list):
            name = name[0]
        event_code = "%s:%s" % (ecodes.EV[event.type], name)
        if fd is not None:
            return ('DEV_%d' % self._file_descriptors[fd], event_code)
        return (event_code, )

    
    def get_current_gestures (self, where_to_find = None, current_gestures = None):
        """
            return: A set of gestures activated at this moment
        """
        if where_to_find is None:
            where_to_find = self._profile.device.gestures_lut

        if current_gestures is None:
            current_gestures = set([])
        for ev in self._event_status:
            if self._event_status[ev]:  # Is pressed?
                for found in self.find_event_keys(ev, where_to_find):
                    result = where_to_find[found]
                    if isinstance(result, dict):
                        self.get_current_gestures(result, current_gestures)
                    else:
                        current_gestures.add(result)
            
        return current_gestures
                            

    def set_event_status (self, event_code, status):
        """
            Sets the status for every event that matches the event_code
        """
        for ev_key in self.find_event_keys(event_code, self._event_status):
            self._event_status[ev_key] = status    


    def __del__ (self):
        print("Stopping capturer")
        if self._running:
            self.stop()

