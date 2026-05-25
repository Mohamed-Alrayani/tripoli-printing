import os
import random
import logging
import requests
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QFileDialog, QDateEdit, QSpinBox
)
from datetime import datetime
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QColor
import database as db
from pdf_export import generate_invoice_pdf, generate_summary_report
from colors import *


STYLES = {
    "title": f"font-size: 16px; font-weight: bold; color: {PRIMARY}; padding: 6px;",
    "table": f"""
        QTableWidget {{ border: 1px solid {BORDER}; gridline-color: {BORDER};
            font-size: 13px; border-radius: 8px;
            background-color: {CARD}; alternate-background-color: {TABLE_ALT};
            color: {TEXT}; }}
        QHeaderView::section {{ background-color: {TABLE_HEADER}; color: {HEADER_TEXT};
            padding: 8px 7px; font-weight: bold; border: none;
            border-bottom: 1px solid {BORDER}; border-right: 1px solid {BORDER}; }}
        QTableWidget::item {{ padding: 6px 5px; border: none; }}
        QTableWidget::item:selected {{ background-color: rgba(37, 99, 235, 0.12); color: {TEXT}; }}
    """,
    "btn_search": f"""
        QPushButton {{ background-color: {ACCENT}; color: white; padding: 8px 24px;
            font-weight: bold; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: #1d4ed8; }}
    """,
    "btn_attach": f"""
        QPushButton {{ background-color: {PURPLE}; color: white; padding: 6px 14px;
            font-weight: bold; border-radius: 6px; font-size: 12px; border: none; }}
        QPushButton:hover {{ background-color: {PURPLE_HOVER}; }}
    """,
    "btn_print": f"""
        QPushButton {{ background-color: {WARNING}; color: white; padding: 6px 14px;
            font-weight: bold; border-radius: 6px; font-size: 12px; border: none; }}
        QPushButton:hover {{ background-color: {WARNING_HOVER}; }}
    """,
    "btn_delete": f"""
        QPushButton {{ background-color: {BTN_NEUTRAL}; color: white; padding: 6px 14px;
            font-weight: bold; border-radius: 6px; font-size: 12px; border: none; }}
        QPushButton:hover {{ background-color: {BTN_NEUTRAL_HOVER}; }}
    """,
    "btn_refresh": f"""
        QPushButton {{ background-color: {SUCCESS}; color: white; padding: 8px 24px;
            font-weight: bold; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {SUCCESS_HOVER}; }}
    """,
    "dialog": f"""
        QDialog {{ background-color: {BG}; }}
        QLabel {{ color: {TEXT}; font-size: 13px; }}
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{
            padding: 8px 12px; border: 1.5px solid {BORDER};
            border-radius: 8px; background-color: {INPUT_BG}; color: {TEXT}; font-size: 13px; }}
        QLineEdit:focus, QComboBox:focus {{ border-color: {BORDER_FOCUS};
            background-color: {INPUT_FOCUS}; }}
        QComboBox::drop-down {{ border: none; }}
        QComboBox QAbstractItemView {{ background-color: {CARD}; color: {TEXT};
            border: 1px solid {BORDER}; border-radius: 6px;
            selection-background-color: {ACCENT}; selection-color: white; }}
    """,
}


