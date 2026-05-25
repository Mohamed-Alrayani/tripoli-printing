from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import database as db
from colors import *


STYLES = {
    "title": f"font-size: 16px; font-weight: bold; color: {PRIMARY}; padding: 6px;",
    "subtitle": f"font-size: 14px; font-weight: bold; color: {PRIMARY}; padding: 4px 0;",
    "group": f"""
        QGroupBox {{ font-weight: bold; font-size: 13px; padding-top: 12px;
            background-color: {CARD}; border: 1px solid {BORDER};
            border-radius: 10px; margin-top: 8px;
            padding: 16px 12px 12px 12px;
            color: {TEXT_SEC}; }}
    """,
    "btn_save": f"""
        QPushButton {{ background-color: {SUCCESS}; color: white;
            padding: 11px 45px; font-weight: bold; font-size: 13px;
            border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {SUCCESS_HOVER}; }}
    """,
    "btn_add": f"""
        QPushButton {{ background-color: {ACCENT}; color: white;
            padding: 9px 24px; font-weight: bold; font-size: 13px;
            border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {PRIMARY}; }}
    """,
    "btn_danger": f"""
        QPushButton {{ background-color: {DANGER}; color: white;
            padding: 9px 24px; font-weight: bold; font-size: 13px;
            border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {DANGER_HOVER}; }}
    """,
    "input_style": f"""
        QLineEdit, QComboBox, QTextEdit {{
            padding: 8px 12px;
            border: 1.5px solid {BORDER};
            border-radius: 8px;
            background-color: {INPUT_BG};
            color: {TEXT};
            font-size: 13px;
        }}
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
            border-color: {BORDER_FOCUS};
            background-color: {INPUT_FOCUS};
        }}
        QComboBox::drop-down {{
            border: none;
            padding-right: 6px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {CARD};
            color: {TEXT};
            border: 1px solid {BORDER};
            border-radius: 6px;
            selection-background-color: {ACCENT};
            selection-color: white;
        }}
    """,
}


