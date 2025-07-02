# Main Deps
import cv2
import mss
import numpy
import pyKey

# Utility Deps
import sys
import yaml
import time
import win32gui
import threading
import tkinter as tk

class config:
    def __init__(self, file):
        self.file = file
        self.updateConfig()

    def updateConfig(self):
        try:
            with open(self.file) as f:
                self.__data = yaml.safe_load(f)
                print("config loaded!")
                return self.__data
        
        except FileNotFoundError:
            print("config file not found!")

    def getConfig(self):
        return self.__data

    def writeConfig(self, data):
        with open(self.file, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)
        
        print("config updated!")

class rectangle:
    def __init__(self, left, top, w, h):
        self.left = left
        self.top = top
        self.w = w
        self.h = h

class screenSelect(tk.Tk):
    def __init__(self):
        super().__init__()

        # Setup screen 'overlay': non-decorated window that covers the entire screen
        self.overrideredirect(True)
        self.attributes('-alpha', 0.3)
        self.attributes('-topmost', True)
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

        # Setup canvas, where we will be able to select the region
        self.canvas = tk.Canvas(self, bg='gray', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.sx = self.sy = self.rid = None

        self.canvas.bind("<ButtonPress-1>", self._onButtonPress)
        self.canvas.bind("<B1-Motion>", self._onMouseDrag)
        self.canvas.bind("<ButtonRelease-1>", self._onButtonRelease)
        self.bind("<Escape>", self._quitWindow)

    def _quitWindow(self, event):
        self.withdraw()
        sys.exit(0)

    def _onButtonPress(self, event):
        self.sx = event.x_root
        self.sy = event.y_root

        if self.rid:
            self.canvas.delete(self.rid)
        
        self.rid = self.canvas.create_rectangle(self.sx, self.sy, self.sx, self.sy, outline='black', width=5)

    def _onMouseDrag(self, event):
        cx, cy = event.x_root, event.y_root
        self.canvas.coords(self.rid, self.sx, self.sy, cx, cy)

    def _onButtonRelease(self, event):
        ex, ey = event.x_root, event.y_root
        left = min(self.sx, ex)
        top = min(self.sy, ey)
        width = abs(ex - self.sx)
        height = abs(ey - self.sy)

        self.result = rectangle(left, top, width, height)
        self.destroy()


img = None
running = True
class BarThread(threading.Thread):
    def __init__(self, sel):
        super().__init__()

        self.sel = sel
        self.isDigging = False
        self.daemon = True
        self._stopEvent = threading.Event()
        
    def _robloxFocused(self):
        try:
            title = win32gui.GetWindowText(win32gui.GetForegroundWindow())
            return "roblox" in title.lower()
        
        except Exception as e:
            print(e)

        return False

    def _getContour(self, data):
        gData = cv2.cvtColor(data, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gData, 45, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            c = max(contours, key = cv2.contourArea)
            return c
        else:
            print("no contours found!")
            return None
        
    def run(self):
        global img
        black = numpy.array([0, 0, 0, 255])
        lwhite = numpy.array([200, 200, 200])
        white = numpy.array([255, 255, 255])
        barColor = numpy.array([25, 25, 25, 255])
        sct = mss.mss()
        while not self._stopEvent.is_set():
            if self._robloxFocused():
                region = { "left": self.sel.left, "top": self.sel.top, "width": self.sel.w, "height": self.sel.h }
                screenshotArr = numpy.array(sct.grab(region), dtype=numpy.uint8)
                img = screenshotArr

                if numpy.array_equal(screenshotArr[0][0], black) == True:
                    self.isDigging = True

                while self.isDigging:
                    if numpy.array_equal(screenshotArr[0][0], black) == False:
                        self.isDigging = False
                        break

                    screenshotArr = numpy.array(sct.grab(region), dtype=numpy.uint8)
                    img = screenshotArr

                    contour = self._getContour(screenshotArr)

                    x,y,w,h = cv2.boundingRect(contour)
                    mx = int(x + (w / 2))
                    my = int(y + (h / 2))
                    mc = screenshotArr[my, mx]

                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    #cv2.rectangle(img, (mx, my), (mx + 1, my + 1), (255, 0, 0), 2)

                    if numpy.array_equal(screenshotArr[my][mx], barColor) == True:
                        pyKey.press(key="SPACEBAR", sec=0)

    def stop(self):
        print("thread stopped!")
        self._stopEvent.set()


class DebugWindowThread(threading.Thread):
    def __init__(self, enabled, wName):
        super().__init__()
        self.wName = wName
        self.enabled = enabled

        self._stopEvent = threading.Event()
        self.daemon = True

    def run(self):
        global running, img
        cv2.namedWindow(self.wName, cv2.WINDOW_AUTOSIZE)

        while not self._stopEvent.is_set():
            if cv2.getWindowProperty(self.wName, cv2.WND_PROP_VISIBLE) < 1:
                running = False
                break

            if self.enabled:
                cv2.setWindowProperty(self.wName, cv2.WND_PROP_TOPMOST, 1)

                if img is not None:
                    cv2.imshow(self.wName, img)
                cv2.waitKey(1)

    def stop(self):
        self._stopEvent.set()

def stopThread(name, thread):
    if thread and thread.is_alive():
        thread.stop()
        thread.join()
        if thread.is_alive():
            print(f"W: Thread '{name}' did NOT stop smoothly")

if __name__ == '__main__':
    conf = config('./config.yml')
    data = conf.getConfig()

    sel = None
    if data['skip_rectangle'] == False:
        app = screenSelect()
        app.mainloop()
        sel = app.result

        data['rectangle']['left'] = sel.left
        data['rectangle']['top'] = sel.top
        data['rectangle']['w'] = sel.w
        data['rectangle']['h'] = sel.h
        conf.writeConfig(data)

    elif data['skip_rectangle']:
        rect = data['rectangle']
        sel = rectangle(rect['left'], rect['top'], rect['w'], rect['h'])

    bT = BarThread(sel)
    bT.start()

    wT = DebugWindowThread(data['debug'], 'autodig Debug Window')
    wT.start()

    try:
        while running:
            time.sleep(0)

    except KeyboardInterrupt:
        print("Closing!")

    except Exception as e:
        print(e)

    finally:
        print("Killing Threads!")
        stopThread("bT", bT)
        stopThread("wT", wT)
        cv2.destroyAllWindows()

        sys.exit(1)
