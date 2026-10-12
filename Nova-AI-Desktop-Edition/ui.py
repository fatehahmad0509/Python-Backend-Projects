#!/usr/bin/env python3
"""
Nova AI – PySide6 Desktop UI
Run: python ui.py
"""

import sys, os, json
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QScrollArea, QLabel, QFrame, QSizePolicy,
    QDialog, QComboBox, QStackedWidget, QGraphicsDropShadowEffect,
    QTextEdit
)
from PySide6.QtCore  import Qt, QThread, Signal, QTimer, QRectF
from PySide6.QtGui   import (
    QFont, QColor, QPixmap, QPainter, QPainterPath,
    QLinearGradient, QBrush, QIcon, QPen
)

# ── main.py'den import et (DB + AI fonksiyonları) ────────
from main import (
    init_db, save_message, get_recent_messages, search_messages,
    SEARCH_TOOL, SYSTEM_PROMPT
)
from google import genai
from google.genai import types

# ═══════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

_LOGO_CANDIDATES = [
    os.path.join(BASE_DIR, "logo.jpeg"),
    os.path.join(BASE_DIR, "logo.png"),
    os.path.join(BASE_DIR, "nova_logo.png"),
]

def _find_logo():
    for p in _LOGO_CANDIDATES:
        if os.path.exists(p):
            return p
    return None

# ═══════════════════════════════════════════════════════════
#  SETTINGS  (main.py ile aynı key isimleri: api_key, model, theme)
# ═══════════════════════════════════════════════════════════
_DEFAULTS = {"model": "gemini-2.0-flash-lite", "theme": "dark", "api_key": ""}

def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        for k, v in _DEFAULTS.items():
            d.setdefault(k, v)
        return d
    except Exception:
        return dict(_DEFAULTS)

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ═══════════════════════════════════════════════════════════
#  THEMES
# ═══════════════════════════════════════════════════════════
DARK = {
    "bg": "#06061A", "surface": "#0D0D24", "surface2": "#131330",
    "border": "#1E1E50", "accent": "#7C3AED", "accent2": "#A855F7",
    "user_start": "#5B21B6", "user_end": "#9333EA",
    "ai_bubble": "#10102A", "ai_border": "#252565",
    "text_primary": "#E8E8FF", "text_sec": "#8888CC", "text_muted": "#353570",
    "input_bg": "#0D0D24", "input_border": "#2A2A60",
    "sb": "#1E1E50", "sb_h": "#4040A0",
}
LIGHT = {
    "bg": "#F3F0FF", "surface": "#FFFFFF", "surface2": "#EDE9FE",
    "border": "#C4B5FD", "accent": "#7C3AED", "accent2": "#A855F7",
    "user_start": "#6D28D9", "user_end": "#A855F7",
    "ai_bubble": "#FFFFFF", "ai_border": "#DDD6FE",
    "text_primary": "#1E1B4B", "text_sec": "#4C4488", "text_muted": "#9090C0",
    "input_bg": "#FFFFFF", "input_border": "#C4B5FD",
    "sb": "#C4B5FD", "sb_h": "#9B7AFA",
}

def get_theme(name):
    return DARK if name == "dark" else LIGHT

# ═══════════════════════════════════════════════════════════
#  STREAMING (UI için — main.py fonksiyonlarını kullanır)
# ═══════════════════════════════════════════════════════════
def create_answer_stream(user_message: str, api_key: str, model: str):
    """main.py'deki DB + TOOL + SYSTEM_PROMPT kullanarak UI'a chunk yollar."""
    client = genai.Client(api_key=api_key)
    recent = get_recent_messages(20)
    history = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
    user_content = f"[History]\n{history}\n\n[User]\n{user_message}"
    messages = [{"role": "user", "parts": [{"text": user_content}]}]

    # 1. Önce tool call var mı kontrol et (non-stream)
    response = client.models.generate_content(
        model=model, contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT, tools=[SEARCH_TOOL]
        )
    )

    part = response.candidates[0].content.parts[0]

    if getattr(part, "function_call", None):
        fn = part.function_call
        results = search_messages(fn.args.get("query", ""))
        result_text = "\n".join(f"{r['role']}: {r['content']}" for r in results) or "No results."
        messages.append(response.candidates[0].content)
        messages.append(types.Content(role="user", parts=[
            types.Part.from_function_response(name=fn.name, response={"result": result_text})
        ]))

    # 2. Stream çağrısı (tool call sonrası ya da direkt)
    stream = client.models.generate_content_stream(
        model=model, contents=messages,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT, tools=[SEARCH_TOOL]
        )
    )
    for chunk in stream:
        if chunk.text:
            yield chunk.text