class SettingsWidget(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.current_user = current_user
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._load()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(8)
        main.setContentsMargins(20, 12, 20, 12)

        tabs = QTabWidget()
        tabs.setLayoutDirection(Qt.RightToLeft)
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 8px;
                background-color: {BG}; top: -1px; }}
            QTabBar::tab {{ background-color: {TAB_BG}; color: {TEXT_SEC};
                padding: 8px 20px; font-weight: bold; font-size: 13px;
                border-top-left-radius: 8px; border-top-right-radius: 8px;
                border: 1px solid transparent; border-bottom: none; }}
            QTabBar::tab:selected {{ background-color: {TAB_SELECTED};
                color: {PRIMARY}; border-color: {BORDER};
                border-bottom: 2.5px solid {ACCENT}; }}
            QTabBar::tab:hover:!selected {{ background-color: {TAB_HOVER};
                color: {TEXT}; }}
        """)

        company_tab = self._build_company_tab()
        tabs.addTab(company_tab, "بيانات الشركة")

        users_tab = self._build_users_tab()
        tabs.addTab(users_tab, "إدارة المستخدمين")

        change_pass_tab = self._build_change_password_tab()
        tabs.addTab(change_pass_tab, "تغيير كلمة المرور")

        main.addWidget(tabs)

    def _build_company_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        title = QLabel("إعدادات المنظومة - بيانات الشركة")
        title.setStyleSheet(STYLES["title"])
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        grp = QGroupBox("بيانات الشركة")
        grp.setStyleSheet(STYLES["group"])
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("اسم الشركة")
        self.company_name.setStyleSheet(STYLES["input_style"])
        form.addRow("اسم الشركة:", self.company_name)

        self.phone1 = QLineEdit()
        self.phone1.setPlaceholderText("رقم الهاتف الرئيسي")
        self.phone1.setStyleSheet(STYLES["input_style"])
        form.addRow("الهاتف 1:", self.phone1)

        self.phone2 = QLineEdit()
        self.phone2.setPlaceholderText("رقم هاتف إضافي")
        self.phone2.setStyleSheet(STYLES["input_style"])
        form.addRow("الهاتف 2:", self.phone2)

        self.address = QLineEdit()
        self.address.setPlaceholderText("العنوان بالكامل")
        self.address.setStyleSheet(STYLES["input_style"])
        form.addRow("العنوان:", self.address)

        self.currency = QComboBox()
        self.currency.addItems(["د.ل (دينار ليبي)", "ر.س (ريال سعودي)", "د.ك (دينار كويتي)", "د.إ (درهم إماراتي)", "$ (دولار)"])
        self.currency.setEditable(True)
        self.currency.setStyleSheet(STYLES["input_style"])
        form.addRow("العملة الافتراضية:", self.currency)

        self.invoice_notes = QTextEdit()
        self.invoice_notes.setMaximumHeight(80)
        self.invoice_notes.setPlaceholderText("ملاحظات تظهر في أسفل الفاتورة...")
        self.invoice_notes.setStyleSheet(STYLES["input_style"])
        form.addRow("ملاحظات الفاتورة:", self.invoice_notes)

        self.telegram_token = QLineEdit()
        self.telegram_token.setPlaceholderText("توكن بوت Telegram الخاص بك")
        self.telegram_token.setEchoMode(QLineEdit.Password)
        self.telegram_token.setStyleSheet(STYLES["input_style"])
        form.addRow("Telegram Bot Token:", self.telegram_token)

        self.telegram_admin_id = QLineEdit()
        self.telegram_admin_id.setPlaceholderText("ID المسؤول المستلم لنسخة من كل فاتورة")
        self.telegram_admin_id.setStyleSheet(STYLES["input_style"])
        form.addRow("Telegram ID المسؤول:", self.telegram_admin_id)

        self.telegram_bot_username = QLineEdit()
        self.telegram_bot_username.setPlaceholderText("Billlllllls_bot")
        self.telegram_bot_username.setStyleSheet(STYLES["input_style"])
        form.addRow("يوزر البوت (بدون @):", self.telegram_bot_username)

        self.cloud_server_url = QLineEdit()
        self.cloud_server_url.setPlaceholderText("https://tripoli-printing.onrender.com")
        self.cloud_server_url.setStyleSheet(STYLES["input_style"])
        form.addRow("رابط السيرفر السحابي:", self.cloud_server_url)

        self.cloud_api_key = QLineEdit()
        self.cloud_api_key.setPlaceholderText("مفتاح API للسحابة")
        self.cloud_api_key.setEchoMode(QLineEdit.Password)
        self.cloud_api_key.setStyleSheet(STYLES["input_style"])
        form.addRow("مفتاح API للسحابة:", self.cloud_api_key)

        grp.setLayout(form)
        layout.addWidget(grp)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("حفظ الإعدادات")
        save_btn.setStyleSheet(STYLES["btn_save"])
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return w

    def _build_users_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        title = QLabel("إدارة المستخدمين")
        title.setStyleSheet(STYLES["title"])
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        add_btn = QPushButton("إضافة مستخدم جديد")
        add_btn.setStyleSheet(STYLES["btn_add"])
        add_btn.clicked.connect(self._add_user_dialog)
        btn_row.addWidget(add_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.users_table = QTableWidget()
        self.users_table.setLayoutDirection(Qt.RightToLeft)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setSelectionMode(QTableWidget.SingleSelection)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setStyleSheet(f"""
            QTableWidget {{ background-color: {CARD}; alternate-background-color: {TABLE_ALT};
                border: 1px solid {BORDER}; border-radius: 8px; gridline-color: {BORDER}; font-size: 13px; }}
            QHeaderView::section {{ background-color: {TABLE_HEADER}; color: {HEADER_TEXT};
                padding: 8px; font-weight: bold; font-size: 13px; border: none; }}
            QTableWidget::item {{ padding: 6px; }}
        """)
        self.users_table.setColumnCount(5)
        self.users_table.setHorizontalHeaderLabels(["المعرف", "اسم المستخدم", "الصلاحية", "الاسم الكامل", "الإجراءات"])
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        layout.addWidget(self.users_table)

        self._refresh_users_table()
        return w

    def _build_change_password_tab(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        title = QLabel("تغيير كلمة المرور")
        title.setStyleSheet(STYLES["title"])
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        grp = QGroupBox("تغيير كلمة المرور")
        grp.setStyleSheet(STYLES["group"])
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.old_pass = QLineEdit()
        self.old_pass.setPlaceholderText("كلمة المرور الحالية")
        self.old_pass.setEchoMode(QLineEdit.Password)
        self.old_pass.setStyleSheet(STYLES["input_style"])
        form.addRow("كلمة المرور الحالية:", self.old_pass)

        self.new_pass = QLineEdit()
        self.new_pass.setPlaceholderText("كلمة المرور الجديدة")
        self.new_pass.setEchoMode(QLineEdit.Password)
        self.new_pass.setStyleSheet(STYLES["input_style"])
        form.addRow("كلمة المرور الجديدة:", self.new_pass)

        self.confirm_pass = QLineEdit()
        self.confirm_pass.setPlaceholderText("تأكيد كلمة المرور الجديدة")
        self.confirm_pass.setEchoMode(QLineEdit.Password)
        self.confirm_pass.setStyleSheet(STYLES["input_style"])
        form.addRow("تأكيد كلمة المرور:", self.confirm_pass)

        grp.setLayout(form)
        layout.addWidget(grp)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        change_btn = QPushButton("تغيير كلمة المرور")
        change_btn.setStyleSheet(STYLES["btn_save"])
        change_btn.clicked.connect(self._change_password)
        btn_row.addWidget(change_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        return w

    def _load(self):
        s = db.get_company_settings()
        self.company_name.setText(s.get("company_name", ""))
        self.phone1.setText(s.get("phone1", ""))
        self.phone2.setText(s.get("phone2", ""))
        self.address.setText(s.get("address", ""))
        currency = s.get("currency", "د.ل")
        idx = self.currency.findText(currency, Qt.MatchContains)
        if idx >= 0:
            self.currency.setCurrentIndex(idx)
        else:
            self.currency.setEditText(currency)
        self.invoice_notes.setPlainText(s.get("invoice_notes", ""))
        self.telegram_token.setText(s.get("telegram_bot_token", ""))
        self.telegram_admin_id.setText(s.get("telegram_admin_id", ""))
        self.telegram_bot_username.setText(s.get("telegram_bot_username", ""))
        self.cloud_server_url.setText(s.get("cloud_server_url", ""))
        self.cloud_api_key.setText(s.get("cloud_api_key", ""))

    def _save(self):
        name = self.company_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال اسم الشركة")
            return
        currency = self.currency.currentText().strip()
        db.save_company_settings(
            name,
            self.phone1.text().strip(),
            self.phone2.text().strip(),
            self.address.text().strip(),
            currency,
            self.invoice_notes.toPlainText().strip(),
            self.telegram_token.text().strip(),
            self.telegram_admin_id.text().strip(),
            self.cloud_server_url.text().strip(),
            self.cloud_api_key.text().strip(),
            self.telegram_bot_username.text().strip()
        )
        QMessageBox.information(self, "تم", "تم حفظ إعدادات الشركة بنجاح")

    def _refresh_users_table(self):
        users = db.get_all_users()
        self.users_table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.users_table.setItem(i, 0, QTableWidgetItem(str(u["id"])))
            self.users_table.setItem(i, 1, QTableWidgetItem(u["username"]))
            role_map = {"admin": "مشرف", "user": "مستخدم", "viewer": "مشاهد"}
            self.users_table.setItem(i, 2, QTableWidgetItem(role_map.get(u["role"], u["role"])))
            self.users_table.setItem(i, 3, QTableWidgetItem(u.get("full_name", "")))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            edit_btn = QPushButton("تعديل")
            edit_btn.setFixedSize(70, 28)
            edit_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {WARNING}; color: white;
                    border-radius: 5px; font-size: 12px; font-weight: bold; border: none; }}
                QPushButton:hover {{ background-color: {WARNING_HOVER}; }}
            """)
            uid = u["id"]
            edit_btn.clicked.connect(lambda checked, uid=uid: self._edit_user_dialog(uid))
            btn_layout.addWidget(edit_btn)

            if u["username"] != "admin":
                del_btn = QPushButton("حذف")
                del_btn.setFixedSize(70, 28)
                del_btn.setStyleSheet(f"""
                    QPushButton {{ background-color: {DANGER}; color: white;
                        border-radius: 5px; font-size: 12px; font-weight: bold; border: none; }}
                    QPushButton:hover {{ background-color: {DANGER_HOVER}; }}
                """)
                del_btn.clicked.connect(lambda checked, uid=uid: self._delete_user(uid))
                btn_layout.addWidget(del_btn)

            self.users_table.setCellWidget(i, 4, btn_widget)

    def _add_user_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("إضافة مستخدم جديد")
        dlg.setFixedSize(380, 320)
        dlg.setLayoutDirection(Qt.RightToLeft)
        dlg.setStyleSheet(f"QDialog {{ background-color: {CARD}; }}")
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("إضافة مستخدم جديد")
        title.setStyleSheet(STYLES["subtitle"])
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        username_input = QLineEdit()
        username_input.setPlaceholderText("اسم المستخدم")
        username_input.setStyleSheet(STYLES["input_style"])
        layout.addWidget(username_input)

        password_input = QLineEdit()
        password_input.setPlaceholderText("كلمة المرور")
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setStyleSheet(STYLES["input_style"])
        layout.addWidget(password_input)

        full_name_input = QLineEdit()
        full_name_input.setPlaceholderText("الاسم الكامل (اختياري)")
        full_name_input.setStyleSheet(STYLES["input_style"])
        layout.addWidget(full_name_input)

        role_combo = QComboBox()
        role_combo.addItems(["مستخدم", "مشرف", "مشاهد"])
        role_combo.setStyleSheet(STYLES["input_style"])
        layout.addWidget(role_combo)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {BTN_NEUTRAL}; color: white;
                padding: 8px 24px; border-radius: 6px; font-weight: bold; border: none; }}
            QPushButton:hover {{ background-color: {BTN_NEUTRAL_HOVER}; }}
        """)
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("إضافة")
        save_btn.setStyleSheet(STYLES["btn_add"])
        save_btn.clicked.connect(lambda: self._do_add_user(dlg, username_input, password_input, full_name_input, role_combo))
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)
        dlg.exec_()

    def _do_add_user(self, dlg, username_input, password_input, full_name_input, role_combo):
        username = username_input.text().strip()
        password = password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(dlg, "تنبيه", "الرجاء إدخال اسم المستخدم وكلمة المرور")
            return
        role_map = {"مستخدم": "user", "مشرف": "admin", "مشاهد": "viewer"}
        role = role_map.get(role_combo.currentText(), "user")
        full_name = full_name_input.text().strip()
        ok, msg = db.add_user(username, password, role, full_name)
        if ok:
            QMessageBox.information(dlg, "تم", msg)
            dlg.accept()
            self._refresh_users_table()
        else:
            QMessageBox.warning(dlg, "خطأ", msg)

    def _edit_user_dialog(self, user_id):
        users = db.get_all_users()
        user = next((u for u in users if u["id"] == user_id), None)
        if not user:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل المستخدم")
        dlg.setFixedSize(380, 350)
        dlg.setLayoutDirection(Qt.RightToLeft)
        dlg.setStyleSheet(f"QDialog {{ background-color: {CARD}; }}")
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("تعديل بيانات المستخدم")
        title.setStyleSheet(STYLES["subtitle"])
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        username_input = QLineEdit(user["username"])
        username_input.setPlaceholderText("اسم المستخدم")
        username_input.setStyleSheet(STYLES["input_style"])
        layout.addWidget(username_input)

        password_input = QLineEdit()
        password_input.setPlaceholderText("كلمة المرور الجديدة (اترك فارغاً إن لم ترد التغيير)")
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setStyleSheet(STYLES["input_style"])
        layout.addWidget(password_input)

        full_name_input = QLineEdit(user.get("full_name", ""))
        full_name_input.setPlaceholderText("الاسم الكامل")
        full_name_input.setStyleSheet(STYLES["input_style"])
        layout.addWidget(full_name_input)

        role_combo = QComboBox()
        role_combo.addItems(["مستخدم", "مشرف", "مشاهد"])
        role_map = {"user": "مستخدم", "admin": "مشرف", "viewer": "مشاهد"}
        idx = role_combo.findText(role_map.get(user["role"], "مستخدم"))
        role_combo.setCurrentIndex(idx if idx >= 0 else 0)
        role_combo.setStyleSheet(STYLES["input_style"])
        layout.addWidget(role_combo)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {BTN_NEUTRAL}; color: white;
                padding: 8px 24px; border-radius: 6px; font-weight: bold; border: none; }}
            QPushButton:hover {{ background-color: {BTN_NEUTRAL_HOVER}; }}
        """)
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("حفظ")
        save_btn.setStyleSheet(STYLES["btn_save"])
        save_btn.clicked.connect(lambda: self._do_edit_user(dlg, user_id, username_input, password_input, full_name_input, role_combo))
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)
        dlg.exec_()

    def _do_edit_user(self, dlg, user_id, username_input, password_input, full_name_input, role_combo):
        username = username_input.text().strip()
        if not username:
            QMessageBox.warning(dlg, "تنبيه", "اسم المستخدم مطلوب")
            return
        role_map = {"مستخدم": "user", "مشرف": "admin", "مشاهد": "viewer"}
        role = role_map.get(role_combo.currentText(), "user")
        full_name = full_name_input.text().strip()
        password = password_input.text().strip()
        ok, msg = db.update_user(user_id, username, password, role, full_name)
        if ok:
            QMessageBox.information(dlg, "تم", msg)
            dlg.accept()
            self._refresh_users_table()
        else:
            QMessageBox.warning(dlg, "خطأ", msg)

    def _delete_user(self, user_id):
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     "هل أنت متأكد من حذف هذا المستخدم؟",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return
        ok, msg = db.delete_user(user_id)
        if ok:
            QMessageBox.information(self, "تم", msg)
            self._refresh_users_table()
        else:
            QMessageBox.warning(self, "خطأ", msg)

    def _change_password(self):
        if not self.current_user:
            QMessageBox.warning(self, "تنبيه", "يجب تسجيل الدخول أولاً")
            return
        old = self.old_pass.text()
        new = self.new_pass.text()
        confirm = self.confirm_pass.text()
        if not old or not new:
            QMessageBox.warning(self, "تنبيه", "الرجاء إدخال كلمة المرور الحالية والجديدة")
            return
        if new != confirm:
            QMessageBox.warning(self, "تنبيه", "كلمة المرور الجديدة وتأكيدها غير متطابقين")
            return
        if len(new) < 4:
            QMessageBox.warning(self, "تنبيه", "كلمة المرور الجديدة يجب أن تكون 4 أحرف على الأقل")
            return
        ok, msg = db.change_user_password(self.current_user["id"], old, new)
        if ok:
            QMessageBox.information(self, "تم", msg)
            self.old_pass.clear()
            self.new_pass.clear()
            self.confirm_pass.clear()
        else:
            QMessageBox.warning(self, "خطأ", msg)
