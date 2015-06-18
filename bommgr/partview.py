#!/usr/bin/env python3
"""
    This file is part of BOMtools.

    BOMtools is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    BOMTools is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with BOMTools.  If not, see <http://www.gnu.org/licenses/>.

"""

__author__ = 'srodgers'

import configparser
from tkinter import *
from tkinter.ttk import *
from bommdb import *

defaultMpn = 'N/A'
defaultDb= '/etc/bommgr/parts.db'
defaultConfigLocations = ['/etc/bommgr/bommgr.conf','~/.bommgr/bommgr.conf','bommgr.conf']
firstPn = '800000-101'
defaultMID = 'M0000000'

listFrame = None

#
#
#
#
# Classes for TK GUI
#
#
#
#

#
# Full screen App Class. Sets up TK to use full screen
#


class FullScreenApp(object):
    def __init__(self, master, **kwargs):
        self.master=master
        pad=3
        self._geom='200x200+0+0'
        master.geometry("{0}x{1}+0+0".format(
            master.winfo_screenwidth()-pad, master.winfo_screenheight()-pad))
        master.bind('<Escape>',self.toggle_geom)

    def toggle_geom(self,event):
        geom = self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom


#
# Dialog class
#

class Dialog(Toplevel):

    def __init__(self, parent, title = None, xoffset = 50, yoffset = 50):

        Toplevel.__init__(self, parent)
        self.transient(parent)

        if title:
            self.title(title)

        self.parent = parent

        self.result = None

        body = Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)

        self.buttonbox()

        self.grab_set()

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx()+xoffset,
                                  parent.winfo_rooty()+yoffset))

        self.initial_focus.focus_set()

        self.wait_window(self)

    #
    # construction hooks
    #

    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden

        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons

        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)
        w = Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

    #
    # standard button semantics
    #

    def ok(self, event=None):

        if not self.validate():
            self.initial_focus.focus_set() # put focus back
            return

        self.withdraw()
        self.update_idletasks()

        self.apply()

        self.cancel()

    def cancel(self, event=None):

        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks
    #

    def validate(self):

        return 1 # override

    def apply(self):

        pass # override



# List part numbers, descriptions, manufacturers, manufacturer part numbers in a TreeView class with
# Vertical and horizontal scrollbars


def listParts(like=None):
    global DB, defaultMpn, defaultMfgr, listFrame

    if listFrame is not None:
        listFrame.destroy()
        listFrame = None

    listFrame=Frame(root)
    listFrame.pack(side=TOP, fill=BOTH, expand=Y)


    ltree = Treeview(height="26", columns=("Part Number","Description","Manufacturer","Manufacturer Part Number"), selectmode="extended")
    ysb = Scrollbar(orient='vertical', command=ltree.yview)
    xsb = Scrollbar(orient='horizontal', command=ltree.xview)
    ltree.configure(xscroll=xsb.set, yscroll=ysb.set)
    ltree.heading('#1', text='Part Number', anchor=W)
    ltree.heading('#2', text='Description', anchor=W)
    ltree.heading('#3', text='Manufacturer', anchor=W)
    ltree.heading('#4', text='Manufacturer Part Number', anchor=W)
    ltree.column('#1', stretch=NO, minwidth=0, width=200)
    ltree.column('#2', stretch=NO, minwidth=0, width=500)
    ltree.column('#3', stretch=NO, minwidth=0, width=300)
    ltree.column('#4', stretch=YES, minwidth=0, width=300)
    ltree.column('#0', stretch=NO, minwidth=0, width=0) #width 0 for special heading


    parts = DB.get_parts(like)


    for row,(pn,desc) in enumerate(parts):
        mfg = defaultMfgr
        mpn = defaultMpn

        # Try to retrieve manufacturer info
        minfo = DB.lookup_mpn_by_pn(pn)

        if minfo == []: # Use defaults if it no MPN and manufacturer
            minfo =[{'mname':defaultMfgr,'mpn':defaultMpn}]

        for i,item in enumerate(minfo):
            mfg = item['mname']
            mpn = item['mpn']
            if i > 0:
                pn = ''
                desc = ''
            ltree.insert("", "end", "", values=((pn, desc, mfg, mpn)), tags=(row))

    # add tree and scrollbars to frame
    ltree.grid(in_=listFrame, row=0, column=0, sticky=NSEW)
    ysb.grid(in_=listFrame, row=0, column=1, sticky=NS)
    xsb.grid(in_=listFrame, row=1, column=0, sticky=EW)
    # set frame resizing priorities
    listFrame.rowconfigure(0, weight=1)
    listFrame.columnconfigure(0, weight=1)

#
#
#
#
# Main line code
#
#
#
#
#

if __name__ == '__main__':
    conn = None
    cur = None

   ## Customize default configurations to user's home directory

    for i in range(0, len(defaultConfigLocations)):
        defaultConfigLocations[i] = os.path.expanduser(defaultConfigLocations[i])


    # Read the config file
    config = configparser.ConfigParser()

    configLocation = defaultConfigLocations

    config.read(configLocation)

    try:
        general = config['general']
    except KeyError:
        print('Error: no config file found')
        sys.exit(2)

    # Open the database file


    db = os.path.expanduser(general.get('db', defaultDb))

    # Check to see if we can access the database file and that it is writable

    if(os.path.isfile(db) == False):
        print('Error: Database file {} doesn\'t exist'.format(db))
        raise(SystemError)
    if(os.access(db,os.W_OK) == False):
        print('Error: Database file {} is not writable'.format(db))
        raise(SystemError)

    DB = BOMdb(db)

    # Look up default manufacturer

    res = DB.lookup_mfg_by_id(defaultMID)
    if(res is None):
        defaultMfgr = 'Default MFG Error'
    else:
        defaultMfgr = res[0]

    # Set up the TCL add window

    root = Tk()
    app=FullScreenApp(root)
    menubar = Menu(root, tearoff = 0)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    # display the menu
    root.config(menu=menubar)

    viewmenu = Menu(menubar, tearoff = 0)
    viewmenu.add_command(label="List Parts", command=listParts)
    menubar.add_cascade(label="View", menu=viewmenu)


    # display the menu
    root.config(menu=menubar)

    root.mainloop()