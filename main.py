import sys
import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QScrollArea,
    QMessageBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QFrame
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEvent, pyqtProperty, QSize, QTimer
from PyQt5.QtGui import QFont, QCursor, QPainter, QPixmap, QIcon, QColor, QFontMetrics, QBrush, QPen

from database import init_db, DB_PATH
from invoice_module import InvoiceWidget
from archive_module import ArchiveWidget
from clients_module import ClientsWidget
from inventory_module import InventoryWidget
from settings_module import SettingsWidget
from login_module import LoginDialog
from telegram_bot_listener import TelegramBotListener
from colors import *

APP_STYLE = f"""
QMainWindow {{
    background-color: {BG};
}}
QWidget {{
    font-family: 'Noto Sans Arabic', 'Segoe UI', 'Tahoma', sans-serif;
    color: {TEXT};
    font-size: 13px;
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit, QTimeEdit {{
    padding: 8px 12px;
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    background-color: {INPUT_BG};
    color: {TEXT};
    selection-background-color: {ACCENT};
    selection-color: white;
    font-size: 13px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
    border-color: {BORDER_FOCUS};
    background-color: {INPUT_FOCUS};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    selection-background-color: {ACCENT};
    selection-color: white;
    padding: 4px;
}}
QGroupBox {{
    background-color: {CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 10px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    font-size: 13px;
    color: {TEXT_SEC};
}}
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    background-color: {BG};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background-color: {BORDER};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QTableWidget {{
    background-color: {CARD};
    alternate-background-color: {TABLE_ALT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    font-size: 13px;
    color: {TEXT};
}}
QHeaderView::section {{
    background-color: {TABLE_HEADER};
    color: {HEADER_TEXT};
    padding: 9px 8px;
    font-weight: bold;
    font-size: 13px;
    border: none;
    border-bottom: 1px solid {BORDER};
    border-right: 1px solid {BORDER};
}}
QTableWidget::item {{
    padding: 7px 5px;
    border: none;
}}
QTableWidget::item:selected {{
    background-color: rgba(37, 99, 235, 0.12);
    color: {TEXT};
}}
QPushButton {{
    padding: 9px 20px;
    border-radius: 8px;
    font-weight: bold;
    font-size: 13px;
    border: none;
}}
QSpinBox, QDoubleSpinBox {{
    padding: 8px 12px;
}}
"""