class ArchiveWidget(QWidget):
    edit_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._search()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(8)
        main.setContentsMargins(20, 12, 20, 12)

        title = QLabel("📂 أرشيف الفواتير - بحث واستعراض")
        title.setStyleSheet(STYLES["title"])
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        search_group = QGroupBox("🔍 بحث متقدم")
        search_group.setStyleSheet(f"QGroupBox{{font-weight:bold;font-size:13px;padding-top:10px;color:{TEXT_SEC};background:{CARD};border:1px solid {BORDER};border-radius:10px;margin-top:8px;padding:16px 12px 12px 12px;}}")
        search_layout = QVBoxLayout()
        search_layout.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        row1.addWidget(QLabel("رقم الفاتورة:"))
        self.search_number = QLineEdit()
        self.search_number.setPlaceholderText("INV-...")
        self.search_number.returnPressed.connect(self._search)
        row1.addWidget(self.search_number)

        row1.addWidget(QLabel("اسم العميل:"))
        self.search_client = QLineEdit()
        self.search_client.setPlaceholderText("بحث بالاسم")
        self.search_client.returnPressed.connect(self._search)
        row1.addWidget(self.search_client)

        row1.addWidget(QLabel("الحالة:"))
        self.search_status = QComboBox()
        self.search_status.addItems(["الكل", "قيد التصميم", "في المطبعة", "جاهز للتركيب", "تم التسليم"])
        row1.addWidget(self.search_status)

        search_btn = QPushButton("🔍 بحث")
        search_btn.setStyleSheet(STYLES["btn_search"])
        search_btn.clicked.connect(self._search)
        row1.addWidget(search_btn)

        report_btn = QPushButton("📊 تقرير شامل")
        report_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {PURPLE}; color: white; padding: 8px 20px;
                font-weight: bold; border-radius: 8px; border: none; }}
            QPushButton:hover {{ background-color: {PURPLE_HOVER}; }}
        """)
        report_btn.clicked.connect(self._generate_report)
        row1.addWidget(report_btn)

        search_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(QLabel("من تاريخ:"))
        self.search_date_from = QDateEdit()
        self.search_date_from.setCalendarPopup(True)
        self.search_date_from.setDate(QDate.currentDate().addYears(-1))
        self.search_date_from.setDisplayFormat("yyyy/MM/dd")
        row2.addWidget(self.search_date_from)

        row2.addWidget(QLabel("إلى تاريخ:"))
        self.search_date_to = QDateEdit()
        self.search_date_to.setCalendarPopup(True)
        self.search_date_to.setDate(QDate.currentDate())
        self.search_date_to.setDisplayFormat("yyyy/MM/dd")
        row2.addWidget(self.search_date_to)

        row2.addStretch()
        search_layout.addLayout(row2)
        search_group.setLayout(search_layout)
        main.addWidget(search_group)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(11)
        self.results_table.setHorizontalHeaderLabels([
            "#", "رقم الفاتورة", "العميل", "التاريخ",
            "الإجمالي", "المدفوع", "المتبقي", "الحالة", "المرفق", "كود التحقق", "إجراءات"
        ])
        h = self.results_table.horizontalHeader()
        stretch_cols = [1, 2, 3, 4, 5, 6, 7]
        for c in range(9):
            if c in stretch_cols:
                h.setSectionResizeMode(c, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        h.setMinimumSectionSize(80)
        self.results_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.Fixed)
        self.results_table.setColumnWidth(10, 620)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setStyleSheet(STYLES["table"])
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        main.addWidget(self.results_table, 1)

    def _search(self):
        inv_num = self.search_number.text().strip()
        client_name = self.search_client.text().strip()
        status = self.search_status.currentText()
        if status == "الكل":
            status = ""
        date_from = self.search_date_from.date().toString("yyyy/MM/dd")
        date_to = self.search_date_to.date().toString("yyyy/MM/dd")

        results = db.search_invoices(
            invoice_number=inv_num, client_name=client_name,
            date_from=date_from, date_to=date_to, status=status
        )
        self.results_table.setRowCount(0)
        if not results:
            return

        red_c = QColor(220, 38, 38)
        green_c = QColor(5, 150, 105)
        for idx, inv in enumerate(results):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            self.results_table.setRowHeight(row, 40)
            self.results_table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            self.results_table.setItem(row, 1, QTableWidgetItem(inv["invoice_number"]))
            self.results_table.setItem(row, 2, QTableWidgetItem(inv["client_name"]))
            self.results_table.setItem(row, 3, QTableWidgetItem(inv["date"]))
            self.results_table.setItem(row, 4, QTableWidgetItem(f"{inv['total_after_discount']:.2f}"))
            self.results_table.setItem(row, 5, QTableWidgetItem(f"{inv['paid_amount']:.2f}"))

            remaining = inv["remaining_amount"]
            rem_item = QTableWidgetItem(f"{remaining:.2f}")
            rem_item.setForeground(red_c if remaining > 0 else green_c)
            self.results_table.setItem(row, 6, rem_item)

            status_item = QTableWidgetItem(inv["status"])
            status_colors = {
                "قيد التصميم": QColor(217, 119, 6),
                "في المطبعة": QColor(37, 99, 235),
                "جاهز للتركيب": QColor(124, 58, 237),
                "تم التسليم": QColor(5, 150, 105),
            }
            status_item.setForeground(status_colors.get(inv["status"], QColor(0, 0, 0)))
            self.results_table.setItem(row, 7, status_item)

            has_attachment = "✔️" if inv.get("attachment_path") else "❌"
            attach_item = QTableWidgetItem(has_attachment)
            attach_item.setTextAlignment(Qt.AlignCenter)
            self.results_table.setItem(row, 8, attach_item)

            code = inv.get("telegram_secure_code") or ""
            code_item = QTableWidgetItem(code)
            code_item.setTextAlignment(Qt.AlignCenter)
            if code:
                code_item.setForeground(QColor(37, 99, 235))
                code_item.setToolTip("أرسل هذا الكود للبوت لاستلام الفاتورة")
            self.results_table.setItem(row, 9, code_item)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(8)

            attach_btn = QPushButton("📎 إرفاق")
            attach_btn.setStyleSheet(STYLES["btn_attach"])
            attach_btn.setFixedSize(95, 30)
            attach_btn.clicked.connect(lambda checked, iid=inv["id"]: self._attach_file(iid))
            actions_layout.addWidget(attach_btn)

            view_btn = QPushButton("👁️ عرض")
            view_btn.setStyleSheet(STYLES["btn_print"])
            view_btn.setFixedSize(95, 30)
            view_btn.clicked.connect(lambda checked, iid=inv["id"]: self._view_invoice(iid))
            actions_layout.addWidget(view_btn)

            reprint_btn = QPushButton("🖨️ طباعة")
            reprint_btn.setStyleSheet(STYLES["btn_print"])
            reprint_btn.setFixedSize(95, 30)
            reprint_btn.clicked.connect(lambda checked, iid=inv["id"]: self._reprint_invoice(iid))
            actions_layout.addWidget(reprint_btn)

            edit_btn = QPushButton("✏️ تعديل")
            edit_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {WARNING}; color: white; padding: 6px 14px;
                    font-weight: bold; border-radius: 6px; font-size: 12px; border: none; }}
                QPushButton:hover {{ background-color: {WARNING_HOVER}; }}
            """)
            edit_btn.setFixedSize(95, 30)
            edit_btn.clicked.connect(lambda checked, iid=inv["id"]: self._edit_invoice_local(iid))
            actions_layout.addWidget(edit_btn)

            tg_btn = QPushButton("📤 تلجرام")
            tg_btn.setStyleSheet(f"""
                QPushButton {{ background-color: {ACCENT}; color: white; padding: 6px 14px;
                    font-weight: bold; border-radius: 6px; font-size: 12px; border: none; }}
                QPushButton:hover {{ background-color: {PRIMARY}; }}
            """)
            tg_btn.setFixedSize(95, 30)
            tg_btn.clicked.connect(lambda checked, iid=inv["id"]: self._send_telegram_invoice(iid))
            actions_layout.addWidget(tg_btn)

            del_btn = QPushButton("🗑️ حذف")
            del_btn.setStyleSheet(STYLES["btn_delete"])
            del_btn.setFixedSize(95, 30)
            del_btn.clicked.connect(lambda checked, iid=inv["id"]: self._delete_invoice(iid))
            actions_layout.addWidget(del_btn)

            self.results_table.setCellWidget(row, 10, actions_widget)

            for col in range(10):
                it = self.results_table.item(row, col)
                if it and col != 6 and col != 7:
                    it.setTextAlignment(Qt.AlignCenter)

    def _attach_file(self, invoice_id):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختيار ملف مرفق", "",
            "الملفات المدعومة (*.jpg *.jpeg *.png *.pdf *.ai *.eps *.cdr *.psd);;All Files (*)"
        )
        if path:
            try:
                import shutil
                attach_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attachments")
                os.makedirs(attach_dir, exist_ok=True)
                ext = os.path.splitext(path)[1]
                dest = os.path.join(attach_dir, f"invoice_{invoice_id}{ext}")
                shutil.copy2(path, dest)
                db.update_attachment(invoice_id, dest)
                QMessageBox.information(self, "تم", "✅ تم إرفاق الملف بنجاح")
                self._search()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"❌ {str(e)}")

    def _view_invoice(self, invoice_id):
        inv = db.get_invoice_by_id(invoice_id)
        if not inv:
            QMessageBox.warning(self, "خطأ", "❌ لم يتم العثور على الفاتورة")
            return
        items = db.get_invoice_items(invoice_id)
        client = db.get_client_by_id(inv["client_id"])
        dlg = InvoiceViewDialog(self, inv, items, client)
        dlg.exec_()

    def _edit_invoice_local(self, invoice_id):
        inv = db.get_invoice_by_id(invoice_id)
        if not inv:
            QMessageBox.warning(self, "خطأ", "❌ لم يتم العثور على الفاتورة")
            return
        items = db.get_invoice_items(invoice_id)
        client = db.get_client_by_id(inv["client_id"])
        dlg = InvoiceEditDialog(self, inv, items, client)
        if dlg.exec_() == QDialog.Accepted:
            self._search()

    def _reprint_invoice(self, invoice_id):
        inv = db.get_invoice_by_id(invoice_id)
        if not inv:
            QMessageBox.warning(self, "خطأ", "❌ لم يتم العثور على الفاتورة")
            return
        items = db.get_invoice_items(invoice_id)
        client = db.get_client_by_id(inv["client_id"])
        try:
            pdf_dir = "/home/mohamed/سطح المكتب/فواتير منظومة"
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(
                pdf_dir,
                f"فاتورة_{inv['invoice_number']}_reprint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            invoice_data = {
                "number": inv["invoice_number"],
                "date": inv["date"],
                "total_before_discount": inv["total_before_discount"],
                "discount": inv["discount"],
                "total_after_discount": inv["total_after_discount"],
                "paid_amount": inv["paid_amount"],
                "remaining_amount": inv["remaining_amount"],
                "status": inv["status"],
            }
            generate_invoice_pdf(invoice_data, items, client, pdf_path)
            QMessageBox.information(self, "تم", f"✅ تم إعادة طباعة الفاتورة:\n{pdf_path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ {str(e)}")

    def _delete_invoice(self, invoice_id):
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            "هل أنت متأكد من حذف هذه الفاتورة؟\n⚠️ لا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                db.delete_invoice(invoice_id)
                self._search()
                QMessageBox.information(self, "تم", "✅ تم حذف الفاتورة بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"❌ {str(e)}")

    def _send_telegram_invoice(self, invoice_id):
        inv = db.get_invoice_by_id(invoice_id)
        if not inv:
            QMessageBox.warning(self, "خطأ", "❌ لم يتم العثور على الفاتورة")
            return
        client = db.get_client_by_id(inv["client_id"])
        if not client:
            QMessageBox.warning(self, "خطأ", "❌ لم يتم العثور على العميل")
            return

        secure_code = f"{random.randint(100, 999)}"
        db.save_secure_code(invoice_id, secure_code)

        settings = db.get_company_settings()
        admin_id = settings.get("telegram_admin_id", "").strip()
        token = settings.get("telegram_bot_token", "")

        if not token:
            QMessageBox.warning(self, "خطأ", "❌ لا يوجد توكن بوت Telegram في الإعدادات")
            return

        if not admin_id:
            QMessageBox.warning(self, "تنبيه", "⚠️ لم يتم تعيين Telegram ID للمسؤول في الإعدادات")
            return

        items = db.get_invoice_items(invoice_id)
        os.makedirs("/home/mohamed/سطح المكتب/فواتير منظومة", exist_ok=True)
        pdf_path = os.path.join(
            "/home/mohamed/سطح المكتب/فواتير منظومة",
            f"فاتورة_{inv['invoice_number']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        try:
            invoice_data = {
                "number": inv["invoice_number"],
                "date": inv["date"],
                "total_before_discount": inv["total_before_discount"],
                "discount": inv["discount"],
                "total_after_discount": inv["total_after_discount"],
                "paid_amount": inv["paid_amount"],
                "remaining_amount": inv["remaining_amount"],
                "status": inv["status"],
            }
            generate_invoice_pdf(invoice_data, items, client, pdf_path)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ فشل إنشاء PDF:\n{str(e)}")
            return

        try:
            url_doc = f"https://api.telegram.org/bot{token}/sendDocument"
            url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
            caption = (
                f"📄 فاتورة رقم: {inv['invoice_number']}\n"
                f"العميل: {client.get('name', '')}\n"
                f"الإجمالي: {inv['total_after_discount']:.2f} د.ل\n"
                f"━━━━━━━━━━━━━━\n"
                f"🔐 كود التحقق: {secure_code}\n"
                f"⚠️ أرسل العميل هذا الكود للبوت لاستلام الفاتورة."
            )
            with open(pdf_path, "rb") as f:
                files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
                data = {"chat_id": admin_id, "caption": caption}
                resp = requests.post(url_doc, files=files, data=data, timeout=60)

            if resp.status_code == 200 and resp.json().get("ok"):
                db.log_telegram_send(
                    invoice_id, inv["invoice_number"],
                    client["id"], client.get("name", ""),
                    admin_id, "success",
                    f"✅ تم إرسال الفاتورة وكود التحقق {secure_code} للمسؤول"
                )
                # رفع للسحابة عشان تستقبلها حتى لو الابتوب مقفل
                self._upload_to_cloud(pdf_path, secure_code, client.get("name", ""), inv["total_after_discount"], inv["invoice_number"])
                QMessageBox.information(
                    self, "تم",
                    f"✅ تم إرسال الفاتورة وكود التحقق للمسؤول.\n"
                    f"🔐 كود التحقق: {secure_code}\n"
                    f"على العميل إرسال هذا الكود للبوت لاستلام الفاتورة."
                )
            else:
                err = resp.json().get("description", str(resp.status_code))
                QMessageBox.warning(self, "خطأ", f"❌ فشل الإرسال:\n{err}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"❌ فشل الإرسال:\n{str(e)}")

    def _upload_to_cloud(self, pdf_path, secure_code, client_name, total, invoice_number=""):
        settings = db.get_company_settings()
        cloud_url = (settings.get("cloud_server_url") or "").rstrip("/")
        cloud_api_key = settings.get("cloud_api_key") or ""
        if not cloud_url or not cloud_api_key or not pdf_path or not os.path.exists(pdf_path):
            return
        try:
            with open(pdf_path, "rb") as f:
                files = {"pdf": (os.path.basename(pdf_path), f, "application/pdf")}
                data = {
                    "secure_code": secure_code,
                    "invoice_number": invoice_number,
                    "client_name": client_name,
                    "total": str(total),
                }
                resp = requests.post(
                    f"{cloud_url}/add-invoice",
                    files=files, data=data,
                    headers={"X-API-KEY": cloud_api_key},
                    timeout=30
                )
                if resp.status_code == 200:
                    logging.info(f"Invoice {invoice_number} uploaded to cloud from archive")
                    return True
                else:
                    logging.warning(f"Cloud upload failed from archive: {resp.status_code}")
        except Exception as e:
            logging.warning(f"Cloud upload error from archive: {e}")
        from cloud_sync import add_pending
        add_pending(pdf_path, secure_code, client_name, total, invoice_number)
        return False

    def _generate_report(self):
        inv_num = self.search_number.text().strip()
        client_name = self.search_client.text().strip()
        status = self.search_status.currentText()
        if status == "الكل":
            status = ""
        date_from = self.search_date_from.date().toString("yyyy/MM/dd")
        date_to = self.search_date_to.date().toString("yyyy/MM/dd")
        invoices = db.search_invoices(
            invoice_number=inv_num, client_name=client_name,
            date_from=date_from, date_to=date_to, status=status
        )
        if not invoices:
            QMessageBox.information(self, "تنبيه", "⚠️ لا توجد فواتير لإنشاء التقرير")
            return
        try:
            pdf_dir = "/home/mohamed/سطح المكتب/فواتير منظومة"
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_path = os.path.join(
                pdf_dir,
                f"تقرير_شامل_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            generate_summary_report(invoices, pdf_path)
            QMessageBox.information(self, "تم", f"✅ تم إنشاء التقرير الشامل بنجاح:\n{pdf_path}")

            settings = db.get_company_settings()
            token = settings.get("telegram_bot_token", "")
            admin_id = settings.get("telegram_admin_id", "").strip()
            if token and admin_id:
                try:
                    url = f"https://api.telegram.org/bot{token}/sendDocument"
                    caption = (
                        f"📊 تقرير شامل\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"عدد الفواتير: {len(invoices)}\n"
                        f"الفترة: {self.search_date_from.date().toString('yyyy/MM/dd')} → "
                        f"{self.search_date_to.date().toString('yyyy/MM/dd')}\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"تم إنشاء التقرير بنجاح ✅"
                    )
                    with open(pdf_path, "rb") as f:
                        files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
                        data = {"chat_id": admin_id, "caption": caption}
                        requests.post(url, files=files, data=data, timeout=60)
                except Exception:
                    pass
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ فشل إنشاء التقرير:\n{str(e)}")


class InvoiceViewDialog(QDialog):
    def __init__(self, parent, inv, items, client):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle(f"عرض الفاتورة - {inv['invoice_number']}")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self.setStyleSheet(STYLES["dialog"])
        self.inv = inv
        self.items = items
        self.client = client
        self._build_ui()

    def _build_ui(self):
        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 14, 20, 14)

        title = QLabel(f"📄 الفاتورة: {self.inv['invoice_number']}")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        meta = QFormLayout()
        meta.setLabelAlignment(Qt.AlignRight)
        meta.setSpacing(10)
        meta.addRow("رقم الفاتورة:", QLabel(self.inv["invoice_number"]))
        meta.addRow("التاريخ:", QLabel(self.inv["date"]))
        meta.addRow("العميل:", QLabel(self.client["name"] if self.client else ""))
        meta.addRow("هاتف:", QLabel(self.client["phone"] if self.client else ""))
        tid = self.client.get("telegram_id", "") if self.client else ""
        if tid:
            meta.addRow("Telegram:", QLabel(tid))
        code = self.inv.get("telegram_secure_code") or ""
        if code:
            code_lbl = QLabel(code)
            code_lbl.setStyleSheet(f"color: {PRIMARY}; font-weight: bold; font-size: 14px;")
            meta.addRow("كود التحقق:", code_lbl)
        meta.addRow("الحالة:", QLabel(self.inv["status"]))
        layout.addLayout(meta)

        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "#", "الإجمالي", "الكمية",
            "سعر المتر", "المساحة", "المقاس", "الخدمة"
        ])
        h = table.horizontalHeader()
        stretch_cols = [1, 2, 3, 4, 5, 6]
        for c in range(7):
            if c in stretch_cols:
                h.setSectionResizeMode(c, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        h.setMinimumSectionSize(90)
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setMinimumHeight(120)
        table.setStyleSheet(STYLES["table"])

        for idx, item in enumerate(self.items):
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            table.setItem(row, 1, QTableWidgetItem(f"{item['total']:.2f}"))
            table.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))
            table.setItem(row, 3, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            table.setItem(row, 4, QTableWidgetItem(f"{item['area']:.2f}"))
            table.setItem(row, 5, QTableWidgetItem(f"{item['length']}x{item['width']}"))
            table.setItem(row, 6, QTableWidgetItem(item["service_type"]))
            for col in range(7):
                it = table.item(row, col)
                if it:
                    it.setTextAlignment(Qt.AlignCenter)

        layout.addWidget(table, 1)

        totals = QFormLayout()
        totals.setLabelAlignment(Qt.AlignRight)
        totals.setSpacing(10)
        totals.addRow("الإجمالي قبل الخصم:", QLabel(f"{self.inv['total_before_discount']:.2f} ر.س"))
        totals.addRow("قيمة الخصم:", QLabel(f"{self.inv['discount']:.2f} ر.س"))
        totals.addRow("الإجمالي النهائي:", QLabel(f"{self.inv['total_after_discount']:.2f} ر.س"))
        totals.addRow("المبلغ المدفوع:", QLabel(f"{self.inv['paid_amount']:.2f} ر.س"))

        rem_label = QLabel(f"{self.inv['remaining_amount']:.2f} ر.س")
        rem_label.setStyleSheet(
            f"color: {DANGER}; font-weight: bold; font-size: 15px;"
            if self.inv["remaining_amount"] > 0
            else f"color: {SUCCESS}; font-weight: bold; font-size: 15px;"
        )
        totals.addRow("المبلغ المتبقي:", rem_label)

        if self.inv.get("attachment_path"):
            totals.addRow("الملف المرفق:", QLabel(f"✔️ {os.path.basename(self.inv['attachment_path'])}"))

        layout.addLayout(totals)

        close_btn = QPushButton("❌ إغلاق")
        close_btn.setStyleSheet(
            f"padding: 10px 36px; font-weight: bold; color: white; "
            f"background-color: {BTN_NEUTRAL}; border-radius: 8px; border: none; font-size: 14px;"
        )
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        scroll.setWidget(content)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)


