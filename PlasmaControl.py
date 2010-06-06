from Tkinter import *
import time
from serial import Serial

COM_LEFT = 'COM1'
COM_RIGHT = 'COM2'

COMMANDS = {}
COMMANDS['Power'] = dict([('On','PON'), ('Off','POF')])
COMMANDS['Source'] = dict([('Video','IIS:VID'), ('PC VGA','IIS:PC1')])
COMMANDS['Mode'] = dict([('Normal','DAM:NORM'), ('Zoom','DAM:ZOOM'), 
                         ('Full','DAM:FULL'), ('Justified','DAM:JUST'), ('Auto','DAM:SELF')]) 

class FakePort(object):
    def __init__(self, *args, **kwargs):
        self.port = kwargs.get('port', 'NoName')
        self.timeout = kwargs.get('timeout', 1)
        self.modes = set(['PON','POF','IIS:VID','IIS:PC1','DAM:NORM','DAM:ZOOM','DAM:FULL','DAM:JUST','DAM:SELF'])
        self.current = {'PO':'POF','DA':'DAM:FULL','II':'IIS:PC1'}
        self.buf = ""

    def write(self, data):
        print(self.port + ': ' + repr(data))
        mode = data[1:-1]
        if mode in self.modes:
            if mode != self.current[mode[:2]]:
                self.buf += '\x02' + mode[:3] +'\x03'
                self.current[mode[:2]] = mode
            else:
                pass
        else:
            self.buf += '\x02ER401\x03'
                
    def read(self, *args, **kwargs):
        if self.buf:
            val = self.buf[0]
            self.buf = self.buf[1:]
        else:
            time.sleep(self.timeout)
            val = ''
        return val
        
# For testing
PORT = FakePort
#PORT = Serial

class Panel(object):
    def __init__(self, port_name, status_var):
        self.port_name = port_name
        self.status_var = status_var
        self.status = {'Power':'On', 'Source':'PC VGA', 'Mode':'Full'}
        self.port = None
    def port_open(self):
        if self.port:
            return True
        else:
            try:
                # Open Serial Port
                self.port = PORT(port=self.port_name, timeout=1)
                return True
            except:
                self.status_var.set('Error Opening\n' + self.port_name)
                return False
    def update_status(self):
        var = ''
        for x in ['Power','Source','Mode']:
            var += x + ': ' + self.status[x] + '\n'
        self.status_var.set(var)
    def send(self, cat, val):
        self._send(cat, val)
        if cat=='Power' and val=='On':
            self._send('Source',self.status['Source'])
            self._send('Mode',self.status['Mode'])

    def _send(self, cat, val):
        if self.port_open():
            self.port.write('\x02' + COMMANDS[cat][val] + '\x03')
            
            byte = ''
            buffer = ''
            while True:
                byte = self.port.read()
                buffer += byte
                if byte in ('\x03',''):
                    break
            if buffer == '\x02' + COMMANDS[cat][val][:3] + '\x03':
                self.status[cat] = val
                self.update_status()
            elif byte == '' and buffer == '':
                #no reply if status already set
                pass
            else:
                var = 'Error Setting\n' + cat + ' to ' + val
                self.status_var.set(var)

class Dispatcher(object):
    def __init__(self, left_panel, right_panel, panel_selection):
        self.left_panel = left_panel
        self.right_panel = right_panel
        self.panel_selection = panel_selection
    def send(self, cat, val):
        sel = self.panel_selection.get()
        if sel in ('left','both'):
            self.left_panel.send(cat, val)
        if sel in ('right','both'):
            self.right_panel.send(cat, val)
    def make_sender(self, cat, val):
        def sender(*args, **kwargs):
            self.send(cat, val)
        return sender

def make_frame(master, cat, dispatcher):
    frame = LabelFrame(master, text=cat, padx = 5, pady = 5)
    for val in COMMANDS[cat]:
        Button(frame, text=val, command=dispatcher.make_sender(cat, val)).pack(side=LEFT)
    return frame


root = Tk()
root.title('Plasma Control Console')

PANEL_SELECTION = StringVar(root, value='both')
STATUS_LEFT = StringVar(root)
STATUS_RIGHT = StringVar(root)

panel_left = Panel(COM_LEFT, STATUS_LEFT)
panel_right = Panel(COM_RIGHT, STATUS_RIGHT)
dispatcher = Dispatcher(panel_left, panel_right, PANEL_SELECTION)

Label(root, text="Plasma Panel Control Console").grid(row=0, column=0, columnspan=4)
Message(root, textvariable=STATUS_LEFT).grid(row=1, column=0, sticky=E+W+N+S)
frame = Frame(root, pady = 5)
Radiobutton(frame, text="<- Left Panel", variable=PANEL_SELECTION, value='left', indicatoron=False).pack(fill=BOTH,expand=True, anchor=W)
Radiobutton(frame, text="<- Both Panels ->", variable=PANEL_SELECTION, value='both', indicatoron=False).pack(fill=BOTH,expand=True, anchor=W)
Radiobutton(frame, text="   Right Panel ->", variable=PANEL_SELECTION, value='right', indicatoron=False).pack(fill=BOTH,expand=True, anchor=W)
frame.grid(row=1, column=1, columnspan=2)
Message(root, textvariable=STATUS_RIGHT).grid(row=1, column=3, sticky=E+W+N+S)
make_frame(root, 'Power', dispatcher).grid(row=2, column=0, columnspan=2, sticky=W)
make_frame(root, 'Source', dispatcher).grid(row=2, column=2, columnspan=2,sticky=E)
make_frame(root, 'Mode', dispatcher).grid(row=3, column=0, columnspan=4)    
root.grid_columnconfigure(0, weight=2, minsize=100)
root.grid_columnconfigure(1, weight=1, minsize=50)
root.grid_columnconfigure(2, weight=1, minsize=50)
root.grid_columnconfigure(3, weight=2, minsize=100)
 
mainloop()