def _make_icon(text, color, size=32):
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor(color)))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(0, 0, size, size, 7, 7)
    p.setPen(QPen(QColor("white")))
    f = QFont("Arial", size // 2, QFont.Bold)
    p.setFont(f)
    fm = QFontMetrics(f)
    tw = fm.width(text)
    th = fm.height()
    p.drawText((size - tw) // 2, (size + th) // 2 - 2, text)
    p.end()
    return QIcon(pix)


class Sidebar(QWidget):
    _expanded_width = 210
    _collapsed_width = 64

    def __init__(self, current_user, main_window, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.main_window = main_window
        self.buttons = []
        self._anim = None
        self._current_index = 0
        self._expanded = False
        self.setFixedWidth(self._collapsed_width)
        self.setAttribute(Qt.WA_Hover)
        self.setMouseTracking(True)
        self.setStyleSheet(f"""
            Sidebar {{
                background-color: {CARD};
                border-left: 1px solid {BORDER};
            }}
        """)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 10)
        layout.setSpacing(4)

        role_map = {"admin": "مشرف", "user": "مستخدم", "viewer": "مشاهد"}
        user_role = role_map.get(self.current_user["role"], self.current_user["role"]) if self.current_user else ""

        self.user_label = QLabel(
            self.current_user.get("full_name", self.current_user["username"]) if self.current_user else "")
        self.user_label.setAlignment(Qt.AlignCenter)
        self.user_label.setStyleSheet(f"color: {PRIMARY}; font-size: 12px; font-weight: bold;")
        self.user_label.setFixedWidth(self._expanded_width - 16)
        self.user_label.installEventFilter(self)
        layout.addWidget(self.user_label)

        self.role_label = QLabel(f"({user_role})")
        self.role_label.setAlignment(Qt.AlignCenter)
        self.role_label.setStyleSheet(f"color: {TEXT_SEC}; font-size: 10px;")
        self.role_label.setFixedWidth(self._expanded_width - 16)
        self.role_label.installEventFilter(self)
        layout.addWidget(self.role_label)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        sep.installEventFilter(self)
        layout.addWidget(sep)

        sections = [
            ("ج", "فاتورة جديدة", ACCENT),
            ("أ", "أرشيف الفواتير", SUCCESS),
            ("ل", "العملاء", TEAL),
            ("م", "المخازن والجرد", WARNING),
            ("ع", "الإعدادات", PURPLE),
        ]

        for i, (icon, text, clr) in enumerate(sections):
            btn = QPushButton()
            btn.setIcon(_make_icon(icon, clr))
            btn.setIconSize(QSize(32, 32))
            btn.setCursor(Qt.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedHeight(50)
            btn._icon_char = icon
            btn._icon_color = clr
            btn._label = text
            btn._index = i
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent; color: {TEXT};
                    text-align: left; padding: 0 12px;
                    border-radius: 8px; font-size: 14px; font-weight: bold;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {TAB_HOVER};
                    color: {PRIMARY};
                }}
                QPushButton:checked {{
                    background-color: {ACCENT};
                    color: white;
                }}
            """)
            btn.clicked.connect(self._on_click)
            btn.installEventFilter(self)
            self.buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {BORDER};")
        sep2.installEventFilter(self)
        layout.addWidget(sep2)

        self.logout_btn = QPushButton("✕")
        self.logout_btn.setCursor(Qt.PointingHandCursor)
        self.logout_btn.setFixedSize(44, 44)
        self.logout_btn.setToolTip("تسجيل الخروج")
        self.logout_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {CARD}; color: {DANGER};
                border-radius: 8px; font-size: 20px; font-weight: bold;
                border: 1.5px solid rgba(220,38,38,0.2); }}
            QPushButton:hover {{ background-color: {DANGER}; color: white; border-color: {DANGER}; }}
        """)
        self.logout_btn.clicked.connect(self._logout_clicked)
        self.logout_btn.installEventFilter(self)
        layout.addWidget(self.logout_btn, 0, Qt.AlignCenter)

    def _on_click(self):
        btn = self.sender()
        idx = btn._index
        self._current_index = idx
        for i, b in enumerate(self.buttons):
            b.setChecked(i == idx)
            if self._expanded:
                b.setText(b._label)
            else:
                b.setText(b._label if i == idx else "")
        self.main_window.set_page(idx)

    def _update_labels(self, expanded):
        for i, btn in enumerate(self.buttons):
            if expanded:
                btn.setText(btn._label)
            else:
                btn.setText(btn._label if btn.isChecked() else "")

    def _get_anim_width(self):
        return self.width()

    def _set_anim_width(self, w):
        self.setFixedWidth(w)

    anim_width = pyqtProperty(int, _get_anim_width, _set_anim_width)

    def expand(self):
        if not self._expanded:
            self._expanded = True
            self._animate_width(self._expanded_width)
            self._update_labels(True)

    def collapse(self):
        if self._expanded:
            self._expanded = False
            self._animate_width(self._collapsed_width)
            self._update_labels(False)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Enter:
            self.expand()
        elif event.type() == QEvent.Leave:
            if not self._is_mouse_inside():
                self.collapse()
        return super().eventFilter(obj, event)

    def enterEvent(self, event):
        self.expand()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._is_mouse_inside():
            self.collapse()
        super().leaveEvent(event)

    def _is_mouse_inside(self):
        return self.rect().contains(self.mapFromGlobal(QCursor.pos()))

    def _animate_width(self, target):
        if self._anim and self._anim.state() == QPropertyAnimation.Running:
            self._anim.stop()
        self._anim = QPropertyAnimation(self, b"anim_width")
        self._anim.setDuration(180)
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(target)
        self._anim.start()

    def _logout_clicked(self):
        self.main_window._logout()