def _item_edit_dialog(parent, item_data):
    dlg = QDialog(parent)
    dlg.setWindowTitle("تعديل البند")
    dlg.setFixedSize(420, 350)
    dlg.setLayoutDirection(Qt.RightToLeft)
    dlg.setStyleSheet(f"""
        QDialog {{ background-color: {CARD}; }}
        QLineEdit {{ padding: 6px 8px; border: 1px solid {BORDER}; border-radius: 6px;
            background-color: {BG}; color: {TEXT}; font-size: 13px; }}
        QSpinBox {{ padding: 6px 8px; border: 1px solid {BORDER}; border-radius: 6px;
            background-color: {BG}; color: {TEXT}; font-size: 13px; }}
    """)
    layout = QVBoxLayout(dlg)
    layout.setSpacing(12)
    layout.setContentsMargins(20, 20, 20, 20)

    title = QLabel("تعديل بيانات البند")
    title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {PRIMARY};")
    title.setAlignment(Qt.AlignCenter)
    layout.addWidget(title)

    form = QFormLayout()
    form.setSpacing(10)
    form.setLabelAlignment(Qt.AlignRight)

    svc = QLineEdit(item_data.get("service_type", ""))
    form.addRow("الخدمة:", svc)

    length = QLineEdit(f"{item_data.get('length', 0)}")
    form.addRow("الطول (م):", length)

    width = QLineEdit(f"{item_data.get('width', 0)}")
    form.addRow("العرض (م):", width)

    price = QLineEdit(f"{item_data.get('unit_price', 0)}")
    form.addRow("سعر المتر:", price)

    qty = QSpinBox()
    qty.setMinimum(1)
    qty.setMaximum(9999)
    qty.setValue(item_data.get("quantity", 1))
    form.addRow("الكمية:", qty)

    layout.addLayout(form)

    btn_row = QHBoxLayout()
    cancel_btn = QPushButton("إلغاء")
    cancel_btn.setStyleSheet(
        f"background-color:{BTN_NEUTRAL}; color:white; padding:8px 24px; "
        f"border-radius:6px; font-weight:bold; border:none;"
    )
    cancel_btn.clicked.connect(dlg.reject)
    btn_row.addWidget(cancel_btn)

    save_btn = QPushButton("حفظ")
    save_btn.setStyleSheet(
        f"background-color:{SUCCESS}; color:white; padding:8px 24px; "
        f"border-radius:6px; font-weight:bold; border:none;"
    )
    save_btn.clicked.connect(lambda: _item_edit_save(dlg, item_data, svc, length, width, price, qty))
    btn_row.addWidget(save_btn)

    layout.addLayout(btn_row)
    return dlg


