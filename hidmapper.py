#!/usr/bin/python3
import gevent, sys, traceback

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from lib.config import HIDMapperConfig
from lib.profile import HIDMapperProfile
from lib.controller import HIDMapperController


"""
    Show the gui or command line options with ---help

    --profile [name] Changes to another profile
"""

from gevent import monkey
monkey.patch_all(select=True)


class HIDMapperGUI (object):

    def __init__ (self):

        self.config = HIDMapperConfig()
        self.profile = HIDMapperProfile(self.config.default_profile)
        self.controller = HIDMapperController()
        self.controller.profile = self.profile
        #self.profile.build_mapping()
        #self.profile.save()
        self.controller.start()
        #self.profile.get_all_gestures()
        
        builder = Gtk.Builder()
        builder.add_from_file("gui/main.glade")
        
        #### Fill the main TreeView profile listing
        self.liststore = Gtk.ListStore(str, str)
        selected_row = 0 
        for row, profile in enumerate(self._get_profiles_list()):
            if profile[0] == self.config.default_profile:
                selected_row = row
            self.liststore.append(profile)
        profile_selection_treeview = builder.get_object("profile-selection-treeview")
        profile_selection_treeview.set_model(self.liststore)
        profile_selection_treeview.set_cursor(selected_row)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", renderer, text=1)
        profile_selection_treeview.append_column(column)
        
        select = profile_selection_treeview.get_selection()
        select.connect("changed", self.on_tree_selection_changed)

        
        #### Fill the default profile combobox
        default_profile_list_container = builder.get_object("default-profile-list-container")
        default_profile_combobox = Gtk.ComboBoxText.new()
        for p_id, p_name in self._get_profiles_list():
            default_profile_combobox.append(p_id, p_name)
        default_profile_combobox.connect("changed", self.on_default_profile_changed)
        default_profile_combobox.set_active_id(self.config.default_profile)
        default_profile_list_container.pack_start(default_profile_combobox, False, False, True)

        handlers_dict = { 
            "on_delete_window" : Gtk.main_quit,
            "on_button_pressed" : self.on_button_pressed,
        }
        builder.connect_signals(handlers_dict)

        self._main_window = builder.get_object("main")
        self._main_window.show_all()

    def on_tree_selection_changed (self, selection):
        model, treeiter = selection.get_selected()
        if treeiter != None:
            self.profile = HIDMapperProfile(model[treeiter][0])
            self.controller.stop()
            self.controller.profile = self.profile
            self.controller.start()

    def on_default_profile_changed(self, combo):
        default = combo.get_active_id()
        if default != None:
            print("Selected: profile=%s" % default)
            self.config.default_profile = default
            self.config.save()

    def on_button_pressed(self, button):
        
        print("Hello World!")

    def _get_profiles_list (self):
        return sorted([(k, v.name or k.capitalize()) for k, v in self.profile.get_all_profiles().items()], key = lambda x: x[1])

    def run (self):

        Gtk.main()
        self.controller.stop()

def idle():
    try:
        gevent.sleep(0.01)
    except:
        Gtk.main_quit()
        gevent.hub.MAIN.throw(traceback.print_exc())
    return True

if __name__=="__main__":
    GObject.idle_add(idle)
    HIDMapperGUI().run()