class MainWindow(QMainWindow):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self._is_logout = False
        self.setWindowTitle("نظام إدارة الفواتير - شركة الدعاية والإعلان")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(APP_STYLE)

        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget()

        inv_scroll = QScrollArea()
        inv_scroll.setWidgetResizable(True)
        self.invoice_widget = InvoiceWidget()
        self.invoice_widget.scroll_requested.connect(self._scroll_invoice_to)
        inv_scroll.setWidget(self.invoice_widget)
        self.stack.addWidget(inv_scroll)

        self.archive_widget = ArchiveWidget()
        self.archive_widget.edit_requested.connect(self._edit_invoice)
        arch_scroll = QScrollArea()
        arch_scroll.setWidgetResizable(True)
        arch_scroll.setWidget(self.archive_widget)
        self.stack.addWidget(arch_scroll)

        self.clients_widget = ClientsWidget()
        clients_scroll = QScrollArea()
        clients_scroll.setWidgetResizable(True)
        clients_scroll.setWidget(self.clients_widget)
        self.stack.addWidget(clients_scroll)

        self.inventory_widget = InventoryWidget()
        inv_scroll2 = QScrollArea()
        inv_scroll2.setWidgetResizable(True)
        inv_scroll2.setWidget(self.inventory_widget)
        self.stack.addWidget(inv_scroll2)

        self.settings_widget = SettingsWidget(current_user=current_user)
        settings_scroll = QScrollArea()
        settings_scroll.setWidgetResizable(True)
        settings_scroll.setWidget(self.settings_widget)
        self.stack.addWidget(settings_scroll)

        self.sidebar = Sidebar(current_user, self)
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack, 1)

        self.setCentralWidget(central)
        self._fit_to_screen()
        self.sidebar.buttons[0].setChecked(True)
        self.stack.currentChanged.connect(self._on_page_changed)
        self.set_page(0)

    def set_page(self, index):
        self.stack.setCurrentIndex(index)

    def _scroll_invoice_to(self, pos):
        scroll_area = self.stack.widget(0)
        if scroll_area and hasattr(scroll_area, 'verticalScrollBar'):
            scroll_area.verticalScrollBar().setValue(pos)

    def _on_page_changed(self, index):
        if index == 0:
            QTimer.singleShot(150, lambda: self._scroll_invoice_to(0))

    def _logout(self):
        reply = QMessageBox.question(
            self, "تأكيد تسجيل الخروج",
            "هل أنت متأكد من تسجيل الخروج؟\nسيتم حفظ الفاتورة الحالية تلقائياً.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        self.invoice_widget.auto_save()
        self._is_logout = True
        self.close()

    def _backup_db(self):
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"backup_{ts}.db")
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, backup_path)

    def closeEvent(self, event):
        if not self._is_logout:
            reply = QMessageBox.question(
                self, "تأكيد الخروج",
                "هل أنت متأكد من الخروج؟\nسيتم حفظ كل التعديلات تلقائياً.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        self.invoice_widget.auto_save()
        if not self._is_logout:
            self._backup_db()
        event.accept()

    def _edit_invoice(self, invoice_id):
        self.invoice_widget.load_invoice(invoice_id)
        self.set_page(0)
        self.sidebar.buttons[0].setChecked(True)
        QTimer.singleShot(300, lambda: self._scroll_invoice_to(0))

    def _fit_to_screen(self):
        screen = QApplication.primaryScreen().geometry()
        sw, sh = screen.width(), screen.height()
        win_w = min(int(sw * 0.92), 1350)
        win_h = min(int(sh * 0.90), 850)
        self.setMinimumSize(max(700, int(sw * 0.4)), max(450, int(sh * 0.4)))
        self.resize(win_w, win_h)
        x = (sw - self.width()) // 2
        y = (sh - self.height()) // 2
        self.move(x, y)


def main():
    init_db()

    bot_listener = TelegramBotListener()
    bot_listener.start()

    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Heartbeat للسيرفر السحابي: يرسل نبض كل 30 ثانية عشان السحاب يعرف ان الابتوب شغال
    _heartbeat_timer = QTimer()
    _heartbeat_timer.setInterval(30000)

    def _send_heartbeat():
        s = db.get_company_settings()
        cloud_url = (s.get("cloud_server_url") or "").rstrip("/")
        cloud_api_key = s.get("cloud_api_key") or ""
        if cloud_url and cloud_api_key:
            try:
                import requests as http_req
                http_req.post(
                    f"{cloud_url}/heartbeat",
                    headers={"X-API-KEY": cloud_api_key},
                    timeout=10
                )
            except Exception:
                pass

    _heartbeat_timer.timeout.connect(_send_heartbeat)
    _heartbeat_timer.start()

    # Retry pending uploads كل دقيقتين
    _retry_timer = QTimer()
    _retry_timer.setInterval(120000)
    _retry_timer.timeout.connect(lambda: __import__("cloud_sync").retry_pending_uploads())
    _retry_timer.start()
    QTimer.singleShot(10000, lambda: __import__("cloud_sync").retry_pending_uploads())

    # مزامنة فورية مع السحابة: تجربة كل 5 ثواني
    _sync_timer = QTimer()
    _sync_timer.setInterval(5000)
    _sync_timer.timeout.connect(lambda: __import__("sync_manager").process_queue())
    _sync_timer.start()
    QTimer.singleShot(2000, lambda: __import__("sync_manager").process_queue())

    while True:
        login = LoginDialog()
        if login.exec_() != LoginDialog.Accepted:
            break

        window = MainWindow(current_user=login.current_user)
        window.show()
        app.aboutToQuit.connect(window._backup_db)
        app.exec_()
        app.aboutToQuit.disconnect(window._backup_db)

        if not window._is_logout:
            break
        window.deleteLater()

    sys.exit()


if __name__ == "__main__":
    main()