# ═══════════════════════════════════════════════════════════
#  WORKER
# ═══════════════════════════════════════════════════════════
class AIWorker(QThread):
    chunk = Signal(str)
    done  = Signal(str)
    error = Signal(str)

    def __init__(self, message, api_key, model):
        super().__init__()
        self.message = message
        self.api_key = api_key
        self.model   = model

    def run(self):
        try:
            full = ""
            for ch in create_answer_stream(self.message, self.api_key, self.model):
                self.chunk.emit(ch)
                full += ch
            self.done.emit(full)
        except Exception as e:
            self.error.emit(str(e))

# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════
def make_circle_pixmap(pix, size):
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    p = QPainter(result)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    path = QPainterPath()
    path.addEllipse(QRectF(0, 0, size, size))
    p.setClipPath(path)
    scaled = pix.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    x_off = (scaled.width()  - size) // 2
    y_off = (scaled.height() - size) // 2
    p.drawPixmap(0, 0, scaled, x_off, y_off, size, size)
    p.end()
    return result

# ═══════════════════════════════════════════════════════════
#  AVATAR
# ═══════════════════════════════════════════════════════════
class AvatarLabel(QLabel):
    def __init__(self, is_user, size=36):
        super().__init__()
        self.setFixedSize(size, size)
        self._sz = size; self._user = is_user
        logo = _find_logo()
        if not is_user and logo:
            pix = QPixmap(logo)
            if not pix.isNull():
                self.setPixmap(make_circle_pixmap(pix, size)); return
        self._draw_fallback()

    def _draw_fallback(self):
        sz = self._sz
        pix = QPixmap(sz, sz); pix.fill(Qt.transparent)
        p = QPainter(pix); p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath(); path.addEllipse(QRectF(0, 0, sz, sz))
        g = QLinearGradient(0, 0, sz, sz)
        g.setColorAt(0, QColor("#5B21B6" if self._user else "#4338CA"))
        g.setColorAt(1, QColor("#9333EA" if self._user else "#A855F7"))
        p.fillPath(path, QBrush(g))
        p.setPen(QColor("#FFFFFF")); p.setFont(QFont("Segoe UI", sz//3, QFont.Bold))
        p.drawText(QRectF(0, 0, sz, sz), Qt.AlignCenter, "S" if self._user else "N")
        p.end(); self.setPixmap(pix)

# ═══════════════════════════════════════════════════════════
#  MESSAGE BUBBLE
# ═══════════════════════════════════════════════════════════
class MessageBubble(QWidget):
    def __init__(self, role, content, timestamp, T):
        super().__init__()
        self._text = content
        self._is_user = (role == "user")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(16, 3, 16, 3)
        outer.setSpacing(10)

        avatar = AvatarLabel(self._is_user, 36)

        bubble = QFrame(); bubble.setObjectName("bbl")
        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(16, 11, 16, 9); bl.setSpacing(5)

        # QLabel + wordWrap → scroll sırasında kesilme yok
        self.lbl = QLabel(content)
        self.lbl.setWordWrap(True)
        self.lbl.setFont(QFont("Segoe UI", 10))
        self.lbl.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl.setStyleSheet("background:transparent; border:none; padding:0;")

        ts_lbl = QLabel(self._fmt(timestamp))
        ts_lbl.setFont(QFont("Segoe UI", 7))
        ts_lbl.setStyleSheet("background:transparent;")

        bl.addWidget(self.lbl)
        bl.addWidget(ts_lbl, alignment=Qt.AlignRight if self._is_user else Qt.AlignLeft)
        bubble.setMaximumWidth(520)

        if self._is_user:
            bubble.setStyleSheet(f"""
                QFrame#bbl {{
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 {T['user_start']}, stop:1 {T['user_end']});
                    border-radius:20px; border-bottom-right-radius:5px;
                }}
            """)
            self.lbl.setStyleSheet("color:#FFFFFF; background:transparent; border:none; padding:0;")
            ts_lbl.setStyleSheet("color:rgba(255,255,255,.40); background:transparent;")
            outer.addStretch(1)
            outer.addWidget(bubble)
            outer.addWidget(avatar, 0, Qt.AlignTop)
        else:
            bubble.setStyleSheet(f"""
                QFrame#bbl {{
                    background:{T['ai_bubble']};
                    border-radius:20px; border-bottom-left-radius:5px;
                    border:1px solid {T['ai_border']};
                }}
            """)
            self.lbl.setStyleSheet(f"color:{T['text_primary']}; background:transparent; border:none; padding:0;")
            ts_lbl.setStyleSheet(f"color:{T['text_muted']}; background:transparent;")
            outer.addWidget(avatar, 0, Qt.AlignTop)
            outer.addWidget(bubble)
            outer.addStretch(1)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18); shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60 if self._is_user else 40))
        bubble.setGraphicsEffect(shadow)

    def _auto_resize(self):
        doc_h = int(self.lbl.document().size().height())
        self.lbl.setFixedHeight(max(doc_h + 4, 20))

    def _fmt(self, ts):
        try:    return datetime.fromisoformat(ts).strftime("%H:%M")
        except: return ""

    def append_text(self, chunk):
        self._text += chunk
        self.lbl.setText(self._text)

