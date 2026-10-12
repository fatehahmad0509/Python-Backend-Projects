import sys
if __name__ == "__main__":
    import tkinter as _tk
    from tkinter import messagebox as _mb
    _root = _tk.Tk(); _root.withdraw()
    _mb.showerror("NF Air", "Please run the application through main.py")
    _root.destroy()
    sys.exit(0)

import threading
import tkinter as tk
from tkinter import ttk, messagebox
import main
import random
from datetime import datetime, timedelta

BG_DARK    = "#0d1f3c"
BG_MID     = "#0a2a52"
BG_CARD    = "#102a50"
BG_CARD2   = "#0e2446"
BTN_BLUE   = "#1a6eb5"
BTN_HOVER  = "#2389e0"
WHITE      = "#f5f9ff"
ICE        = "#c8e6f7"
GOLD       = "#e8b84b"
MUTED      = "#7aadcc"
RED_ERR    = "#e24b4a"
GLASS_BD   = "#1e4d80"
GREEN_FILL = "#1a2e1a"
GREEN_BD   = "#2a5a2a"
GREEN_TXT  = "#5aaa5a"

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUB   = ("Segoe UI", 11)
FONT_LABEL = ("Segoe UI", 9,  "bold")
FONT_INPUT = ("Segoe UI", 11)
FONT_BTN   = ("Segoe UI", 12, "bold")
FONT_SMALL = ("Segoe UI", 10)
FONT_FN    = ("Segoe UI", 13, "bold")
FONT_TIME  = ("Segoe UI", 20, "bold")
FONT_PRICE = ("Segoe UI", 15, "bold")
FONT_BPVAL = ("Segoe UI", 14, "bold")
FONT_BPLBL = ("Segoe UI", 9)

ADULT_PRICE    = 300
CHILD_PRICE    = 200
BAG_FREE_KG    = 3
BAG_EUR_PER_KG = 5

def rand_flight():
    return "NF" + str(random.randint(1000000, 9999999))

def rand_gate():
    return random.choice(["A","B","C","D","F"]) + str(random.randint(10, 99))

def make_flights(departure, arrival, n=2):
    result = []
    destination = main.enterroute(departure, arrival)
    for _ in range(n):
        fn   = rand_flight()
        info = main.flightinfos(destination, fn)
        result.append(info)
    return result

def calc_baggage_surcharge(total_weight_kg):
    if total_weight_kg <= BAG_FREE_KG:
        return 0
    return (total_weight_kg - BAG_FREE_KG) * BAG_EUR_PER_KG

def send_ticket_bg(to_email, flightnumber, destination, dep_hour, arr_hour,
                   seats, payment, baggage_weight):
    def _run():
        try:
            main.send_welcome_email(
                to_email        = to_email,
                flightnumber    = flightnumber,
                flightdestination = destination,
                departurehour   = dep_hour,
                arrivehour      = arr_hour,
                seat            = seats,
                payment         = payment,
                baggageweight   = baggage_weight,
            )
        except Exception as ex:
            print(f"[NF Air] Ticket mail error: {ex}")
    threading.Thread(target=_run, daemon=True).start()

def send_checkin_bg(passenger_list):
    def _run():
        try:
            main.checkin(passenger_list)
        except Exception as ex:
            print(f"[NF Air] Check-in mail error: {ex}")
    threading.Thread(target=_run, daemon=True).start()

def scrollable(parent, bg=BG_DARK):
    outer  = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, bd=0)
    sb     = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview,
                            style="NF.Vertical.TScrollbar")
    inner  = tk.Frame(canvas, bg=bg)
    iid    = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(iid, width=e.width))
    canvas.configure(yscrollcommand=sb.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    return outer, canvas, inner

def nfair_header(parent):
    f = tk.Frame(parent, bg=BG_DARK)
    tk.Label(f, text=" NF ", font=("Segoe UI",18,"bold"), bg=BTN_BLUE, fg=WHITE, pady=3).pack(side="left")
    tk.Label(f, text=" AIR", font=("Segoe UI",18,"bold"), bg=BG_DARK, fg=GOLD).pack(side="left", padx=(4,0))
    return f

def mk_entry(parent, textvariable=None, **kw):
    e = tk.Entry(parent, textvariable=textvariable, font=FONT_INPUT,
                 bg="#0e2a50", fg=WHITE, insertbackground=WHITE,
                 relief="flat", bd=0, highlightbackground=GLASS_BD, highlightthickness=1, **kw)
    e.bind("<FocusIn>",  lambda ev: e.config(highlightbackground=BTN_HOVER))
    e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=GLASS_BD))
    return e

def lbl(parent, text, font=FONT_SUB, fg=WHITE, bg=BG_CARD, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)

def mk_btn(parent, text, command, bg=BTN_BLUE, fg=WHITE, pady=12, **kw):
    b = tk.Button(parent, text=text, command=command, font=FONT_BTN, bg=bg, fg=fg,
                  activebackground=BTN_HOVER, activeforeground=WHITE,
                  relief="flat", bd=0, cursor="hand2", pady=pady, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=BTN_HOVER))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    return b

def ghost_btn(parent, text, command):
    b = tk.Button(parent, text=text, command=command, font=("Segoe UI",10),
                  bg=BG_DARK, fg=MUTED, activebackground=BG_MID, activeforeground=WHITE,
                  relief="flat", bd=0, cursor="hand2", pady=8)
    b.bind("<Enter>", lambda e: b.config(fg=WHITE))
    b.bind("<Leave>", lambda e: b.config(fg=MUTED))
    return b

def mk_sep(parent, bg=GLASS_BD):
    return tk.Frame(parent, bg=bg, height=1)

def mk_card(parent, padx=18, pady=14, bg=BG_CARD):
    outer = tk.Frame(parent, bg=bg, highlightbackground=GLASS_BD, highlightthickness=1)
    inner = tk.Frame(outer, bg=bg, padx=padx, pady=pady)
    inner.pack(fill="x")
    return outer, inner

def counter_row(parent, text, var, bg=BG_CARD, callback=None, min_val=0, max_val=99):
    f = tk.Frame(parent, bg=bg)
    lbl(f, text, font=FONT_SUB, fg=WHITE, bg=bg).pack(side="left")
    def dec():
        if var.get() > min_val: var.set(var.get()-1)
        if callback: callback()
    def inc():
        if var.get() < max_val: var.set(var.get()+1)
        if callback: callback()
    tk.Button(f, text="−", font=("Segoe UI",13,"bold"), bg=BG_MID, fg=WHITE,
              activebackground=GLASS_BD, relief="flat", bd=0, width=2,
              cursor="hand2", command=dec).pack(side="right", padx=(4,0))
    tk.Label(f, textvariable=var, font=("Segoe UI",13,"bold"), bg=bg, fg=WHITE, width=3).pack(side="right")
    tk.Button(f, text="+", font=("Segoe UI",13,"bold"), bg=BG_MID, fg=WHITE,
              activebackground=GLASS_BD, relief="flat", bd=0, width=2,
              cursor="hand2", command=inc).pack(side="right")
    return f

