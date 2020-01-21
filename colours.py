import time
import json
import os
from pifx import PIFX

with open('colours.json', 'r') as fp:
        colours = json.load(fp)

lifx_key = os.getenv('LIFX_KEY')
light = PIFX(lifx_key)
# colours_dict = {}


for t, c in colours.items():
    for n, h in c.items():
        os.system('clear')
        print(f'Type: {t }\nColour: {n}')
        light.set_state(color=h, brightness=1.0)
        time.sleep(2)