# ═══════════════════════════════════════════════════════════
#  TYPING INDICATOR
# ═══════════════════════════════════════════════════════════
class TypingIndicator(QWidget):
    def __init__(self, T):
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 4, 16, 4); lay.setSpacing(10)
        avatar = AvatarLabel(False, 36)
        bubble = QFrame(); bubble.setObjectName("typing")
        bubble.setFixedSize(78, 40)
        bubble.setStyleSheet(f"""
            QFrame#typing {{
                background:{T['ai_bubble']}; border-radius:20px;
                border-bottom-left-radius:5px; border:1px solid {T['ai_border']};
            }}
        """)
        dl = QHBoxLayout(bubble); dl.setContentsMargins(12,0,12,0); dl.setSpacing(6)
        self._dots = []
        for _ in range(3):
            d = QLabel("●"); d.setFont(QFont("Arial", 8))
            d.setStyleSheet(f"color:{T['text_muted']}; background:transparent;")
            dl.addWidget(d); self._dots.append(d)
        lay.addWidget(avatar, 0, Qt.AlignTop)
        lay.addWidget(bubble); lay.addStretch()
        self._step = 0; self._T = T
        t = QTimer(self); t.timeout.connect(self._tick); t.start(350)

    def _tick(self):
        for i, d in enumerate(self._dots):
            c = self._T['accent2'] if i == self._step % 3 else self._T['text_muted']
            d.setStyleSheet(f"color:{c}; background:transparent;")
        self._step += 1

