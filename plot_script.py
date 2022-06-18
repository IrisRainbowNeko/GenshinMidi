import time
from pynput.mouse import Button, Controller
import numpy as np
from pynput import keyboard
import sys

import argparse

note_x=652
note_y=[339, 513, 681, 853, 1024, 1194][::-1]

pos_next=[2453, 768]
pos_prev=[238, 768]

pos_short=[223, 1360]
pos_long=[570, 1360]

flag=[False]

def click_at(x,y):
    mouse.position=(x,y)
    time.sleep(args.delay)
    mouse.click(Button.left)
    time.sleep(args.delay)

def plot(path):
    script=np.load(path)
    tick=-args.offset
    last_state=0

    for i, note in enumerate(script):
        if flag[0]:
            break

        if note[1]-note[0]>args.long:
            if last_state!=1:
                click_at(*pos_long)

            while tick<note[0]:
                tick+=1
                click_at(*pos_next)

            click_at(note_x, note_y[note[2]])

            tick_tmp = tick
            while tick_tmp<note[1]:
                tick_tmp+=1
                click_at(*pos_next)

            click_at(note_x, note_y[note[2]])

            for i in range(tick_tmp-tick):
                click_at(*pos_prev)
            last_state=1
        else:
            if last_state!=0:
                click_at(*pos_short)

            while tick<note[0]:
                tick+=1
                click_at(*pos_next)

            click_at(note_x, note_y[note[2]])

            last_state = 0

def on_press(key):
    if key=='q':
        flag[0]=True
        sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OF Generate')
    parser.add_argument('-p', '--path', default='xg.npy', type=str)
    parser.add_argument('-d', '--delay', default=0.02, type=float)
    parser.add_argument('-l', '--long', default=30, type=int) #长键阈值
    parser.add_argument('--offset', default=9, type=int)
    parser.add_argument('--width', default=2560, type=int)
    parser.add_argument('--height', default=1440, type=int)
    args = parser.parse_args()

    if args.width!=2560 or args.height!=1440:
        factor = (args.width / 2560, args.height / 1440)
        note_x=note_x*factor[0]
        note_y=[item*factor[1] for item in note_y]

        for item in [pos_next, pos_prev, pos_short, pos_long]:
            item[0]*=factor[0]; item[1]*=factor[1]

    print('start in 5s')
    time.sleep(5)
    mouse = Controller()
    key_listener = keyboard.Listener(on_press=on_press)
    key_listener.start()
    plot(args.path)
    print('ok')

