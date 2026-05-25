import random
import requests
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QApplication,
                             QWidget, QStackedWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from colors import *
import database as db


class LoginDialog(QDialog):
    login_success = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.reset_code = None
        self.reset_username = None
        self.setWindowTitle("تسجيل الدخول - نظام إدارة الفواتير")
        self.setFixedSize(420, 420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {BG};
            }}
        """)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._stack = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)
        self._build_login_ui()
        self._build_reset_ui()
        self._stack.setCurrentIndex(0)

    def _build_login_ui(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(12)

        header = QLabel("نظام إدارة الفواتير")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setStyleSheet(f"color: {PRIMARY};")
        layout.addWidget(header)

        sub = QLabel("يرجى تسجيل الدخول للمتابعة")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_SEC}; font-size: 13px;")
        layout.addWidget(sub)

        layout.addSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.username_input.setStyleSheet(f"""
            QLineEdit {{ padding: 10px; border: 2px solid {BORDER};
                border-radius: 8px; font-size: 14px;
                background: {INPUT_BG}; color: {TEXT}; }}
            QLineEdit:focus {{ border-color: {ACCENT}; background: {INPUT_FOCUS}; }}
        """)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{ padding: 10px; border: 2px solid {BORDER};
                border-radius: 8px; font-size: 14px;
                background: {INPUT_BG}; color: {TEXT}; }}
            QLineEdit:focus {{ border-color: {ACCENT}; background: {INPUT_FOCUS}; }}
        """)
        self.password_input.returnPressed.connect(self._do_login)
        layout.addWidget(self.password_input)

        layout.addSpacing(8)

        self.login_btn = QPushButton("تسجيل الدخول")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: white; font-size: 15px;
                font-weight: bold; padding: 10px; border-radius: 8px; border: none; }}
            QPushButton:hover {{ background-color: {PRIMARY}; }}
        """)
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        self._forgot_btn = QPushButton("نسيان كلمة السر؟")
        self._forgot_btn.setCursor(Qt.PointingHandCursor)
        self._forgot_btn.setFlat(True)
        self._forgot_btn.setStyleSheet(f"""
            QPushButton {{ color: {ACCENT}; font-size: 12px; border: none;
                text-decoration: underline; padding: 4px; }}
            QPushButton:hover {{ color: {PRIMARY}; }}
        """)
        self._forgot_btn.clicked.connect(lambda: self._stack.setCurrentIndex(1))
        layout.addWidget(self._forgot_btn, alignment=Qt.AlignCenter)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: {DANGER}; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self._stack.addWidget(page)

    def _build_reset_ui(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setSpacing(12)

        header = QLabel("إعادة تعيين كلمة السر")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet(f"color: {PRIMARY};")
        layout.addWidget(header)

        sub = QLabel("سيتم إرسال رمز تحقق إلى المسؤول عبر Telegram")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px;")
        layout.addWidget(sub)

        layout.addSpacing(10)

        self.reset_user_input = QLineEdit()
        self.reset_user_input.setPlaceholderText("اسم المستخدم")
        self.reset_user_input.setStyleSheet(f"""
            QLineEdit {{ padding: 10px; border: 2px solid {BORDER};
                border-radius: 8px; font-size: 14px;
                background: {INPUT_BG}; color: {TEXT}; }}
            QLineEdit:focus {{ border-color: {ACCENT}; background: {INPUT_FOCUS}; }}
        """)
        layout.addWidget(self.reset_user_input)

        self.send_code_btn = QPushButton("إرسال رمز التحقق")
        self.send_code_btn.setCursor(Qt.PointingHandCursor)
        self.send_code_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: white; font-size: 14px;
                font-weight: bold; padding: 10px; border-radius: 8px; border: none; }}
            QPushButton:hover {{ background-color: {PRIMARY}; }}
        """)
        self.send_code_btn.clicked.connect(self._send_reset_code)
        layout.addWidget(self.send_code_btn)

        layout.addSpacing(8)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("أدخل رمز التحقق")
        self.code_input.setStyleSheet(f"""
            QLineEdit {{ padding: 10px; border: 2px solid {BORDER};
                border-radius: 8px; font-size: 14px;
                background: {INPUT_BG}; color: {TEXT}; }}
            QLineEdit:focus {{ border-color: {ACCENT}; background: {INPUT_FOCUS}; }}
        """)
        self.code_input.setVisible(False)
        layout.addWidget(self.code_input)

        self.new_pass_input = QLineEdit()
        self.new_pass_input.setPlaceholderText("كلمة السر الجديدة")
        self.new_pass_input.setEchoMode(QLineEdit.Password)
        self.new_pass_input.setStyleSheet(f"""
            QLineEdit {{ padding: 10px; border: 2px solid {BORDER};
                border-radius: 8px; font-size: 14px;
                background: {INPUT_BG}; color: {TEXT}; }}
            QLineEdit:focus {{ border-color: {ACCENT}; background: {INPUT_FOCUS}; }}
        """)
        self.new_pass_input.setVisible(False)
        layout.addWidget(self.new_pass_input)

        self.confirm_pass_input = QLineEdit()
        self.confirm_pass_input.setPlaceholderText("تأكيد كلمة السر الجديدة")
        self.confirm_pass_input.setEchoMode(QLineEdit.Password)
        self.confirm_pass_input.setStyleSheet(f"""
            QLineEdit {{ padding: 10px; border: 2px solid {BORDER};
                border-radius: 8px; font-size: 14px;
                background: {INPUT_BG}; color: {TEXT}; }}
            QLineEdit:focus {{ border-color: {ACCENT}; background: {INPUT_FOCUS}; }}
        """)
        self.confirm_pass_input.setVisible(False)
        self.confirm_pass_input.returnPressed.connect(self._do_reset)
        layout.addWidget(self.confirm_pass_input)

        self.reset_btn = QPushButton("تغيير كلمة السر")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {SUCCESS}; color: white; font-size: 14px;
                font-weight: bold; padding: 10px; border-radius: 8px; border: none; }}
            QPushButton:hover {{ background-color: {SUCCESS_HOVER}; }}
        """)
        self.reset_btn.setVisible(False)
        self.reset_btn.clicked.connect(self._do_reset)
        layout.addWidget(self.reset_btn)

        layout.addSpacing(6)

        self._back_btn = QPushButton("← العودة لتسجيل الدخول")
        self._back_btn.setCursor(Qt.PointingHandCursor)
        self._back_btn.setFlat(True)
        self._back_btn.setStyleSheet(f"""
            QPushButton {{ color: {TEXT_SEC}; font-size: 12px; border: none; padding: 4px; }}
            QPushButton:hover {{ color: {ACCENT}; }}
        """)
        self._back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(0))
        layout.addWidget(self._back_btn, alignment=Qt.AlignCenter)

        self.reset_status = QLabel("")
        self.reset_status.setAlignment(Qt.AlignCenter)
        self.reset_status.setStyleSheet(f"color: {DANGER}; font-size: 12px;")
        layout.addWidget(self.reset_status)

        layout.addStretch()
        self._stack.addWidget(page)

    def _send_reset_code(self):
        username = self.reset_user_input.text().strip()
        if not username:
            self.reset_status.setText("الرجاء إدخال اسم المستخدم")
            return

        user = db.get_user_by_username(username)
        if not user:
            self.reset_status.setText("اسم المستخدم غير موجود")
            return

        self.reset_username = username
        self.reset_code = f"{random.randint(100000, 999999)}"

        settings = db.get_company_settings()
        token = settings.get("telegram_bot_token", "")
        admin_id = settings.get("telegram_admin_id", "").strip()

        if not token or not admin_id:
            self.reset_status.setText("لم يتم إعداد Telegram للمسؤول. تواصل مع مدير النظام.")
            return

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            msg = (
                f"🔐 طلب إعادة تعيين كلمة السر\n"
                f"━━━━━━━━━━━━━━\n"
                f"المستخدم: {username}\n"
                f"رمز التحقق: {self.reset_code}\n"
                f"━━━━━━━━━━━━━━\n"
                f"إذا لم تكن أنت من طلب ذلك، تجاهل هذه الرسالة."
            )
            resp = requests.post(url, data={"chat_id": admin_id, "text": msg}, timeout=10)

            if resp.status_code == 200:
                self.send_code_btn.setEnabled(False)
                self.send_code_btn.setText("✅ تم الإرسال")
                self.code_input.setVisible(True)
                self.code_input.setFocus()
                self.reset_status.setStyleSheet(f"color: {SUCCESS}; font-size: 12px;")
                self.reset_status.setText("✅ تم إرسال رمز التحقق للمسؤول")
            else:
                self.reset_status.setText("❌ فشل إرسال رمز التحقق")
        except Exception as e:
            self.reset_status.setText(f"❌ خطأ في الإرسال: {str(e)}")

    def _do_reset(self):
        if not self.reset_code:
            return

        entered = self.code_input.text().strip()
        if entered != self.reset_code:
            self.reset_status.setText("❌ رمز التحقق غير صحيح")
            return

        new_pass = self.new_pass_input.text().strip()
        confirm = self.confirm_pass_input.text().strip()

        if not new_pass:
            self.reset_status.setText("الرجاء إدخال كلمة السر الجديدة")
            return

        if new_pass != confirm:
            self.reset_status.setText("❌ كلمتا السر غير متطابقتين")
            return

        if len(new_pass) < 4:
            self.reset_status.setText("❌ كلمة السر يجب أن تكون 4 محارف على الأقل")
            return

        user = db.get_user_by_username(self.reset_username)
        if not user:
            self.reset_status.setText("❌ المستخدم غير موجود")
            return

        success, msg = db.update_user(user["id"], user["username"], new_pass, user["role"], user.get("full_name", ""))
        if success:
            QMessageBox.information(self, "تم", "✅ تم تغيير كلمة السر بنجاح.\nالرجاء تسجيل الدخول بكلمة السر الجديدة.")
            self.reset_code = None
            self.reset_username = None
            self.code_input.setText("")
            self.new_pass_input.setText("")
            self.confirm_pass_input.setText("")
            self.reset_user_input.setText("")
            self.code_input.setVisible(False)
            self.new_pass_input.setVisible(False)
            self.confirm_pass_input.setVisible(False)
            self.reset_btn.setVisible(False)
            self.send_code_btn.setEnabled(True)
            self.send_code_btn.setText("إرسال رمز التحقق")
            self.reset_status.setText("")
            self._stack.setCurrentIndex(0)
        else:
            self.reset_status.setText(f"❌ {msg}")

    def _do_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            self.status_label.setText("الرجاء إدخال اسم المستخدم وكلمة المرور")
            return
        user = db.verify_user(username, password)
        if user:
            self.current_user = user
            self.login_success.emit(user)
            self.accept()
        else:
            self.status_label.setText("اسم المستخدم أو كلمة المرور غير صحيحة")
            self.password_input.clear()
            self.password_input.setFocus()