# ═══════════════════════════════════════════════════════════
#  CHAT AREA
# ═══════════════════════════════════════════════════════════
class ChatArea(QScrollArea):
    def __init__(self, T):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame); self._T = T
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(0, 16, 0, 16)
        self._layout.setSpacing(4); self._layout.addStretch()
        self.setWidget(self._container); self._style()

    def _style(self):
        T = self._T
        self.setStyleSheet(f"""
            QScrollArea {{ background:{T['bg']}; border:none; }}
            QWidget      {{ background:{T['bg']}; }}
            QScrollBar:vertical {{ background:transparent; width:5px; }}
            QScrollBar::handle:vertical {{
                background:{T['sb']}; border-radius:2px; min-height:24px;
            }}
            QScrollBar::handle:vertical:hover {{ background:{T['sb_h']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)

    def add_message(self, role, content, ts, T):
        bbl = MessageBubble(role, content, ts, T)
        self._layout.insertWidget(self._layout.count()-1, bbl)
        QTimer.singleShot(30, self._scroll_bottom); return bbl

    def add_typing(self, T):
        ind = TypingIndicator(T)
        self._layout.insertWidget(self._layout.count()-1, ind)
        QTimer.singleShot(30, self._scroll_bottom); return ind

    def remove_widget(self, w):
        self._layout.removeWidget(w); w.deleteLater()

    def _scroll_bottom(self):
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

# ═══════════════════════════════════════════════════════════
#  INPUT BAR
# ═══════════════════════════════════════════════════════════
class InputBar(QWidget):
    send_message = Signal(str)

    def __init__(self, T):
        super().__init__(); self._build(T)

    def _build(self, T):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{T['border']}; border:none;"); root.addWidget(sep)
        bar = QWidget(); bar.setStyleSheet(f"background:{T['surface']};")
        lay = QHBoxLayout(bar); lay.setContentsMargins(20,14,20,14); lay.setSpacing(12)
        self.field = QLineEdit()
        self.field.setPlaceholderText("Nova'ya bir şey sor...")
        self.field.setMinimumHeight(50); self.field.setFont(QFont("Segoe UI", 10))
        self.field.setStyleSheet(f"""
            QLineEdit {{
                background:{T['input_bg']}; color:{T['text_primary']};
                border:1.5px solid {T['input_border']}; border-radius:25px; padding:10px 22px;
            }}
            QLineEdit:focus {{ border:1.5px solid {T['accent']}; }}
        """)
        self.field.returnPressed.connect(self._emit)
        self.btn = QPushButton("➤"); self.btn.setFixedSize(50, 50)
        self.btn.setFont(QFont("Arial", 15)); self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {T['user_start']}, stop:1 {T['user_end']});
                color:#FFFFFF; border-radius:25px; border:none;
            }}
            QPushButton:hover {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {T['accent']}, stop:1 {T['accent2']});
            }}
            QPushButton:disabled {{ background:#1A1A38; color:#2A2A50; }}
        """)
        self.btn.clicked.connect(self._emit)
        lay.addWidget(self.field); lay.addWidget(self.btn); root.addWidget(bar)

    def _emit(self):
        txt = self.field.text().strip()
        if txt: self.field.clear(); self.send_message.emit(txt)

    def set_enabled(self, v):
        self.field.setEnabled(v); self.btn.setEnabled(v)
        if v: self.field.setFocus()