def _item_edit_save(dlg, item_data, svc, length, width, price, qty):
    try:
        item_data["service_type"] = svc.text().strip()
        item_data["length"] = float(length.text() or 0)
        item_data["width"] = float(width.text() or 0)
        item_data["unit_price"] = float(price.text() or 0)
        item_data["quantity"] = qty.value()
        item_data["area"] = item_data["length"] * item_data["width"]
        item_data["total"] = (item_data["area"] * item_data["unit_price"]) * item_data["quantity"]
        dlg.accept()
    except ValueError:
        QMessageBox.warning(dlg, "خطأ", "الرجاء إدخال أرقام صحيحة")




class InvoiceEditDialog(QDialog):
    def __init__(self, parent, inv, items, client):
        super().__init__(parent)
        self.inv = dict(inv)
        self.items = [dict(it) for it in items]
        self.client = client
        self._changed = False

        self.setWindowTitle(f"تعديل الفاتورة - {inv['invoice_number']}")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setModal(True)
        self.setMinimumSize(850, 650)
        self.resize(950, 750)
        self.setStyleSheet(f"QDialog {{ background-color: {BG}; }}")

        self._build_ui()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(10)
        main.setContentsMargins(20, 14, 20, 14)

        title = QLabel(f"تعديل الفاتورة: {self.inv['invoice_number']}")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        info_group = QGroupBox("معلومات الفاتورة")
        info_group.setStyleSheet(f"""
            QGroupBox {{ font-weight: bold; font-size: 13px; padding-top: 10px;
                background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
                margin-top: 6px; padding: 14px 12px 10px 12px; color: {TEXT_SEC}; }}
        """)
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)

        info_layout.addWidget(QLabel("رقم الفاتورة:"))
        num_label = QLabel(self.inv["invoice_number"])
        num_label.setStyleSheet(f"font-weight:bold; color:{ACCENT}; font-size:14px;")
        info_layout.addWidget(num_label)

        info_layout.addWidget(QLabel("التاريخ:"))
        info_layout.addWidget(QLabel(self.inv["date"]))

        info_layout.addWidget(QLabel("العميل:"))
        info_layout.addWidget(QLabel(self.client["name"] if self.client else ""))

        tid = self.client.get("telegram_id", "") if self.client else ""
        if tid:
            info_layout.addWidget(QLabel("Telegram:"))
            info_layout.addWidget(QLabel(tid))

        info_layout.addStretch()
        info_group.setLayout(info_layout)
        main.addWidget(info_group)

        table_label = QLabel("بنود الفاتورة")
        table_label.setStyleSheet(f"font-weight: bold; color: {TEXT_SEC}; font-size: 13px;")
        main.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "#", "الإجمالي", "الكمية",
            "سعر المتر", "المساحة", "المقاس", "الخدمة"
        ])
        h = self.table.horizontalHeader()
        for c in range(7):
            h.setSectionResizeMode(c, QHeaderView.Stretch)
        h.setMinimumSectionSize(80)
        self.table.setColumnWidth(0, 45)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{ border: 1px solid {BORDER}; gridline-color: {BORDER};
                font-size: 13px; border-radius: 8px; background-color: {CARD};
                alternate-background-color: {TABLE_ALT}; color: {TEXT}; }}
            QHeaderView::section {{ background-color: {TABLE_HEADER}; color: {HEADER_TEXT};
                padding: 8px 6px; font-weight: bold; font-size: 13px; border: none;
                border-bottom: 1px solid {BORDER}; border-right: 1px solid {BORDER}; }}
            QTableWidget::item {{ padding: 6px 4px; border: none; }}
        """)
        self.item_num_spin = QSpinBox()
        self.item_num_spin.setMinimum(1)
        self.item_num_spin.setMaximum(max(1, len(self.items)))
        self.item_num_spin.setFixedWidth(70)

        self._refresh_table()
        main.addWidget(self.table, 1)

        item_edit_row = QHBoxLayout()
        item_edit_row.setSpacing(8)
        item_edit_row.addWidget(QLabel("رقم البند المراد تعديله:"))
        item_edit_row.addWidget(self.item_num_spin)
        edit_item_btn = QPushButton("تعديل البند")
        edit_item_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {WARNING}; color: white; padding: 8px 20px;
                font-weight: bold; border-radius: 6px; border: none; font-size: 13px; }}
            QPushButton:hover {{ background-color: {WARNING_HOVER}; }}
        """)
        edit_item_btn.clicked.connect(self._edit_item)
        item_edit_row.addWidget(edit_item_btn)

        delete_item_btn = QPushButton("حذف البند")
        delete_item_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {DANGER}; color: white; padding: 8px 20px;
                font-weight: bold; border-radius: 6px; border: none; font-size: 13px; }}
            QPushButton:hover {{ background-color: {DANGER_HOVER}; }}
        """)
        delete_item_btn.clicked.connect(self._delete_item)
        item_edit_row.addWidget(delete_item_btn)

        item_edit_row.addStretch()
        main.addLayout(item_edit_row)

        totals_group = QGroupBox("ملخص الفاتورة")
        totals_group.setStyleSheet(f"""
            QGroupBox {{ font-weight: bold; font-size: 13px; padding-top: 10px;
                background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
                margin-top: 6px; padding: 14px 12px 10px 12px; color: {TEXT_SEC}; }}
        """)
        totals_layout = QHBoxLayout()
        totals_layout.setSpacing(14)

        totals_layout.addWidget(QLabel("قبل الخصم:"))
        self.total_before_label = QLabel(f"{self.inv['total_before_discount']:.2f}")
        self.total_before_label.setStyleSheet(f"font-weight:bold; color:{ACCENT}; font-size:14px;")
        totals_layout.addWidget(self.total_before_label)

        totals_layout.addWidget(QLabel("الخصم:"))
        self.discount_input = QLineEdit(f"{self.inv['discount']:.2f}")
        self.discount_input.setFixedWidth(80)
        self.discount_input.textChanged.connect(self._calc)
        totals_layout.addWidget(self.discount_input)

        totals_layout.addWidget(QLabel("النهائي:"))
        self.final_label = QLabel(f"{self.inv['total_after_discount']:.2f}")
        self.final_label.setStyleSheet(f"font-weight:bold; color:{DANGER}; font-size:15px;")
        totals_layout.addWidget(self.final_label)

        totals_layout.addWidget(QLabel("المدفوع:"))
        self.paid_input = QLineEdit(f"{self.inv['paid_amount']:.2f}")
        self.paid_input.setFixedWidth(80)
        self.paid_input.textChanged.connect(self._calc)
        totals_layout.addWidget(self.paid_input)

        totals_layout.addWidget(QLabel("المتبقي:"))
        self.remaining_label = QLabel(f"{self.inv['remaining_amount']:.2f}")
        self.remaining_label.setStyleSheet(
            f"font-weight:bold; font-size:15px; color:{DANGER if self.inv['remaining_amount'] > 0 else SUCCESS};"
        )
        totals_layout.addWidget(self.remaining_label)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["قيد التصميم", "في المطبعة", "جاهز للتركيب", "تم التسليم"])
        idx = self.status_combo.findText(self.inv.get("status", ""))
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        totals_layout.addWidget(QLabel("الحالة:"))
        totals_layout.addWidget(self.status_combo)

        totals_layout.addStretch()
        totals_group.setLayout(totals_layout)
        main.addWidget(totals_group)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {BTN_NEUTRAL}; color: white; padding: 10px 32px;
                font-weight: bold; border-radius: 8px; border: none; font-size: 13px; }}
            QPushButton:hover {{ background-color: {BTN_NEUTRAL_HOVER}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("💾 حفظ التعديلات")
        save_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {SUCCESS}; color: white; padding: 10px 32px;
                font-weight: bold; border-radius: 8px; border: none; font-size: 13px; }}
            QPushButton:hover {{ background-color: {SUCCESS_HOVER}; }}
        """)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        btn_row.addStretch()
        main.addLayout(btn_row)

    def _refresh_table(self):
        self.table.setRowCount(0)
        for idx, item in enumerate(self.items):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 36)
            self.table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(f"{item['total']:.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))
            self.table.setItem(row, 3, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{item['area']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{item['length']}×{item['width']}"))
            self.table.setItem(row, 6, QTableWidgetItem(item["service_type"]))
            for c in range(7):
                it = self.table.item(row, c)
                if it:
                    it.setTextAlignment(Qt.AlignCenter)
        self.item_num_spin.setMaximum(max(1, len(self.items)))

    def _edit_item(self):
        idx = self.item_num_spin.value() - 1
        if idx < 0 or idx >= len(self.items):
            return
        item = self.items[idx]
        dlg = _item_edit_dialog(self, item)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_table()
            self._calc()
            self._changed = True

    def _delete_item(self):
        idx = self.item_num_spin.value() - 1
        if idx < 0 or idx >= len(self.items):
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف البند رقم {idx + 1} ({self.items[idx]['service_type']})؟",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            del self.items[idx]
            self._refresh_table()
            self._calc()
            self._changed = True

    def _calc(self):
        total_before = sum(it["total"] for it in self.items)
        discount = 0.0
        try:
            discount = float(self.discount_input.text() or 0)
        except ValueError:
            pass
        final = max(total_before - discount, 0)
        paid = 0.0
        try:
            paid = float(self.paid_input.text() or 0)
        except ValueError:
            pass
        remaining = max(final - paid, 0)

        self.total_before_label.setText(f"{total_before:.2f}")
        self.final_label.setText(f"{final:.2f}")
        self.remaining_label.setText(f"{remaining:.2f}")
        if remaining > 0:
            self.remaining_label.setStyleSheet(f"font-weight:bold; font-size:15px; color:{DANGER};")
        else:
            self.remaining_label.setStyleSheet(f"font-weight:bold; font-size:15px; color:{SUCCESS};")

    def _save(self):
        total_before = sum(it["total"] for it in self.items)
        try:
            discount = float(self.discount_input.text() or 0)
        except ValueError:
            discount = 0.0
        final = max(total_before - discount, 0)
        try:
            paid = float(self.paid_input.text() or 0)
        except ValueError:
            paid = 0.0
        remaining = max(final - paid, 0)
        status = self.status_combo.currentText()

        try:
            db.update_invoice(
                self.inv["id"], self.inv["client_id"], self.inv["date"],
                total_before, discount, final, paid, remaining,
                status, self.items
            )
            QMessageBox.information(self, "تم", "✅ تم حفظ التعديلات بنجاح")
            self._changed = True
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ فشل الحفظ:\n{str(e)}")

