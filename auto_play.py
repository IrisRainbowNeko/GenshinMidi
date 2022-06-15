import win32api, win32con, win32gui, win32ui
import numpy as np
import cv2
import time
from pynput.keyboard import Controller as c_key
import threading

import argparse

def match_img(img, target, type=cv2.TM_SQDIFF_NORMED, mask=None):
    h, w = target.shape[:2]
    res = cv2.matchTemplate(img, target, type, mask=mask)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if type in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        return (
            *min_loc,
            min_loc[0] + w,
            min_loc[1] + h,
            min_loc[0] + w // 2,
            min_loc[1] + h // 2,
            min_val,
        )
    else:
        return (
            *max_loc,
            max_loc[0] + w,
            max_loc[1] + h,
            max_loc[0] + w // 2,
            max_loc[1] + h // 2,
            max_val,
        )

class Player:
    def __init__(self, key_delay=0.3, width=2560, height=1440):
        self.WINDOW_NAME = '原神'
        self.DEFAULT_MONITOR_WIDTH=width
        self.DEFAULT_MONITOR_HEIGHT=height

        self.det_areas=[
            [820,505,820+130,505+130],
            [950,570,950+130,570+130],
            [1095,600,1095+130,600+130],

            [1330,600,1330+130,600+130],
            [1470,570,1470+130,570+130],
            [1605,505,1605+130,505+130],
        ]

        self.tmp_short=cv2.imread('imgs/short.png', cv2.IMREAD_COLOR)
        self.tmp_long=cv2.imread('imgs/long.png', cv2.IMREAD_COLOR)

        self.scale_images()

        self.mask_short = ((self.tmp_short>1).any(axis=-1).astype(np.uint8)*255)[:,:,None].repeat(3, axis=2)
        self.mask_long = ((self.tmp_long>1).any(axis=-1).astype(np.uint8)*255)[:,:,None].repeat(3, axis=2)

        self.note_th = 0.07
        self.note_th_long = 0.04
        self.note_key=['a','s','d', 'j', 'k', 'l']
        self.key_delay=key_delay
        self.long_interval=0.1
        self.short_interval=0.1

    def scale_images(self):
        if self.DEFAULT_MONITOR_WIDTH==2560 and self.DEFAULT_MONITOR_HEIGHT==1440:
            return
        factor=(self.DEFAULT_MONITOR_WIDTH/2560, self.DEFAULT_MONITOR_HEIGHT/1440)
        self.tmp_short=cv2.resize(self.tmp_short,(int(self.tmp_short.shape[0]*factor[0]), int(self.tmp_short.shape[1]*factor[1])))
        self.tmp_long=cv2.resize(self.tmp_long,(int(self.tmp_long.shape[0]*factor[0]), int(self.tmp_long.shape[1]*factor[1])))

        for i, item in enumerate(self.det_areas):
            self.det_areas[i]=[int(item[0]*factor[0]), int(item[1]*factor[1]), int(item[2]*factor[0]), int(item[3]*factor[1])]


    def pre_start(self):
        self.hwnd = win32gui.FindWindow(None, self.WINDOW_NAME)
        self.genshin_window_rect = win32gui.GetWindowRect(self.hwnd)
        self.keyboard = c_key()

        self.flag=False

    def key_loop(self, short_queue, long_queue):
        long_state = np.zeros((6,), dtype=np.uint8)
        long_time = [0,0,0,0,0,0]
        short_time = [0,0,0,0,0,0]

        # 按音符
        while True:
            time.sleep(0.01)
            now = time.time()
            if self.flag:
                break
            if len(short_queue) > 0 and now - short_queue[0][1] >= self.key_delay:
                note = short_queue.pop(0)
                if note[1] - short_time[note[0]] > self.short_interval:
                    self.keyboard.press(self.note_key[note[0]])
                    self.keyboard.release(self.note_key[note[0]])
                    short_time[note[0]] = note[1]

            if len(long_queue) > 0 and now - long_queue[0][1] >= self.key_delay:
                note = long_queue.pop(0)
                if note[1]-long_time[note[0]] > self.long_interval:
                    if long_state[note[0]]:
                        self.keyboard.release(self.note_key[note[0]])
                    else:
                        self.keyboard.press(self.note_key[note[0]])
                    long_state[note[0]] = ~long_state[note[0]]
                    long_time[note[0]]=note[1]

    def start(self):
        short_queue = []
        long_queue = []

        threading.Thread(target=self.key_loop, args=(short_queue, long_queue)).start()

        while True:
            #识别音符
            image=self.cap()
            note_short, note_long = self.check_note(image)
            for note in note_short:
                short_queue.append((note, time.time()))
            for note in note_long:
                long_queue.append((note, time.time()))

            if win32api.GetKeyState(ord('Q'))<0:
                self.flag=True
                break

    def check_note(self, image):
        det_imgs=[image[area[1]:area[3], area[0]:area[2], :] for area in self.det_areas]
        dets_short=[match_img(imgs, self.tmp_short, mask=self.mask_short) for imgs in det_imgs]
        dets_long=[match_img(imgs, self.tmp_long, mask=self.mask_long) for imgs in det_imgs]
        #print([x[-1] for x in dets_short], [x[-1] for x in dets_long])

        note_short = [i for i,item in enumerate(dets_short) if item[-1]<self.note_th]
        note_long = [i for i,item in enumerate(dets_long) if item[-1]<self.note_th_long]
        if len(note_short)>0 or len(note_long)>0:
            print([x[-1] for x in dets_short], [x[-1] for x in dets_long])

        note_long = [x for i,x in enumerate(note_long) if not ((x in note_short) and (dets_short[i][-1]<dets_long[i][-1]))]
        note_short = [x for i,x in enumerate(note_short) if not ((x in note_long) and (dets_long[i][-1]<dets_short[i][-1]))]

        return note_short, note_long

    def cap(self, region=None):
        if region is not None:
            left, top, w, h = region
            # w = x2 - left + 1
            # h = y2 - top + 1
        else:
            w = self.DEFAULT_MONITOR_WIDTH  # set this
            h = self.DEFAULT_MONITOR_HEIGHT  # set this
            left = 0
            top = 0

        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()

        dataBitMap.CreateCompatibleBitmap(dcObj, w, h)

        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (w, h), dcObj, (left, top), win32con.SRCCOPY)
        # dataBitMap.SaveBitmapFile(cDC, bmpfilenamename)
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype="uint8")
        img.shape = (h, w, 4)

        # Free Resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        return cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--delay', default=0.32, type=float)
    parser.add_argument('--width', default=2560, type=int)
    parser.add_argument('--height', default=1440, type=int)
    args = parser.parse_args()

    #image=cv2.imread('imgs/sc2.bmp', cv2.IMREAD_COLOR)
    player=Player(key_delay=args.delay, width=args.width, height=args.height)
    #player.check_note(image)
    while win32api.GetKeyState(ord('T'))>=0:
        pass
    player.pre_start()
    player.start()