# ═══════════════════════════════════════════════════════════
#  HEADER
# ═══════════════════════════════════════════════════════════
class HeaderBar(QWidget):
    def __init__(self, T, on_settings):
        super().__init__(); self.setFixedHeight(72)
        self.setStyleSheet(f"HeaderBar {{ background:{T['surface']}; border-bottom:1px solid {T['border']}; }}")
        lay = QHBoxLayout(self); lay.setContentsMargins(22,0,22,0); lay.setSpacing(14)

        LOGO_SIZE = 46; RING_SIZE = 52
        logo_path = _find_logo()
        logo_pix = QPixmap(logo_path) if logo_path else QPixmap()
        ring_pix = QPixmap(RING_SIZE, RING_SIZE); ring_pix.fill(Qt.transparent)
        rp = QPainter(ring_pix)
        rp.setRenderHint(QPainter.Antialiasing); rp.setRenderHint(QPainter.SmoothPixmapTransform)
        offset = (RING_SIZE - LOGO_SIZE) // 2
        if not logo_pix.isNull():
            rp.drawPixmap(offset, offset, make_circle_pixmap(logo_pix, LOGO_SIZE))
        else:
            path_fb = QPainterPath(); path_fb.addEllipse(QRectF(offset, offset, LOGO_SIZE, LOGO_SIZE))
            g = QLinearGradient(offset, offset, offset+LOGO_SIZE, offset+LOGO_SIZE)
            g.setColorAt(0, QColor("#5B21B6")); g.setColorAt(1, QColor("#A855F7"))
            rp.fillPath(path_fb, QBrush(g))
            rp.setPen(QColor("#FFFFFF")); rp.setFont(QFont("Segoe UI", 18, QFont.Bold))
            rp.drawText(QRectF(offset, offset, LOGO_SIZE, LOGO_SIZE), Qt.AlignCenter, "N")
        rp.setPen(QPen(QColor(T['accent']), 2.5)); rp.setBrush(Qt.NoBrush)
        rp.drawEllipse(QRectF(1, 1, RING_SIZE-2, RING_SIZE-2)); rp.end()

        ring = QLabel(); ring.setFixedSize(RING_SIZE, RING_SIZE); ring.setPixmap(ring_pix)

        title_w = QWidget(); title_w.setStyleSheet("background:transparent;")
        tvl = QVBoxLayout(title_w); tvl.setContentsMargins(0,0,0,0); tvl.setSpacing(2)
        name_lbl = QLabel("Nova AI"); name_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        name_lbl.setStyleSheet(f"color:{T['text_primary']}; background:transparent;")
        status_row = QWidget(); status_row.setStyleSheet("background:transparent;")
        srl = QHBoxLayout(status_row); srl.setContentsMargins(0,0,0,0); srl.setSpacing(5)
        dot = QLabel("●"); dot.setFont(QFont("Arial",8))
        dot.setStyleSheet("color:#22C55E; background:transparent;")
        online = QLabel("Çevrimiçi"); online.setFont(QFont("Segoe UI",8))
        online.setStyleSheet(f"color:{T['text_muted']}; background:transparent;")
        srl.addWidget(dot); srl.addWidget(online); srl.addStretch()
        tvl.addWidget(name_lbl); tvl.addWidget(status_row)

        s_btn = QPushButton("⚙"); s_btn.setFixedSize(40, 40)
        s_btn.setFont(QFont("Arial",16)); s_btn.setCursor(Qt.PointingHandCursor)
        s_btn.setStyleSheet(f"""
            QPushButton {{
                background:{T['surface2']}; color:{T['text_sec']};
                border-radius:20px; border:1px solid {T['border']};
            }}
            QPushButton:hover {{ background:{T['accent']}; color:white; border:none; }}
        """)
        s_btn.clicked.connect(on_settings)
        lay.addWidget(ring); lay.addWidget(title_w); lay.addStretch(); lay.addWidget(s_btn)

# ═══════════════════════════════════════════════════════════
#  WELCOME SCREEN
# ═══════════════════════════════════════════════════════════
class WelcomeScreen(QWidget):
    def __init__(self, T):
        super().__init__(); self.setStyleSheet(f"background:{T['bg']};")
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignCenter); lay.setSpacing(16)
        logo_ring = QFrame(); logo_ring.setFixedSize(112, 112)
        logo_ring.setStyleSheet(f"background:transparent; border:2px solid {T['accent']}; border-radius:56px;")
        rlay = QHBoxLayout(logo_ring); rlay.setContentsMargins(4,4,4,4)
        logo_lbl = QLabel(); logo_lbl.setFixedSize(100, 100)
        logo_path = _find_logo()
        if logo_path:
            pix = QPixmap(logo_path)
            if not pix.isNull(): logo_lbl.setPixmap(make_circle_pixmap(pix, 100))
        else:
            logo_lbl.setText("N"); logo_lbl.setAlignment(Qt.AlignCenter)
            logo_lbl.setFont(QFont("Segoe UI", 42, QFont.Bold))
            logo_lbl.setStyleSheet("color:white; background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #5B21B6,stop:1 #A855F7); border-radius:50px;")
        rlay.addWidget(logo_lbl)
        title = QLabel("Nova AI"); title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 28, QFont.Bold))
        title.setStyleSheet(f"color:{T['accent2']}; background:transparent;")
        sub = QLabel("Yapay zeka asistanın her zaman burada")
        sub.setAlignment(Qt.AlignCenter); sub.setFont(QFont("Segoe UI", 11))
        sub.setStyleSheet(f"color:{T['text_sec']}; background:transparent;")
        hint = QLabel("Aşağıya yazarak sohbete başla ↓")
        hint.setAlignment(Qt.AlignCenter); hint.setFont(QFont("Segoe UI", 9))
        hint.setStyleSheet(f"color:{T['text_muted']}; background:transparent;")
        lay.addWidget(logo_ring, alignment=Qt.AlignCenter)
        lay.addWidget(title); lay.addWidget(sub); lay.addSpacing(6); lay.addWidget(hint)