class Screen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_DARK)
        self.app = app
    def on_show(self): pass

class ScreenMenu(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        center = tk.Frame(self, bg=BG_DARK)
        center.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85)
        lf = tk.Frame(center, bg=BG_DARK); lf.pack(pady=(0,28))
        tk.Label(lf, text=" NF ", font=("Segoe UI",32,"bold"), bg=BTN_BLUE, fg=WHITE, pady=4).pack(side="left")
        tk.Label(lf, text=" AIR", font=("Segoe UI",32,"bold"), bg=BG_DARK, fg=GOLD).pack(side="left", padx=(6,0))
        lbl(center,"Welcome aboard",font=("Segoe UI",11),fg=MUTED,bg=BG_DARK).pack(pady=(0,4))
        lbl(center,"Your journey starts here",font=("Segoe UI",13,"bold"),fg=WHITE,bg=BG_DARK).pack(pady=(0,28))
        bf = tk.Frame(center,bg=BG_DARK); bf.pack(fill="x")
        bf.columnconfigure(0,weight=1); bf.columnconfigure(1,weight=1)
        self._choice(bf,"BUY TICKET", lambda: app.show("ScreenRoute"), 0)
        self._choice(bf,"CHECK IN",   lambda: app.show("ScreenCheckinStart"), 1)

    def _choice(self, parent, text, cmd, col):
        c = tk.Frame(parent,bg=BG_CARD,highlightbackground=GLASS_BD,highlightthickness=1)
        c.grid(row=0,column=col,padx=8,sticky="nsew",ipady=14)
        icon = "🎫" if "TICKET" in text else "✅"
        tk.Label(c,text=icon,font=("Segoe UI Emoji",28),bg=BG_CARD,fg=WHITE).pack(pady=(16,6))
        tk.Label(c,text=text,font=("Segoe UI",12,"bold"),bg=BG_CARD,fg=WHITE).pack(pady=(0,16))
        for w in [c]+list(c.winfo_children()): w.bind("<Button-1>", lambda e,f=cmd: f())
        c.bind("<Enter>", lambda e,f=c: [w.config(bg=BG_MID) for w in [f]+list(f.winfo_children())])
        c.bind("<Leave>", lambda e,f=c: [w.config(bg=BG_CARD) for w in [f]+list(f.winfo_children())])

