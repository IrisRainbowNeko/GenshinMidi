import time
from pynput.mouse import Button, Controller
import numpy as np
from pynput import keyboard
import sys

import argparse

note_x=652
note_y=[339, 513, 681, 853, 1024, 1194][::-1]

pos_next=(2453, 768)

flag=[False]

def click_at(x,y):
    mouse.position=(x,y)
    time.sleep(args.delay)
    mouse.click(Button.left)
    time.sleep(args.delay)

def plot(path):
    script=np.load(path)
    tick=-args.offset

    for i, note in enumerate(script):
        if flag[0]:
            break

        print(i)
        while tick<note[0]:
            tick+=1
            click_at(*pos_next)

        click_at(note_x, note_y[note[2]])

def on_press(key):
    if key=='q':
        flag[0]=True
        sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='OF Generate')
    parser.add_argument('-p', '--path', default='xg.npy', type=str)
    parser.add_argument('-d', '--delay', default=0.02, type=float)
    parser.add_argument('--offset', default=9, type=int)
    args = parser.parse_args()

    print('start in 5s')
    time.sleep(5)
    mouse = Controller()
    key_listener = keyboard.Listener(on_press=on_press)
    key_listener.start()
    plot(args.path)
    print('ok')

