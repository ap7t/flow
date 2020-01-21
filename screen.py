import tkinter as tk
import time 

class Screen(tk.Tk):
    def __init__(self, colour, period=None):
        tk.Tk.__init__(self)
        self.period = period
        self.colour = colour    
        self.attributes('-fullscreen', True)
        self.configure(bg=colour)
        # self.mainloop()
        # self.geometry('400x400')

    def change_colour(self, colour):
        self['bg'] = colour

if __name__ == '__main__':
    s = Screen('#006400')
    # inp = input('colour: ')
    # s.change_colour(inp)

    s.mainloop()