class ScreenRoute(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        outer = tk.Frame(self,bg=BG_DARK)
        outer.place(relx=0.5,rely=0.06,anchor="n",relwidth=0.88)
        nfair_header(outer).pack(anchor="w",pady=(0,16))
        lbl(outer,"Plan Your Route",font=FONT_TITLE,fg=WHITE,bg=BG_DARK).pack(anchor="w")
        lbl(outer,"Enter departure and arrival cities",fg=MUTED,bg=BG_DARK).pack(anchor="w",pady=(2,14))
        co,ci = mk_card(outer,padx=20,pady=20); co.pack(fill="x")
        row = tk.Frame(ci,bg=BG_CARD); row.pack(fill="x")
        row.columnconfigure(0,weight=1); row.columnconfigure(2,weight=1)
        lf2 = tk.Frame(row,bg=BG_CARD); lf2.grid(row=0,column=0,sticky="ew",padx=(0,6))
        lbl(lf2,"DEPARTURE CITY",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(0,4))
        self.dep_e = mk_entry(lf2,textvariable=app.departure)
        self.dep_e.pack(fill="x",ipady=9)
        lbl(lf2,"e.g.  Istanbul (IST)",font=("Segoe UI",9),fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(2,0))
        mf = tk.Frame(row,bg=BG_CARD); mf.grid(row=0,column=1,padx=4,pady=(14,0))
        tk.Button(mf,text="⇄",font=("Segoe UI",13,"bold"),bg=BG_MID,fg=GOLD,relief="flat",bd=0,
                  cursor="hand2",padx=8,pady=8,command=self._swap).pack()
        rf2 = tk.Frame(row,bg=BG_CARD); rf2.grid(row=0,column=2,sticky="ew",padx=(6,0))
        lbl(rf2,"ARRIVAL CITY",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(0,4))
        self.arr_e = mk_entry(rf2,textvariable=app.arrival)
        self.arr_e.pack(fill="x",ipady=9)
        lbl(rf2,"e.g.  Berlin (BER)",font=("Segoe UI",9),fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(2,0))
        self.err_lbl = tk.Label(ci,text="",font=FONT_SMALL,fg=RED_ERR,bg=BG_CARD)
        self.err_lbl.pack(anchor="w",pady=(10,0))
        mk_btn(ci,"SEARCH FLIGHTS  →",self._search,pady=13).pack(fill="x",pady=(14,4))
        ghost_btn(ci,"← Back to Menu", lambda: app.show("ScreenMenu")).pack()

    def _swap(self):
        d,a = self.app.departure.get(), self.app.arrival.get()
        self.app.departure.set(a); self.app.arrival.set(d)

    def _search(self):
        dep = self.app.departure.get().strip()
        arr = self.app.arrival.get().strip()
        if not dep or not arr:
            self.err_lbl.config(text="Please enter both cities."); return
        self.err_lbl.config(text="")
        self.app.destination = main.enterroute(dep, arr)
        self.app.flights = make_flights(dep, arr, 2)
        self.app.show("ScreenFlights")

class ScreenFlights(Screen):
    def __init__(self, parent, app): super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        app = self.app
        outer = tk.Frame(self,bg=BG_DARK)
        outer.place(relx=0.5,rely=0.05,anchor="n",relwidth=0.9,relheight=0.93)
        nfair_header(outer).pack(anchor="w",pady=(0,14))
        lbl(outer,"Available Flights",font=FONT_TITLE,fg=WHITE,bg=BG_DARK).pack(anchor="w")
        lbl(outer,app.destination,fg=MUTED,bg=BG_DARK).pack(anchor="w",pady=(2,14))
        so,_,inner = scrollable(outer); so.pack(fill="both",expand=True)
        for i,f in enumerate(app.flights): self._card(inner,f,i)
        ghost_btn(inner,"← Change Route", lambda: app.show("ScreenRoute")).pack(pady=8)

    def _card(self, parent, f, idx):
        app=self.app; dep_city=app.departure.get(); arr_city=app.arrival.get()
        c = tk.Frame(parent,bg=BG_CARD,highlightbackground=GLASS_BD,highlightthickness=1)
        c.pack(fill="x",pady=6)
        ci = tk.Frame(c,bg=BG_CARD,padx=18,pady=16); ci.pack(fill="x")
        badge = tk.Frame(ci,bg="#1a3a6a",highlightbackground="#2389e0",highlightthickness=1)
        badge.pack(anchor="w",pady=(0,10))
        tk.Label(badge,text=f"  {f['flightnumber']}  ",font=FONT_FN,bg="#1a3a6a",fg=ICE,pady=4).pack()
        rr = tk.Frame(ci,bg=BG_CARD); rr.pack(fill="x"); rr.columnconfigure(1,weight=1)
        df = tk.Frame(rr,bg=BG_CARD); df.grid(row=0,column=0,sticky="w")
        tk.Label(df,text=f["departurehour"],font=FONT_TIME,bg=BG_CARD,fg=WHITE).pack(anchor="w")
        tk.Label(df,text=dep_city,font=("Segoe UI",9),bg=BG_CARD,fg=MUTED).pack(anchor="w")
        mf = tk.Frame(rr,bg=BG_CARD); mf.grid(row=0,column=1,padx=10,sticky="ew")
        tk.Label(mf,text="- - - ✈ - - -",font=("Segoe UI",10),bg=BG_CARD,fg=GOLD).pack()
        tk.Label(mf,text="~3h 00m",font=("Segoe UI",9),bg=BG_CARD,fg=MUTED).pack()
        af = tk.Frame(rr,bg=BG_CARD); af.grid(row=0,column=2,sticky="e")
        tk.Label(af,text=f["arrivalhour"],font=FONT_TIME,bg=BG_CARD,fg=WHITE).pack(anchor="e")
        tk.Label(af,text=arr_city,font=("Segoe UI",9),bg=BG_CARD,fg=MUTED).pack(anchor="e")
        tk.Label(af,text=f"{ADULT_PRICE} EUR",font=FONT_PRICE,bg=BG_CARD,fg=GOLD).pack(anchor="e",pady=(6,0))
        tk.Label(af,text="per adult",font=("Segoe UI",9),bg=BG_CARD,fg=MUTED).pack(anchor="e")
        mk_sep(ci).pack(fill="x",pady=10)
        def select(i=idx):
            fl = app.flights[i]
            app.selected_flight = fl
            app.gate = rand_gate()
            app.adult_count.set(1); app.child_count.set(0)
            app.selected_seats = []
            app.show("ScreenBuy")
        mk_btn(ci,"BUY TICKET  →",select,pady=10).pack(fill="x")

class ScreenBuy(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.bag_count_e    = None
        self.bag_weight_e   = None
        self.err_lbl        = None
        self.total_frame    = None
        self.seat_canvas    = None
        self.seat_info_lbl  = None
        self.bag_details    = None
        self.bag_toggle_btn = None

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        app = self.app; f = app.selected_flight
        outer = tk.Frame(self,bg=BG_DARK)
        outer.place(relx=0.5,rely=0.04,anchor="n",relwidth=0.92,relheight=0.95)
        nfair_header(outer).pack(anchor="w",pady=(0,10))
        lbl(outer,"Book Your Seats",font=FONT_TITLE,fg=WHITE,bg=BG_DARK).pack(anchor="w")
        lbl(outer,"Select passengers & seats",fg=MUTED,bg=BG_DARK).pack(anchor="w",pady=(2,8))
        so,_,inner = scrollable(outer); so.pack(fill="both",expand=True)

        fco,fci = mk_card(inner); fco.pack(fill="x",pady=(0,8))
        badge = tk.Frame(fci,bg="#1a3a6a",highlightbackground="#2389e0",highlightthickness=1)
        badge.pack(anchor="w",pady=(0,8))
        tk.Label(badge,text=f"  {f['flightnumber']}  ",font=FONT_FN,bg="#1a3a6a",fg=ICE,pady=4).pack()
        ri = tk.Frame(fci,bg=BG_CARD); ri.pack(fill="x")
        tk.Label(ri,text=f["departurehour"],font=("Segoe UI",17,"bold"),bg=BG_CARD,fg=WHITE).pack(side="left")
        tk.Label(ri,text="  →  ",font=("Segoe UI",13),bg=BG_CARD,fg=GOLD).pack(side="left")
        tk.Label(ri,text=f["arrivalhour"],font=("Segoe UI",17,"bold"),bg=BG_CARD,fg=WHITE).pack(side="left")
        tk.Label(fci,text=f"Gate: {app.gate}   |   {app.destination}",
                 font=("Segoe UI",9),bg=BG_CARD,fg=MUTED).pack(anchor="w",pady=(4,0))

        pco,pci = mk_card(inner); pco.pack(fill="x",pady=6)
        lbl(pci,"PASSENGERS",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(0,8))
        ph = tk.Frame(pci,bg=BG_CARD); ph.pack(fill="x",pady=(0,6))
        lbl(ph,f"Adult: {ADULT_PRICE} EUR   |   Child: {CHILD_PRICE} EUR",
            font=("Segoe UI",9),fg=MUTED,bg=BG_CARD).pack(side="left")
        counter_row(pci,"Adult Passengers",app.adult_count,bg=BG_CARD,callback=self._refresh,min_val=0,max_val=5).pack(fill="x",pady=3)
        counter_row(pci,"Child Passengers",app.child_count,bg=BG_CARD,callback=self._refresh,min_val=0,max_val=5).pack(fill="x",pady=3)

        sco,sci = mk_card(inner,padx=14,pady=14); sco.pack(fill="x",pady=6)
        lbl(sci,"SELECT SEATS",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(0,6))
        self.seat_info_lbl = tk.Label(sci,text="Select 1 seat(s)  —  0 selected",
                                      font=("Segoe UI",10),bg=BG_CARD,fg=MUTED)
        self.seat_info_lbl.pack(anchor="w",pady=(0,6))
        legf = tk.Frame(sci,bg=BG_CARD); legf.pack(anchor="w",pady=(0,6))
        for color,ltxt in [(BG_MID,"Available"),(BTN_BLUE,"Selected"),(GREEN_FILL,"Children"),(BG_CARD2,"Taken")]:
            tk.Frame(legf,bg=color,width=12,height=12,
                     highlightbackground=GLASS_BD,highlightthickness=1).pack(side="left",padx=(0,3))
            lbl(legf,ltxt,font=("Segoe UI",9),fg=MUTED,bg=BG_CARD).pack(side="left",padx=(0,10))
        self.seat_canvas = tk.Canvas(sci,bg=BG_CARD,highlightthickness=0,height=340)
        self.seat_canvas.pack(fill="x",pady=(0,4))
        self.seat_canvas.bind("<Configure>", lambda e: self._draw_plane(e.width,e.height))

        bco,bci = mk_card(inner); bco.pack(fill="x",pady=6)
        lbl(bci,"BAGGAGE",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(0,8))
        lbl(bci,f"First {BAG_FREE_KG} kg free  |  +{BAG_EUR_PER_KG} EUR/kg above limit  |  max 3 bags",
            font=("Segoe UI",9),fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(0,8))
        bagrow = tk.Frame(bci,bg=BG_CARD); bagrow.pack(fill="x")
        lbl(bagrow,"Add checked baggage",font=FONT_SUB,fg=WHITE,bg=BG_CARD).pack(side="left")
        self.bag_toggle_btn = tk.Button(bagrow,text="OFF",font=("Segoe UI",9,"bold"),
                                        bg=BG_MID,fg=MUTED,relief="flat",bd=0,
                                        cursor="hand2",padx=10,pady=4,command=self._toggle_bag)
        self.bag_toggle_btn.pack(side="right")
        self.bag_details = tk.Frame(bci,bg=BG_CARD)
        dr = tk.Frame(self.bag_details,bg=BG_CARD); dr.pack(fill="x")
        dr.columnconfigure(0,weight=1); dr.columnconfigure(1,weight=1)
        lbc = tk.Frame(dr,bg=BG_CARD); lbc.grid(row=0,column=0,sticky="ew",padx=(0,6))
        lbl(lbc,"Number of bags (1-3)",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(4,2))
        self.bag_count_e = mk_entry(lbc); self.bag_count_e.insert(0,"1")
        self.bag_count_e.pack(fill="x",ipady=7)
        self.bag_count_e.bind("<KeyRelease>", lambda e: self._build_totals())
        rbc = tk.Frame(dr,bg=BG_CARD); rbc.grid(row=0,column=1,sticky="ew",padx=(6,0))
        lbl(rbc,"Total weight (1-30 kg)",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(4,2))
        self.bag_weight_e = mk_entry(rbc); self.bag_weight_e.insert(0,"10")
        self.bag_weight_e.pack(fill="x",ipady=7)
        self.bag_weight_e.bind("<KeyRelease>", lambda e: self._build_totals())

        eco,eci = mk_card(inner); eco.pack(fill="x",pady=6)
        self.total_frame = tk.Frame(eci,bg=BG_CARD2,highlightbackground=GLASS_BD,highlightthickness=1)
        self.total_frame.pack(fill="x",pady=(0,12))
        self._build_totals()
        lbl(eci,"YOUR EMAIL ADDRESS",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(0,4))
        self.email_e = mk_entry(eci,textvariable=app.buyer_email)
        self.email_e.pack(fill="x",ipady=8)
        self.err_lbl = tk.Label(eci,text="",font=FONT_SMALL,fg=RED_ERR,bg=BG_CARD)
        self.err_lbl.pack(anchor="w",pady=(4,0))
        mk_btn(eci,"CONFIRM & PAY  →",self._proceed,pady=13).pack(fill="x",pady=(12,4))
        ghost_btn(eci,"← Back", lambda: app.show("ScreenFlights")).pack()

    def _draw_plane(self, W=600, H=340):
        if not self.seat_canvas or not self.seat_canvas.winfo_exists(): return
        c = self.seat_canvas; c.delete("all")
        if W < 80: return
        app = self.app
        fx1,fy1 = W*0.07, H*0.18
        fx2,fy2 = W*0.89, H*0.82
        cy = (fy1+fy2)/2
        c.create_oval(fx1,fy1,fx2,fy2, fill="#0e2446", outline=GLASS_BD, width=2)
        c.create_polygon(W*0.33,cy,W*0.28,H*0.01,W*0.57,H*0.01,W*0.62,cy,fill="#1a3a6a",outline=GLASS_BD,width=1)
        c.create_polygon(W*0.33,cy,W*0.28,H*0.99,W*0.57,H*0.99,W*0.62,cy,fill="#1a3a6a",outline=GLASS_BD,width=1)
        c.create_polygon(W*0.13,cy,W*0.08,H*0.10,W*0.24,H*0.30,fill="#1a3a6a",outline=GLASS_BD,width=1)
        c.create_polygon(W*0.13,cy,W*0.08,H*0.90,W*0.24,H*0.70,fill="#1a3a6a",outline=GLASS_BD,width=1)
        c.create_oval(W*0.83,cy-H*0.16,W*0.97,cy+H*0.16,fill="#0e2446",outline=GLASS_BD,width=2)
        margin=H*0.04; aisle_half=H*0.05
        top_band_top=fy1+margin; top_band_bot=cy-aisle_half
        bot_band_top=cy+aisle_half; bot_band_bot=fy2-margin
        half_h=(top_band_bot-top_band_top)/2
        y_A_top=top_band_top;          y_A_bot=top_band_top+half_h-1
        y_B_top=top_band_top+half_h+1; y_B_bot=top_band_bot-1
        half_h_low=(bot_band_bot-bot_band_top)/2
        y_C_top=bot_band_top+1;        y_C_bot=bot_band_top+half_h_low-1
        y_D_top=bot_band_top+half_h_low+1; y_D_bot=bot_band_bot
        c.create_line(W*0.15,cy,W*0.85,cy,fill=GLASS_BD,width=1,dash=(5,4))
        ef=("Segoe UI",7,"bold")
        for ex in [0.19,0.50,0.81]:
            c.create_text(W*ex,cy-H*0.10,text="EXIT",fill=GOLD,font=ef)
            c.create_text(W*ex,cy+H*0.10,text="EXIT",fill=GOLD,font=ef)
        lx=W*0.14
        for lt,my in [("A",(y_A_top+y_A_bot)/2),("B",(y_B_top+y_B_bot)/2),
                      ("C",(y_C_top+y_C_bot)/2),("D",(y_D_top+y_D_bot)/2)]:
            c.create_text(lx,my,text=lt,fill=MUTED,font=("Segoe UI",8,"bold"),anchor="center")
        usable_l=W*0.18; usable_r=W*0.82; cell_w=(usable_r-usable_l)/10
        for row_idx in range(10):
            row_num=10-row_idx
            rx=usable_r-(row_idx+0.5)*cell_w
            x1=rx-cell_w*0.42; x2=rx+cell_w*0.42
            for col,yt,yb in [("A",y_A_top,y_A_bot),("B",y_B_top,y_B_bot),
                               ("C",y_C_top,y_C_bot),("D",y_D_top,y_D_bot)]:
                seat_id=f"{row_num}{col}"
                taken=seat_id not in main.availableseats or seat_id in app.taken_seats
                selected=seat_id in app.selected_seats
                child_zone=col in ("C","D") and row_num<=5
                if taken:       fill=BG_CARD2; oc=GLASS_BD; tc="#4a6a8a"
                elif selected:  fill=BTN_BLUE; oc=BTN_HOVER; tc=WHITE
                elif child_zone:fill=GREEN_FILL;oc=GREEN_BD; tc=GREEN_TXT
                else:           fill=BG_MID;   oc=GLASS_BD; tc=ICE
                rid=c.create_rectangle(x1,yt,x2,yb,fill=fill,outline=oc,width=1)
                tid=c.create_text(rx,(yt+yb)/2,text=seat_id,fill=tc,font=("Segoe UI",7,"bold"))
                if not taken:
                    for item in (rid,tid):
                        c.tag_bind(item,"<Button-1>",lambda e,s=seat_id: self._toggle_seat(s))
                        c.tag_bind(item,"<Enter>",   lambda e,r=rid: c.itemconfig(r,outline=BTN_HOVER))
                        c.tag_bind(item,"<Leave>",   lambda e,r=rid,o=oc: c.itemconfig(r,outline=o))
        lx2,ly2=W*0.04,H*0.93
        for color,ltxt in [(BG_MID,"Available"),(BTN_BLUE,"Selected"),(GREEN_FILL,"Children"),(BG_CARD2,"Taken")]:
            c.create_rectangle(lx2,ly2,lx2+10,ly2+10,fill=color,outline=GLASS_BD)
            c.create_text(lx2+14,ly2+5,text=ltxt,anchor="w",fill=MUTED,font=("Segoe UI",8))
            lx2+=85

    def _toggle_seat(self, s):
        total=self.app.adult_count.get()+self.app.child_count.get()
        if s in self.app.selected_seats:
            self.app.selected_seats.remove(s)
        else:
            if len(self.app.selected_seats)>=total:
                messagebox.showwarning("NF Air",f"You can only select {total} seat(s)."); return
            self.app.selected_seats.append(s)
        self._refresh()

    def _refresh(self):
        total=self.app.adult_count.get()+self.app.child_count.get()
        if self.seat_info_lbl and self.seat_info_lbl.winfo_exists():
            self.seat_info_lbl.config(text=f"Select {total} seat(s)  —  {len(self.app.selected_seats)} selected")
        if self.seat_canvas and self.seat_canvas.winfo_exists():
            W=self.seat_canvas.winfo_width(); H=self.seat_canvas.winfo_height()
            self._draw_plane(W if W>10 else 600, H if H>10 else 340)
        if self.total_frame and self.total_frame.winfo_exists():
            self._build_totals()

    def _toggle_bag(self):
        self.app.has_baggage.set(not self.app.has_baggage.get())
        if self.app.has_baggage.get():
            self.bag_toggle_btn.config(text="ON",bg=BTN_BLUE,fg=WHITE)
            self.bag_details.pack(fill="x",pady=(8,0))
        else:
            self.bag_toggle_btn.config(text="OFF",bg=BG_MID,fg=MUTED)
            self.bag_details.pack_forget()
        self._build_totals()

    def _build_totals(self):
        if not self.total_frame or not self.total_frame.winfo_exists(): return
        for w in self.total_frame.winfo_children(): w.destroy()
        a=self.app.adult_count.get(); ch=self.app.child_count.get()
        bag_s=0
        if self.app.has_baggage.get() and self.bag_weight_e and self.bag_weight_e.winfo_exists():
            try:
                raw=self.bag_weight_e.get().strip()
                if raw: bag_s=calc_baggage_surcharge(int(raw))
            except (ValueError,TypeError): pass
        total=a*ADULT_PRICE+ch*CHILD_PRICE+bag_s
        self.app.total_payment=total
        tp=tk.Frame(self.total_frame,bg=BG_CARD2,padx=14,pady=10); tp.pack(fill="x")
        for lt,rt in [(f"Adults (x{a})",f"{a*ADULT_PRICE} EUR"),(f"Children (x{ch})",f"{ch*CHILD_PRICE} EUR")]:
            r=tk.Frame(tp,bg=BG_CARD2); r.pack(fill="x",pady=1)
            tk.Label(r,text=lt,font=FONT_SMALL,bg=BG_CARD2,fg=MUTED).pack(side="left")
            tk.Label(r,text=rt,font=FONT_SMALL,bg=BG_CARD2,fg=WHITE).pack(side="right")
        if bag_s:
            r=tk.Frame(tp,bg=BG_CARD2); r.pack(fill="x",pady=1)
            tk.Label(r,text="Baggage surcharge",font=FONT_SMALL,bg=BG_CARD2,fg=MUTED).pack(side="left")
            tk.Label(r,text=f"{bag_s} EUR",font=FONT_SMALL,bg=BG_CARD2,fg=WHITE).pack(side="right")
        mk_sep(tp,bg=GLASS_BD).pack(fill="x",pady=6)
        tr=tk.Frame(tp,bg=BG_CARD2); tr.pack(fill="x")
        tk.Label(tr,text="TOTAL",font=("Segoe UI",12,"bold"),bg=BG_CARD2,fg=WHITE).pack(side="left")
        tk.Label(tr,text=f"{total} EUR",font=("Segoe UI",14,"bold"),bg=BG_CARD2,fg=GOLD).pack(side="right")

    def _proceed(self):
        app=self.app
        total=app.adult_count.get()+app.child_count.get()
        email=app.buyer_email.get().strip()
        if not email:
            self.err_lbl.config(text="Please enter your email address."); return
        if total==0:
            self.err_lbl.config(text="Please add at least 1 passenger."); return
        if len(app.selected_seats)<total:
            self.err_lbl.config(text=f"Please select {total} seat(s)."); return
        if app.has_baggage.get():
            try:
                bc=int(self.bag_count_e.get())
                bw=int(self.bag_weight_e.get())
                if bc < 1:
                    self.err_lbl.config(text="Minimum 1 bag required."); return
                if bc > 3:
                    self.err_lbl.config(text="Maximum 3 bags allowed."); return
                if bw < 1:
                    self.err_lbl.config(text="Minimum baggage weight is 1 kg."); return
                if bw > 30:
                    self.err_lbl.config(text="Maximum baggage weight is 30 kg."); return
                app.bag_count_val=bc; app.bag_weight_val=bw
            except:
                self.err_lbl.config(text="Invalid baggage values."); return
        self.err_lbl.config(text="")
        app.show("ScreenPayment")

class ScreenPayment(Screen):
    def __init__(self, parent, app): super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        app=self.app
        outer=tk.Frame(self,bg=BG_DARK)
        outer.place(relx=0.5,rely=0.05,anchor="n",relwidth=0.88)
        nfair_header(outer).pack(anchor="w",pady=(0,14))
        lbl(outer,"Complete Payment",font=FONT_TITLE,fg=WHITE,bg=BG_DARK).pack(anchor="w")
        lbl(outer,"Secure checkout",fg=MUTED,bg=BG_DARK).pack(anchor="w",pady=(2,14))
        co,ci=mk_card(outer,padx=20,pady=18); co.pack(fill="x")
        sb=tk.Frame(ci,bg=BG_CARD2,highlightbackground=GLASS_BD,highlightthickness=1,padx=14,pady=10)
        sb.pack(fill="x",pady=(0,14))
        for lt,rt in [("Flight",app.selected_flight["flightnumber"]),
                      ("Route", app.destination),
                      ("Seats", ", ".join(app.selected_seats)),
                      ("Total", f"{app.total_payment} EUR")]:
            r=tk.Frame(sb,bg=BG_CARD2); r.pack(fill="x",pady=2)
            tk.Label(r,text=lt,font=FONT_SMALL,bg=BG_CARD2,fg=MUTED).pack(side="left")
            tk.Label(r,text=rt,font=("Segoe UI",12,"bold") if lt=="Total" else FONT_SMALL,
                     bg=BG_CARD2,fg=GOLD if lt=="Total" else WHITE).pack(side="right")
        lbl(ci,"CARD NUMBER",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(0,4))
        self.card_num=mk_entry(ci); self.card_num.pack(fill="x",ipady=8)
        r2=tk.Frame(ci,bg=BG_CARD); r2.pack(fill="x")
        r2.columnconfigure(0,weight=1); r2.columnconfigure(1,weight=1)
        lf=tk.Frame(r2,bg=BG_CARD); lf.grid(row=0,column=0,sticky="ew",padx=(0,6))
        lbl(lf,"EXPIRY",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(8,2))
        self.card_exp=mk_entry(lf); self.card_exp.insert(0,"MM/YY"); self.card_exp.pack(fill="x",ipady=8)
        rf=tk.Frame(r2,bg=BG_CARD); rf.grid(row=0,column=1,sticky="ew",padx=(6,0))
        lbl(rf,"CVV",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(8,2))
        self.card_cvv=mk_entry(rf); self.card_cvv.pack(fill="x",ipady=8)
        lbl(ci,"CARDHOLDER NAME",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(8,4))
        self.card_name=mk_entry(ci); self.card_name.pack(fill="x",ipady=8)
        self.err_lbl=tk.Label(ci,text="",font=FONT_SMALL,fg=RED_ERR,bg=BG_CARD)
        self.err_lbl.pack(anchor="w",pady=(4,0))
        mk_btn(ci,"PAY NOW",self._pay,pady=13).pack(fill="x",pady=(12,4))
        ghost_btn(ci,"← Back", lambda: app.show("ScreenBuy")).pack()

    def _pay(self):
        num=self.card_num.get().replace(" ","")
        exp=self.card_exp.get().strip()
        cvv=self.card_cvv.get().strip()
        name=self.card_name.get().strip()
        if len(num)<12 or not exp or exp=="MM/YY" or len(cvv)<3 or not name:
            self.err_lbl.config(text="Please fill all payment fields correctly."); return
        self.err_lbl.config(text="")
        app=self.app
        for s in app.selected_seats:
            if s in main.availableseats:
                main.availableseats.remove(s)
        app.taken_seats+=app.selected_seats
        f=app.selected_flight
        bw=getattr(app,"bag_weight_val",0) if app.has_baggage.get() else 0
        send_ticket_bg(
            to_email        = app.buyer_email.get(),
            flightnumber    = f["flightnumber"],
            destination     = app.destination,
            dep_hour        = f["departurehour"],
            arr_hour        = f["arrivalhour"],
            seats           = ", ".join(app.selected_seats),
            payment         = app.total_payment,
            baggage_weight  = bw,
        )
        app.show("ScreenAfterPay")

class ScreenAfterPay(Screen):
    def __init__(self, parent, app): super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        app=self.app
        outer=tk.Frame(self,bg=BG_DARK)
        outer.place(relx=0.5,rely=0.18,anchor="n",relwidth=0.82)
        tk.Label(outer,text="✅",font=("Segoe UI Emoji",52),bg=BG_DARK).pack(pady=(0,8))
        lbl(outer,"Payment Successful!",font=("Segoe UI",20,"bold"),fg=WHITE,bg=BG_DARK).pack()
        lbl(outer,f"Confirmation sent to  {app.buyer_email.get()}",fg=MUTED,bg=BG_DARK).pack(pady=(4,22))
        lbl(outer,"Would you like to check in now?",font=("Segoe UI",12),fg=WHITE,bg=BG_DARK).pack(pady=(0,14))
        bf=tk.Frame(outer,bg=BG_DARK); bf.pack(fill="x")
        bf.columnconfigure(0,weight=1); bf.columnconfigure(1,weight=1)
        def go_ci():
            app.ci_adult.set(app.adult_count.get())
            app.ci_child.set(app.child_count.get())
            app.show("ScreenCheckinForms")
        for col,ltxt,cmd2 in [(0,"CHECK IN",go_ci),(1,"LATER",lambda: app.show("ScreenMenu"))]:
            fr=tk.Frame(bf,bg=BG_CARD,highlightbackground=GLASS_BD,highlightthickness=1)
            fr.grid(row=0,column=col,padx=6,sticky="nsew",ipady=12)
            icon2="✅" if col==0 else "🏠"
            tk.Label(fr,text=icon2,font=("Segoe UI Emoji",26),bg=BG_CARD).pack(pady=(14,4))
            tk.Label(fr,text=ltxt,font=("Segoe UI",11,"bold"),bg=BG_CARD,fg=WHITE).pack(pady=(0,14))
            for w in [fr]+list(fr.winfo_children()): w.bind("<Button-1>",lambda e,f=cmd2: f())
            fr.bind("<Enter>",lambda e,f=fr: [w.config(bg=BG_MID) for w in [f]+list(f.winfo_children())])
            fr.bind("<Leave>",lambda e,f=fr: [w.config(bg=BG_CARD) for w in [f]+list(f.winfo_children())])

class ScreenCheckinStart(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        outer=tk.Frame(self,bg=BG_DARK)
        outer.place(relx=0.5,rely=0.08,anchor="n",relwidth=0.88)
        nfair_header(outer).pack(anchor="w",pady=(0,16))
        lbl(outer,"Online Check-In",font=FONT_TITLE,fg=WHITE,bg=BG_DARK).pack(anchor="w")
        lbl(outer,"Select passenger count",fg=MUTED,bg=BG_DARK).pack(anchor="w",pady=(2,14))
        co,ci=mk_card(outer,padx=20,pady=20); co.pack(fill="x")
        counter_row(ci,"Adult Passengers",app.ci_adult,bg=BG_CARD,min_val=0,max_val=5).pack(fill="x",pady=6)
        counter_row(ci,"Child Passengers",app.ci_child,bg=BG_CARD,min_val=0,max_val=5).pack(fill="x",pady=6)
        mk_sep(ci).pack(fill="x",pady=12)
        def go():
            if app.ci_adult.get()+app.ci_child.get()==0:
                messagebox.showwarning("NF Air","Please add at least 1 passenger."); return
            app.show("ScreenCheckinForms")
        mk_btn(ci,"CONTINUE  →",go,pady=13).pack(fill="x",pady=(4,4))
        ghost_btn(ci,"← Back to Menu", lambda: app.show("ScreenMenu")).pack()

class ScreenCheckinForms(Screen):
    def __init__(self, parent, app): super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        app=self.app
        outer=tk.Frame(self,bg=BG_DARK)
        outer.place(relx=0.5,rely=0.04,anchor="n",relwidth=0.9,relheight=0.95)
        nfair_header(outer).pack(anchor="w",pady=(0,10))
        lbl(outer,"Passenger Details",font=FONT_TITLE,fg=WHITE,bg=BG_DARK).pack(anchor="w")
        lbl(outer,"Fill in info for each passenger",fg=MUTED,bg=BG_DARK).pack(anchor="w",pady=(2,10))
        so,_,inner=scrollable(outer); so.pack(fill="both",expand=True)
        total=app.ci_adult.get()+app.ci_child.get()
        self.fields=[]

        for i in range(total):
            is_child=i>=app.ci_adult.get()
            co,ci2=mk_card(inner,padx=18,pady=14); co.pack(fill="x",pady=6)
            hdr=tk.Frame(ci2,bg=BG_CARD); hdr.pack(fill="x",pady=(0,12))
            lbl(hdr,f"Passenger {i+1}",font=("Segoe UI",12,"bold"),fg=WHITE,bg=BG_CARD).pack(side="left")
            tk.Label(hdr,text="CHILD" if is_child else "ADULT",
                     font=("Segoe UI",8,"bold"),
                     bg="#2a2a00" if is_child else "#002a2a",
                     fg=GOLD if is_child else ICE,padx=8,pady=3).pack(side="left",padx=8)
            fd={}

            def ae(ltext, prefill="", key=None, parent=ci2):
                lbl(parent,ltext,font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
                e=mk_entry(parent); e.pack(fill="x",ipady=8)
                if prefill: e.insert(0,prefill)
                if key: fd[key]=e
                return e

            ae("FLIGHT NUMBER", app.selected_flight["flightnumber"] if app.selected_flight else "", "flightnumber")
            ae("DESTINATION", app.destination or "", "destination")

            r2=tk.Frame(ci2,bg=BG_CARD); r2.pack(fill="x")
            r2.columnconfigure(0,weight=1); r2.columnconfigure(1,weight=1)
            lf2=tk.Frame(r2,bg=BG_CARD); lf2.grid(row=0,column=0,sticky="ew",padx=(0,6))
            lbl(lf2,"DEPARTURE TIME",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
            edep=mk_entry(lf2); edep.pack(fill="x",ipady=8)
            if app.selected_flight: edep.insert(0,app.selected_flight["departurehour"])
            fd["departurehour"]=edep
            rf2=tk.Frame(r2,bg=BG_CARD); rf2.grid(row=0,column=1,sticky="ew",padx=(6,0))
            lbl(rf2,"ARRIVAL TIME",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
            earr=mk_entry(rf2); earr.pack(fill="x",ipady=8)
            if app.selected_flight: earr.insert(0,app.selected_flight["arrivalhour"])
            fd["arrivalhour"]=earr

            ae("FULL NAME","","fullname")

            r3=tk.Frame(ci2,bg=BG_CARD); r3.pack(fill="x")
            r3.columnconfigure(0,weight=1); r3.columnconfigure(1,weight=1)
            lf3=tk.Frame(r3,bg=BG_CARD); lf3.grid(row=0,column=0,sticky="ew",padx=(0,6))
            lbl(lf3,"DATE OF BIRTH",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
            edob=mk_entry(lf3); edob.insert(0,"DD/MM/YYYY"); edob.pack(fill="x",ipady=8); fd["dateofbirth"]=edob
            rf3=tk.Frame(r3,bg=BG_CARD); rf3.grid(row=0,column=1,sticky="ew",padx=(6,0))
            lbl(rf3,"AGE",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
            eage=mk_entry(rf3); eage.pack(fill="x",ipady=8); fd["age"]=eage

            r4=tk.Frame(ci2,bg=BG_CARD); r4.pack(fill="x")
            r4.columnconfigure(0,weight=1); r4.columnconfigure(1,weight=1)
            lf4=tk.Frame(r4,bg=BG_CARD); lf4.grid(row=0,column=0,sticky="ew",padx=(0,6))
            lbl(lf4,"PASSPORT NUMBER",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
            epass=mk_entry(lf4); epass.pack(fill="x",ipady=8); fd["passportnumber"]=epass
            rf4=tk.Frame(r4,bg=BG_CARD); rf4.grid(row=0,column=1,sticky="ew",padx=(6,0))
            lbl(rf4,"SEAT",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
            eseat=mk_entry(rf4); eseat.pack(fill="x",ipady=8)
            if i<len(app.selected_seats): eseat.insert(0,app.selected_seats[i])
            fd["seat"]=eseat

            lbl(ci2,"GENDER",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
            gv=tk.StringVar(value="M")
            gf2=tk.Frame(ci2,bg=BG_CARD); gf2.pack(anchor="w")
            for val,txt in [("M","Male"),("F","Female")]:
                tk.Radiobutton(gf2,text=txt,variable=gv,value=val,font=FONT_SUB,
                               bg=BG_CARD,fg=WHITE,selectcolor=BTN_BLUE,
                               activebackground=BG_CARD,activeforeground=WHITE).pack(side="left",padx=(0,14))
            fd["gender"]=gv

            lbl(ci2,"EMAIL ADDRESS",font=FONT_LABEL,fg=MUTED,bg=BG_CARD).pack(anchor="w",pady=(6,2))
            eemail=mk_entry(ci2); eemail.pack(fill="x",ipady=8)
            if i==0 and app.buyer_email.get(): eemail.insert(0,app.buyer_email.get())
            fd["emailadress"]=eemail

            self.fields.append(fd)

        self.err_lbl=tk.Label(inner,text="",font=FONT_SMALL,fg=RED_ERR,bg=BG_DARK)
        self.err_lbl.pack(anchor="w",pady=(4,0))
        mk_btn(inner,"COMPLETE CHECK-IN  ✈",self._submit,pady=13).pack(fill="x",pady=(8,4))
        ghost_btn(inner,"← Back", lambda: app.show("ScreenCheckinStart")).pack(pady=(0,16))

    def _submit(self):
        app=self.app; pax=[]
        required=["flightnumber","destination","departurehour","arrivalhour",
                  "fullname","passportnumber","seat","emailadress"]
        for fd in self.fields:
            data={}
            for k,v in fd.items():
                if isinstance(v, tk.StringVar):
                    data[k]=v.get()
                elif hasattr(v,"get"):
                    data[k]=v.get()
                else:
                    data[k]=""
            if any(not str(data.get(k,"")).strip() for k in required):
                self.err_lbl.config(text="Please fill all required fields for every passenger.")
                return
            pax.append(data)
        self.err_lbl.config(text="")
        app.ci_passengers=pax
        if not app.gate: app.gate=rand_gate()
        send_checkin_bg(pax)
        app.show("ScreenBoarding")

class ScreenBoarding(Screen):
    def __init__(self, parent, app): super().__init__(parent, app)

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        app=self.app
        outer=tk.Frame(self,bg=BG_DARK)
        outer.place(relx=0.5,rely=0.04,anchor="n",relwidth=0.9,relheight=0.95)
        nfair_header(outer).pack(anchor="w",pady=(0,10))
        lbl(outer,"Boarding Pass",font=FONT_TITLE,fg=WHITE,bg=BG_DARK).pack(anchor="w")
        lbl(outer,"Check-in complete!  Have a great flight.",fg=MUTED,bg=BG_DARK).pack(anchor="w",pady=(2,10))
        so,_,inner=scrollable(outer); so.pack(fill="both",expand=True)
        for p in app.ci_passengers: self._bp(inner,p,app.gate)
        mk_btn(inner,"Return to Home",lambda: app.show("ScreenMenu"),pady=13).pack(fill="x",pady=(8,20))

    def _bp(self, parent, p, gate):
        c=tk.Frame(parent,bg=BG_MID,highlightbackground=BTN_BLUE,highlightthickness=2)
        c.pack(fill="x",pady=8)
        pad=tk.Frame(c,bg=BG_MID,padx=22,pady=18); pad.pack(fill="x")
        tk.Label(pad,text="NF AIR",font=("Segoe UI",10,"bold"),bg=BG_MID,fg=MUTED).pack(anchor="w")
        mk_sep(pad,bg=GLASS_BD).pack(fill="x",pady=8)
        r1=tk.Frame(pad,bg=BG_MID); r1.pack(fill="x",pady=4)
        lf=tk.Frame(r1,bg=BG_MID); lf.pack(side="left",fill="x",expand=True)
        tk.Label(lf,text="PASSENGER",font=FONT_BPLBL,bg=BG_MID,fg=MUTED).pack(anchor="w")
        tk.Label(lf,text=p["fullname"],font=FONT_BPVAL,bg=BG_MID,fg=WHITE).pack(anchor="w")
        rf=tk.Frame(r1,bg=BG_MID); rf.pack(side="right")
        tk.Label(rf,text="FLIGHT",font=FONT_BPLBL,bg=BG_MID,fg=MUTED).pack(anchor="e")
        tk.Label(rf,text=p["flightnumber"],font=FONT_BPVAL,bg=BG_MID,fg=WHITE).pack(anchor="e")
        r2=tk.Frame(pad,bg=BG_MID); r2.pack(fill="x",pady=10)
        lf2=tk.Frame(r2,bg=BG_MID); lf2.pack(side="left")
        tk.Label(lf2,text="DEPARTS",font=FONT_BPLBL,bg=BG_MID,fg=MUTED).pack(anchor="w")
        tk.Label(lf2,text=p["departurehour"],font=("Segoe UI",24,"bold"),bg=BG_MID,fg=WHITE).pack(anchor="w")
        mf=tk.Frame(r2,bg=BG_MID); mf.pack(side="left",expand=True,fill="x",padx=12)
        tk.Label(mf,text="- - - ✈ - - -",font=("Segoe UI",12),bg=BG_MID,fg=GOLD).pack()
        rf2=tk.Frame(r2,bg=BG_MID); rf2.pack(side="right")
        tk.Label(rf2,text="ARRIVES",font=FONT_BPLBL,bg=BG_MID,fg=MUTED).pack(anchor="e")
        tk.Label(rf2,text=p["arrivalhour"],font=("Segoe UI",24,"bold"),bg=BG_MID,fg=WHITE).pack(anchor="e")
        mk_sep(pad,bg=GLASS_BD).pack(fill="x",pady=8)
        r3=tk.Frame(pad,bg=BG_MID); r3.pack(fill="x")
        gender_val=p.get("gender","M")
        gender_txt="Male" if gender_val in ("M","Male") else "Female"
        for lt,val,vfg in [("SEAT",p["seat"],WHITE),("GENDER",gender_txt,WHITE),("GATE",gate,GOLD)]:
            col=tk.Frame(r3,bg=BG_MID); col.pack(side="left",expand=True)
            tk.Label(col,text=lt,font=FONT_BPLBL,bg=BG_MID,fg=MUTED).pack(anchor="w")
            tk.Label(col,text=val,font=("Segoe UI",17,"bold"),bg=BG_MID,fg=vfg).pack(anchor="w")
        mk_sep(pad,bg=GLASS_BD).pack(fill="x",pady=8)
        bot=tk.Frame(pad,bg=BG_MID); bot.pack(fill="x")
        tk.Label(bot,text=f"Passport: {p['passportnumber']}",font=("Segoe UI",9),bg=BG_MID,fg=MUTED).pack(side="left")
        tk.Label(bot,text=p["emailadress"],font=("Segoe UI",9),bg=BG_MID,fg=MUTED).pack(side="right")

class NFAirApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NF Air")
        self.geometry("700x780")
        self.resizable(True, True)
        self.configure(bg=BG_DARK)
        self.minsize(560, 640)
        style=ttk.Style(); style.theme_use("default")
        style.configure("NF.Vertical.TScrollbar",
                        background=BG_DARK, troughcolor=BG_DARK,
                        bordercolor=BG_DARK, arrowcolor=BG_DARK,
                        relief="flat", width=4)
        self.departure       = tk.StringVar()
        self.arrival         = tk.StringVar()
        self.destination     = ""
        self.flights         = []
        self.selected_flight = None
        self.gate            = ""
        self.adult_count     = tk.IntVar(value=1)
        self.child_count     = tk.IntVar(value=0)
        self.selected_seats  = []
        self.taken_seats     = []
        self.has_baggage     = tk.BooleanVar(value=False)
        self.total_payment   = 0
        self.buyer_email     = tk.StringVar()
        self.ci_adult        = tk.IntVar(value=1)
        self.ci_child        = tk.IntVar(value=0)
        self.ci_passengers   = []
        self.bag_count_val   = 0
        self.bag_weight_val  = 0
        container=tk.Frame(self,bg=BG_DARK); container.pack(fill="both",expand=True)
        self.screens={}
        for S in (ScreenMenu,ScreenRoute,ScreenFlights,ScreenBuy,ScreenPayment,
                  ScreenAfterPay,ScreenCheckinStart,ScreenCheckinForms,ScreenBoarding):
            s=S(container,self); self.screens[S.__name__]=s; s.place(relwidth=1,relheight=1)
        self.show("ScreenMenu")

    def show(self, name):
        s=self.screens[name]; s.on_show(); s.lift()