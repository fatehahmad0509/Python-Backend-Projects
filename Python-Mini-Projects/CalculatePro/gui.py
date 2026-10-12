import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import sys
from main import calculate

if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(0)

BTN   = 76
GAP   = 10
PAD   = 16
COLS  = 4
SCALE = 3
BG    = "#1c1c1e"

COLORS = {
    "num":  ((51,51,51),   (74,74,74)),
    "op":   ((255,159,10), (255,179,64)),
    "func": ((99,99,102),  (124,124,128)),
    "eq":   ((255,159,10), (255,179,64)),
    "zero": ((51,51,51),   (74,74,74)),
}

LAYOUT = [
    [("AC","func"),("+/-","func"),("%","func"),("÷","op")],
    [("7","num"),  ("8","num"),   ("9","num"), ("×","op")],
    [("4","num"),  ("5","num"),   ("6","num"), ("−","op")],
    [("1","num"),  ("2","num"),   ("3","num"), ("+","op")],
    [("0","zero"),               (".","num"),  ("=","eq")],
]

OP_MAP = {"÷": "D", "×": "M", "−": "S", "+": "A"}

def load_font(px):
    for path in [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try: return ImageFont.truetype(path, px)
        except: pass
    return ImageFont.load_default()

def make_img(w, h, color, text, left_align=False):
    sw, sh = w*SCALE, h*SCALE
    im = Image.new("RGBA", (sw, sh), (0,0,0,0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle([0,0,sw-1,sh-1], radius=sh//2, fill=color+(255,))
    fn = load_font(26*SCALE)
    bb = dr.textbbox((0,0), text, font=fn)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    tx = (sh//2 - tw//2) if left_align else (sw//2 - tw//2)
    ty = sh//2 - th//2 - bb[1]
    dr.text((tx, ty), text, font=fn, fill=(255,255,255,255))
    return ImageTk.PhotoImage(im.resize((w,h), Image.LANCZOS))

class Calc:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("CalculatePro")
        self.win.resizable(False, False)
        self.win.configure(bg=BG)
        self.number1  = None
        self.pending_op = None
        self.disp     = tk.StringVar(value="0")
        self.small    = tk.StringVar(value="")
        self.fresh    = True
        self._imgs    = {}
        self._build()

    def _build(self):
        GW = COLS*BTN + (COLS-1)*GAP
        GH = 5*BTN + 4*GAP
        W  = GW + 2*PAD
        H  = 160 + GH + 2*PAD
        self.win.geometry(f"{W}x{H}")

        tk.Label(self.win, textvariable=self.small,
                 font=("Helvetica",15), fg="#8e8e93", bg=BG,
                 anchor="e").place(x=PAD, y=18, width=GW)
        tk.Label(self.win, textvariable=self.disp,
                 font=("Helvetica",58,"bold"), fg="#fff", bg=BG,
                 anchor="e").place(x=PAD, y=44, width=GW)
        tk.Frame(self.win, bg="#3a3a3c", height=1).place(x=0, y=158, width=W)

        for row in LAYOUT:
            for lbl, bt in row:
                z = (bt == "zero")
                w = BTN*2+GAP if z else BTN
                n, h = COLORS[bt]
                self._imgs[lbl+"_n"] = make_img(w, BTN, n, lbl, z)
                self._imgs[lbl+"_h"] = make_img(w, BTN, h, lbl, z)

        col_x = [PAD + i*(BTN+GAP) for i in range(COLS)]
        top   = 160 + PAD

        for ri, row in enumerate(LAYOUT):
            ci = 0
            for lbl, bt in row:
                z  = (bt == "zero")
                bw = BTN*2+GAP if z else BTN
                x  = col_x[ci]
                y  = top + ri*(BTN+GAP)

                lb = tk.Label(self.win, image=self._imgs[lbl+"_n"],
                              bg=BG, cursor="hand2")
                lb.place(x=x, y=y, width=bw, height=BTN)

                def bind(w, t):
                    w.bind("<Enter>",    lambda e, _w=w, _t=t: _w.config(image=self._imgs[_t+"_h"]))
                    w.bind("<Leave>",    lambda e, _w=w, _t=t: _w.config(image=self._imgs[_t+"_n"]))
                    w.bind("<Button-1>", lambda e, _t=t: self.press(_t))
                bind(lb, lbl)

                ci += 2 if z else 1

    def press(self, t):
        if t == "AC":
            self.number1 = None
            self.pending_op = None
            self.disp.set("0")
            self.small.set("")
            self.fresh = True

        elif t == "+/-":
            try: self.disp.set(self._f(-float(self.disp.get())))
            except: pass

        elif t == "%":
            try: self.disp.set(self._f(float(self.disp.get()) / 100))
            except: pass

        elif t in OP_MAP:
            self.number1 = float(self.disp.get())
            self.pending_op = OP_MAP[t]
            self.small.set(self.disp.get() + " " + t)
            self.fresh = True

        elif t == "=":
            if self.number1 is not None and self.pending_op is not None:
                number2 = float(self.disp.get())
                result  = calculate(self.number1, number2, self.pending_op)
                self.small.set(
                    self.small.get().replace("D","÷").replace("M","×")
                    .replace("S","−").replace("A","+")
                )
                self.small.set(self.small.get() + " " + self.disp.get() + " =")
                if isinstance(result, str):
                    self.disp.set(result)
                else:
                    self.disp.set(self._f(result))
                self.number1    = None
                self.pending_op = None
                self.fresh      = True

        elif t == ".":
            if self.fresh:
                self.disp.set("0.")
                self.fresh = False
            elif "." not in self.disp.get():
                self.disp.set(self.disp.get() + ".")

        else:
            cur = self.disp.get()
            if self.fresh or cur == "0":
                self.disp.set(t)
                self.fresh = False
            elif len(cur.replace(".", "").replace("-", "")) < 9:
                self.disp.set(cur + t)

    @staticmethod
    def _f(v):
        return str(int(v)) if v == int(v) else f"{v:.8g}"

    def run(self):
        self.win.mainloop()

if __name__ == "__main__":
    Calc().run()