# ═══════════════════════════════════════════════════════════
#  SETTINGS DIALOG
# ═══════════════════════════════════════════════════════════
class SettingsDialog(QDialog):
    saved = Signal(dict)

    def __init__(self, settings, T, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ayarlar – Nova AI")
        self.setMinimumWidth(480); self.setModal(True)
        self.setStyleSheet(f"""
            QDialog   {{ background:{T['bg']}; }}
            QLabel    {{ color:{T['text_primary']}; background:transparent; }}
            QLineEdit, QComboBox {{
                background:{T['input_bg']}; color:{T['text_primary']};
                border:1.5px solid {T['input_border']}; border-radius:10px;
                padding:9px 14px; font-size:10pt;
            }}
            QLineEdit:focus, QComboBox:focus {{ border:1.5px solid {T['accent']}; }}
            QComboBox::drop-down {{ border:none; width:30px; }}
            QComboBox QAbstractItemView {{
                background:{T['surface2']}; color:{T['text_primary']};
                selection-background-color:{T['accent']};
            }}
            QPushButton#save {{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {T['user_start']}, stop:1 {T['user_end']});
                color:white; border-radius:10px; padding:11px;
                font-size:10pt; font-weight:bold; border:none;
            }}
            QPushButton#save:hover {{ background:{T['accent2']}; }}
            QPushButton#cancel {{
                background:{T['surface2']}; color:{T['text_sec']};
                border-radius:10px; padding:11px;
                font-size:10pt; border:1px solid {T['border']};
            }}
        """)
        lay = QVBoxLayout(self); lay.setContentsMargins(32,30,32,28); lay.setSpacing(14)
        hdr = QLabel("⚙  Ayarlar"); hdr.setFont(QFont("Segoe UI", 16, QFont.Bold)); lay.addWidget(hdr)
        div = QFrame(); div.setFrameShape(QFrame.HLine)
        div.setStyleSheet(f"background:{T['border']}; border:none;"); div.setFixedHeight(1); lay.addWidget(div)

        self._sec(lay, "🔑  API Anahtarı")
        # main.py ile aynı key: api_key
        self.api_field = QLineEdit(settings.get("api_key", ""))
        self.api_field.setEchoMode(QLineEdit.Password)
        self.api_field.setPlaceholderText("Google Gemini API anahtarı")
        self.api_field.setMinimumHeight(44); lay.addWidget(self.api_field)
        toggle = QPushButton("👁  Göster / Gizle")
        toggle.setStyleSheet(f"QPushButton {{ background:transparent; color:{T['accent2']}; border:none; font-size:9pt; text-align:left; padding:0; }}")
        toggle.setCursor(Qt.PointingHandCursor)
        toggle.clicked.connect(lambda: self.api_field.setEchoMode(
            QLineEdit.Normal if self.api_field.echoMode()==QLineEdit.Password else QLineEdit.Password))
        lay.addWidget(toggle)

        self._sec(lay, "🤖  Model")
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gemini-2.0-flash-lite","gemini-2.0-flash","gemini-2.5-flash",
                                   "gemini-1.5-flash","gemini-1.5-pro","gemini-3.1-flash-lite"])
        cur = settings.get("model","gemini-2.0-flash-lite")
        idx = self.model_combo.findText(cur)
        if idx >= 0: self.model_combo.setCurrentIndex(idx)
        else: self.model_combo.addItem(cur); self.model_combo.setCurrentText(cur)
        self.model_combo.setMinimumHeight(44); lay.addWidget(self.model_combo)

        self._sec(lay, "🎨  Tema")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark","light"])
        self.theme_combo.setCurrentText(settings.get("theme","dark"))
        self.theme_combo.setMinimumHeight(44); lay.addWidget(self.theme_combo)

        lay.addSpacing(8)
        row = QHBoxLayout(); row.setSpacing(10)
        cancel = QPushButton("İptal"); cancel.setObjectName("cancel")
        cancel.setCursor(Qt.PointingHandCursor); cancel.clicked.connect(self.reject)
        save = QPushButton("💾  Kaydet"); save.setObjectName("save")
        save.setCursor(Qt.PointingHandCursor); save.clicked.connect(self._save)
        row.addWidget(cancel); row.addWidget(save); lay.addLayout(row)

    def _sec(self, lay, text):
        lbl = QLabel(text); lbl.setFont(QFont("Segoe UI", 10, QFont.Medium)); lay.addWidget(lbl)

    def _save(self):
        data = {
            "api_key": self.api_field.text().strip(),   # main.py ile aynı key
            "model":   self.model_combo.currentText(),
            "theme":   self.theme_combo.currentText(),
        }
        save_settings(data); self.saved.emit(data); self.accept()

# ═══════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.T        = get_theme(self.settings.get("theme","dark"))
        self._worker  = None; self._ai_bbl = None
        self._typing  = None; self._busy   = False
        init_db()  # main.py'den
        self._setup(); self._build(); self._load_history()

    def _setup(self):
        self.setWindowTitle("Nova AI"); self.setMinimumSize(820, 600); self.resize(1000, 740)
        logo = _find_logo()
        if logo: self.setWindowIcon(QIcon(logo))
        self._apply_global_style()

    def _apply_global_style(self):
        T = self.T
        self.setStyleSheet(f"""
            QMainWindow {{ background:{T['bg']}; }}
            QToolTip {{
                background:{T['surface2']}; color:{T['text_primary']};
                border:1px solid {T['border']}; padding:5px 9px; border-radius:7px;
            }}
        """)

    def _build(self):
        T = self.T
        cw = QWidget(); cw.setStyleSheet(f"background:{T['bg']};")
        self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.header = HeaderBar(T, self._open_settings); root.addWidget(self.header)
        self.stack = QStackedWidget(); self.stack.setStyleSheet(f"background:{T['bg']};")
        self.welcome = WelcomeScreen(T); self.chat = ChatArea(T)
        self.stack.addWidget(self.welcome); self.stack.addWidget(self.chat)
        root.addWidget(self.stack, 1)
        self.input_bar = InputBar(T)
        self.input_bar.send_message.connect(self._on_send)
        root.addWidget(self.input_bar)

    def _load_history(self):
        msgs = get_recent_messages(20)  # main.py'den
        if msgs:
            self.stack.setCurrentIndex(1)
            for m in msgs: self.chat.add_message(m["role"],m["content"],m["timestamp"],self.T)
        else:
            self.stack.setCurrentIndex(0)

    def _on_send(self, text):
        if self._busy: return
        api_key = self.settings.get("api_key","").strip()  # main.py ile aynı key
        if not api_key:
            self._inject_error("API anahtarı yok. Ayarlar'dan ekleyin."); return
        self.stack.setCurrentIndex(1)
        save_message("user", text)  # main.py'den
        self.chat.add_message("user", text, datetime.now().isoformat(), self.T)
        self._busy = True; self._ai_bbl = None
        self.input_bar.set_enabled(False)
        self._typing = self.chat.add_typing(self.T)
        model = self.settings.get("model","gemini-2.0-flash-lite")
        self._worker = AIWorker(text, api_key, model)
        self._worker.chunk.connect(self._on_chunk)
        self._worker.done.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_chunk(self, ch):
        if self._typing:
            self.chat.remove_widget(self._typing); self._typing = None
        if self._ai_bbl is None:
            self._ai_bbl = self.chat.add_message("ai","",datetime.now().isoformat(),self.T)
        self._ai_bbl.append_text(ch)
        self.chat._scroll_bottom()

    def _on_done(self, full):
        if self._typing: self.chat.remove_widget(self._typing); self._typing = None
        if self._ai_bbl is None:
            self.chat.add_message("ai",full,datetime.now().isoformat(),self.T)
        save_message("ai", full)  # main.py'den
        self._finish()

    def _on_error(self, err):
        if self._typing: self.chat.remove_widget(self._typing); self._typing = None
        e = str(err)
        if "API_KEY_INVALID" in e or "API key not valid" in e:
            msg = "❌ API anahtarı geçersiz. Ayarlar'dan doğru anahtarı girin."
        elif "API_KEY_NOT_FOUND" in e or "API key not found" in e:
            msg = "❌ API anahtarı bulunamadı. Ayarlar'dan anahtarı ekleyin."
        elif "quota" in e.lower() or "RESOURCE_EXHAUSTED" in e:
            msg = "⚠️ API limitine ulaşıldı. Bir süre bekleyip tekrar deneyin."
        elif "network" in e.lower() or "connection" in e.lower():
            msg = "🌐 Bağlantı hatası. İnternet bağlantını kontrol et."
        elif "model" in e.lower() and "not found" in e.lower():
            msg = "🤖 Seçili model bulunamadı. Ayarlar'dan farklı bir model seç."
        else:
            msg = f"⚠️ Bir hata oluştu: {e[:80]}"
        self.chat.add_message("ai", msg, datetime.now().isoformat(), self.T)
        self._finish()

    def _finish(self):
        self._busy = False; self._ai_bbl = None; self.input_bar.set_enabled(True)

    def _inject_error(self, msg):
        self.stack.setCurrentIndex(1)
        self.chat.add_message("ai", msg, datetime.now().isoformat(), self.T)

    def _open_settings(self):
        dlg = SettingsDialog(self.settings, self.T, self)
        dlg.saved.connect(self._on_settings_saved); dlg.exec()

    def _on_settings_saved(self, new_settings):
        old_theme = self.settings.get("theme","dark")
        self.settings = new_settings
        if new_settings.get("theme") != old_theme: self._rebuild()

    def _rebuild(self):
        self.T = get_theme(self.settings.get("theme","dark"))
        msgs = get_recent_messages(20)
        self._apply_global_style()
        cw = QWidget(); cw.setStyleSheet(f"background:{self.T['bg']};")
        self.setCentralWidget(cw)
        root = QVBoxLayout(cw); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.header = HeaderBar(self.T, self._open_settings); root.addWidget(self.header)
        self.stack = QStackedWidget(); self.stack.setStyleSheet(f"background:{self.T['bg']};")
        self.welcome = WelcomeScreen(self.T); self.chat = ChatArea(self.T)
        self.stack.addWidget(self.welcome); self.stack.addWidget(self.chat)
        root.addWidget(self.stack, 1)
        self.input_bar = InputBar(self.T)
        self.input_bar.send_message.connect(self._on_send); root.addWidget(self.input_bar)
        if msgs:
            self.stack.setCurrentIndex(1)
            for m in msgs: self.chat.add_message(m["role"],m["content"],m["timestamp"],self.T)
        else: self.stack.setCurrentIndex(0)
        self._busy = False; self._ai_bbl = None; self._typing = None

# ═══════════════════════════════════════════════════════════
#  ENTRY
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Nova AI")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())