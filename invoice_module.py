import os
import random
import logging
from datetime import datetime
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QComboBox, QLineEdit, QSpinBox, QPushButton, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QCompleter, QScrollArea
)
import database as db
from pdf_export import generate_invoice_pdf
from colors import *
from telegram_sender import TelegramSender


STYLES = {
    "header": f"font-size: 17px; font-weight: bold; color: {PRIMARY}; padding: 10px; letter-spacing: 1px;",
    "group": f"QGroupBox {{ font-weight: bold; font-size: 13px; padding-top: 12px; color: {TEXT_SEC}; background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; margin-top: 8px; padding: 16px 12px 12px 12px; }}",
    "btn_add_client": f"""
        QPushButton {{ background-color: {PURPLE}; color: white; padding: 7px 16px;
            font-weight: bold; border-radius: 8px; border: none; font-size: 12px; }}
        QPushButton:hover {{ background-color: {PURPLE_HOVER}; }}
    """,
    "btn_primary": f"""
        QPushButton {{ background-color: {ACCENT}; color: white; padding: 9px 24px;
            font-weight: bold; font-size: 13px; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: #1d4ed8; }}
    """,
    "btn_save_print": f"""
        QPushButton {{ background-color: {DANGER}; color: white; padding: 10px 24px;
            font-weight: bold; font-size: 13px; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {DANGER_HOVER}; }}
    """,
    "btn_save": f"""
        QPushButton {{ background-color: {SUCCESS}; color: white; padding: 10px 22px;
            font-weight: bold; font-size: 13px; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {SUCCESS_HOVER}; }}
    """,
    "btn_clear": f"""
        QPushButton {{ background-color: {BTN_NEUTRAL}; color: white; padding: 10px 22px;
            font-weight: bold; font-size: 13px; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {BTN_NEUTRAL_HOVER}; }}
    """,
    "table": f"""
        QTableWidget {{ border: 1px solid {BORDER}; gridline-color: {BORDER};
            font-size: 13px; border-radius: 8px; background-color: {CARD};
            alternate-background-color: {TABLE_ALT}; color: {TEXT}; }}
        QHeaderView::section {{ background-color: {TABLE_HEADER}; color: {HEADER_TEXT};
            padding: 8px 7px; font-weight: bold; border: none;
            border-bottom: 1px solid {BORDER}; border-right: 1px solid {BORDER}; font-size: 13px; }}
        QTableWidget::item {{ padding: 6px 5px; border: none; }}
        QTableWidget::item:selected {{ background-color: rgba(37, 99, 235, 0.12); color: {TEXT}; }}
    """,
    "value_highlight": f"font-size: 14px; font-weight: bold; color: {ACCENT};",
    "total_highlight": f"font-size: 16px; font-weight: bold; color: {DANGER};",
    "remaining_highlight": f"font-size: 15px; font-weight: bold; color: {SUCCESS};",
    "item_total": f"font-weight: bold; color: {WARNING}; font-size: 14px;",
    "delete_btn": f"""
        QPushButton {{ background-color: {DANGER}; color: white; border-radius: 5px;
            padding: 4px 12px; font-weight: bold; font-size: 11px; border: none; }}
        QPushButton:hover {{ background-color: {DANGER_HOVER}; }}
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


class ClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة عميل جديد")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setStyleSheet(STYLES["dialog"])
        self.client_id = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel("➕ إضافة عميل جديد")
        title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {PRIMARY}; padding: 4px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم العميل (إجباري)")
        form.addRow("الاسم:", self.name_input)

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("رقم الهاتف")
        form.addRow("الهاتف:", self.phone_input)

        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("العنوان")
        form.addRow("العنوان:", self.address_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("البريد الإلكتروني")
        form.addRow("البريد:", self.email_input)

        layout.addLayout(form)

        btn_box = QDialogButtonBox()
        save_btn = btn_box.addButton("💾 حفظ", QDialogButtonBox.AcceptRole)
        cancel_btn = btn_box.addButton("❌ إلغاء", QDialogButtonBox.RejectRole)
        save_btn.setStyleSheet(
            f"QPushButton {{ background-color: {SUCCESS}; color: white; "
            f"padding: 9px 28px; font-weight: bold; border-radius: 8px; border: none; "
            f"font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {SUCCESS_HOVER}; }}"
        )
        cancel_btn.setStyleSheet(
            f"QPushButton {{ background-color: {BTN_NEUTRAL}; color: white; "
            f"padding: 9px 28px; font-weight: bold; border-radius: 8px; border: none; "
            f"font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: {BTN_NEUTRAL_HOVER}; }}"
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_accept(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "❌ الرجاء إدخال اسم العميل")
            self.name_input.setFocus()
            return
        try:
            self.client_id = db.add_client(
                name,
                self.phone_input.text().strip(),
                self.address_input.text().strip(),
                self.email_input.text().strip(),
                ""
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء حفظ العميل:\n{str(e)}")


class InvoiceWidget(QWidget):
    scroll_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self.items_list = []
        self.current_invoice_number = None
        self.editing_invoice_id = None
        self.editing_item_index = None
        self._build_ui()
        self._load_clients()
        self._load_services()
        self._refresh_invoice_number()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(8)
        main.setContentsMargins(20, 12, 20, 12)

        self._build_header(main)
        self._build_client_section(main)
        self._build_meta_section(main)
        self._build_item_form(main)
        self._build_item_table(main)
        self._build_totals_section(main)
        self._build_action_buttons(main)

    def _build_header(self, outer):
        hdr = QLabel("📋 نظام إدارة الفواتير - شركة الدعاية والإعلان")
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setStyleSheet(STYLES["header"])
        outer.addWidget(hdr)

    def _build_client_section(self, outer):
        grp = QGroupBox("معلومات العميل")
        grp.setStyleSheet(STYLES["group"])
        row = QHBoxLayout()
        row.setSpacing(12)
        row.setContentsMargins(10, 4, 10, 4)

        label = QLabel("العميل:")
        label.setStyleSheet(f"font-weight: bold; color: {TEXT}; font-size: 13px;")
        row.addWidget(label)

        self.client_combo = QComboBox()
        self.client_combo.setEditable(True)
        self.client_combo.setPlaceholderText("-- ابحث عن عميل أو اختر من القائمة --")
        self.client_combo.setMinimumWidth(260)
        self.client_combo.setInsertPolicy(QComboBox.NoInsert)

        self.client_completer = QCompleter()
        self.client_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.client_completer.setFilterMode(Qt.MatchContains)
        self.client_combo.setCompleter(self.client_completer)

        row.addWidget(self.client_combo, 1)

        add_btn = QPushButton("➕ إضافة عميل جديد")
        add_btn.setStyleSheet(STYLES["btn_add_client"])
        add_btn.clicked.connect(self._open_add_client_dialog)
        row.addWidget(add_btn)

        grp.setLayout(row)
        outer.addWidget(grp)

    def _build_meta_section(self, outer):
        meta_group = QGroupBox("معلومات الفاتورة")
        meta_group.setStyleSheet(STYLES["group"])
        row = QHBoxLayout()
        row.setSpacing(14)
        row.setContentsMargins(10, 4, 10, 4)

        row.addWidget(QLabel("رقم الفاتورة:"))
        self.inv_number_label = QLabel("---")
        self.inv_number_label.setStyleSheet(STYLES["value_highlight"])
        row.addWidget(self.inv_number_label)

        row.addWidget(QLabel("  التاريخ:"))
        self.date_label = QLabel(QDate.currentDate().toString("yyyy/MM/dd"))
        self.date_label.setStyleSheet(f"font-weight: bold; color: {TEXT}; font-size: 13px;")
        row.addWidget(self.date_label)

        row.addStretch()

        row.addWidget(QLabel("حالة الطلب:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["قيد التصميم", "في المطبعة", "جاهز للتركيب", "تم التسليم"])
        self.status_combo.setMinimumWidth(130)
        row.addWidget(self.status_combo)
        meta_group.setLayout(row)
        outer.addWidget(meta_group)

    def _build_item_form(self, outer):
        form_group = QGroupBox("➕ إضافة بند جديد")
        form_group.setStyleSheet(STYLES["group"])
        inner = QVBoxLayout(form_group)
        inner.setSpacing(8)
        inner.setContentsMargins(10, 4, 10, 4)

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 4, 0, 4)

        self.service_combo = QComboBox()
        self.service_combo.setEditable(True)
        self.service_combo.setInsertPolicy(QComboBox.NoInsert)
        self.service_combo.setPlaceholderText("اختر أو اكتب خدمة جديدة")
        self.service_completer = QCompleter()
        self.service_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.service_completer.setFilterMode(Qt.MatchContains)
        self.service_combo.setCompleter(self.service_completer)
        grid.addWidget(QLabel("الخدمة:"), 0, 0)
        grid.addWidget(self.service_combo, 0, 1)
        grid.setColumnStretch(1, 1)
        manage_svc_btn = QPushButton("⚙️")
        manage_svc_btn.setToolTip("إدارة الخدمات")
        manage_svc_btn.setFixedWidth(34)
        manage_svc_btn.setStyleSheet("padding:4px; font-weight:bold; background: transparent;")
        manage_svc_btn.clicked.connect(self._manage_services)
        grid.addWidget(manage_svc_btn, 0, 2)

        grid.addWidget(QLabel("الطول (م):"), 0, 3)
        self.length_input = QLineEdit()
        self.length_input.setPlaceholderText("مثال: 3")
        self.length_input.textChanged.connect(self._calc_item_preview)
        self.length_input.setMaximumWidth(120)
        grid.addWidget(self.length_input, 0, 4)

        grid.addWidget(QLabel("العرض (م):"), 0, 5)
        self.width_input = QLineEdit()
        self.width_input.setPlaceholderText("مثال: 2")
        self.width_input.textChanged.connect(self._calc_item_preview)
        self.width_input.setMaximumWidth(120)
        grid.addWidget(self.width_input, 0, 6)

        grid.addWidget(QLabel("المساحة:"), 0, 7)
        self.area_label = QLabel("0.00 م²")
        self.area_label.setStyleSheet(f"font-weight: bold; color: {ACCENT}; font-size: 14px;")
        grid.addWidget(self.area_label, 0, 8)

        grid.addWidget(QLabel("السعر:"), 1, 0)
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("سعر المتر")
        self.price_input.textChanged.connect(self._calc_item_preview)
        self.price_input.setMaximumWidth(120)
        grid.addWidget(self.price_input, 1, 1)

        grid.addWidget(QLabel("الكمية:"), 1, 2)
        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(9999)
        self.qty_spin.setFixedWidth(100)
        self.qty_spin.valueChanged.connect(self._calc_item_preview)
        grid.addWidget(self.qty_spin, 1, 3)

        grid.addWidget(QLabel("إجمالي البند:"), 1, 4)
        self.item_total_label = QLabel("0.00")
        self.item_total_label.setStyleSheet(STYLES["item_total"])
        grid.addWidget(self.item_total_label, 1, 5)

        inner.addLayout(grid)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.add_item_btn = QPushButton("➕ إضافة إلى الفاتورة")
        self.add_item_btn.setStyleSheet(STYLES["btn_primary"])
        self.add_item_btn.clicked.connect(self._add_item)
        btn_row.addWidget(self.add_item_btn)
        btn_row.addStretch()
        inner.addLayout(btn_row)

        outer.addWidget(form_group)

    def _build_item_table(self, outer):
        table_header = QLabel("📋 بنود الفاتورة")
        table_header.setStyleSheet(f"font-weight: bold; color: {TEXT_SEC}; font-size: 13px; padding: 4px 0;")
        outer.addWidget(table_header)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(8)
        self.items_table.setHorizontalHeaderLabels([
            "#", "نوع الخدمة", "المقاس", "المساحة",
            "سعر المتر", "الكمية", "الإجمالي", "حذف"
        ])
        header = self.items_table.horizontalHeader()
        stretch_cols = [1, 2, 3, 4, 5, 6, 7]
        for c in range(8):
            if c in stretch_cols:
                header.setSectionResizeMode(c, QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(c, QHeaderView.Fixed)
        header.setMinimumSectionSize(90)
        self.items_table.setColumnWidth(0, 45)
        self.items_table.setColumnWidth(7, 70)
        self.items_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setStyleSheet(STYLES["table"])
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.cellDoubleClicked.connect(self._edit_item_from_table)
        outer.addWidget(self.items_table, 1)

    def _build_totals_section(self, outer):
        grp = QGroupBox("ملخص الفاتورة")
        grp.setStyleSheet(STYLES["group"])
        row = QHBoxLayout()
        row.setSpacing(12)
        row.setContentsMargins(10, 4, 10, 4)

        row.addWidget(QLabel("قبل الخصم:"))
        self.total_before_label = QLabel("0.00 ر.س")
        self.total_before_label.setStyleSheet(STYLES["value_highlight"])
        row.addWidget(self.total_before_label)

        row.addWidget(QLabel("الخصم:"))
        self.discount_input = QLineEdit()
        self.discount_input.setPlaceholderText("0")
        self.discount_input.setMaximumWidth(85)
        self.discount_input.textChanged.connect(self._calc_final_totals)
        row.addWidget(self.discount_input)

        row.addWidget(QLabel("النهائي:"))
        self.final_total_label = QLabel("0.00 ر.س")
        self.final_total_label.setStyleSheet(STYLES["total_highlight"])
        row.addWidget(self.final_total_label)

        row.addWidget(QLabel("المدفوع:"))
        self.paid_input = QLineEdit()
        self.paid_input.setPlaceholderText("0")
        self.paid_input.setMaximumWidth(85)
        self.paid_input.textChanged.connect(self._calc_remaining)
        row.addWidget(self.paid_input)

        row.addWidget(QLabel("المتبقي:"))
        self.remaining_label = QLabel("0.00 ر.س")
        self.remaining_label.setStyleSheet(STYLES["remaining_highlight"])
        row.addWidget(self.remaining_label)

        self.telegram_check = QCheckBox("📤 إرسال عبر Telegram")
        self.telegram_check.setStyleSheet(f"""
            QCheckBox {{ font-weight: bold; font-size: 13px; color: {ACCENT}; spacing: 8px;
                padding: 4px 8px; }}
            QCheckBox::indicator {{ width: 20px; height: 20px; border-radius: 4px;
                border: 2px solid {BORDER}; }}
            QCheckBox::indicator:checked {{ background-color: {ACCENT}; border-color: {ACCENT}; }}
        """)
        row.addWidget(self.telegram_check)

        row.addStretch()
        grp.setLayout(row)
        outer.addWidget(grp)

    def _build_action_buttons(self, outer):
        row = QHBoxLayout()
        row.setSpacing(12)
        row.addStretch()

        self.save_print_btn = QPushButton("💾 حفظ وطباعة الفاتورة")
        self.save_print_btn.setStyleSheet(STYLES["btn_save_print"])
        self.save_print_btn.clicked.connect(self._save_and_print)
        row.addWidget(self.save_print_btn)

        self.save_btn = QPushButton("💾 حفظ الفاتورة فقط")
        self.save_btn.setStyleSheet(STYLES["btn_save"])
        self.save_btn.clicked.connect(self._save_only)
        row.addWidget(self.save_btn)

        self.telegram_btn = QPushButton("📤 حفظ وإرسال Telegram")
        self.telegram_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {ACCENT}; color: white; padding: 10px 22px;
                font-weight: bold; font-size: 13px; border-radius: 8px; border: none; }}
            QPushButton:hover {{ background-color: {PRIMARY}; }}
        """)
        self.telegram_btn.clicked.connect(self._save_and_send_telegram)
        row.addWidget(self.telegram_btn)

        self.clear_btn = QPushButton("🗑️ تفريغ الحقول")
        self.clear_btn.setStyleSheet(STYLES["btn_clear"])
        self.clear_btn.clicked.connect(self._clear_all)
        row.addWidget(self.clear_btn)

        row.addStretch()
        outer.addLayout(row)

    def _load_clients(self):
        clients = db.get_clients()
        self.client_combo.blockSignals(True)
        self.client_combo.clear()
        for c in clients:
            key = f"{c['name']}  |  {c['phone']}  |  {c['address']}"
            self.client_combo.addItem(key, c["id"])
        self.client_combo.blockSignals(False)
        self.client_completer.setModel(self.client_combo.model())

    def _get_selected_client_id(self):
        cid = self.client_combo.currentData()
        if cid is not None:
            return cid
        current = self.client_combo.currentText().strip()
        for i in range(self.client_combo.count()):
            if current in self.client_combo.itemText(i):
                return self.client_combo.itemData(i)
        return None

    def _open_add_client_dialog(self):
        dlg = ClientDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_clients()
            if dlg.client_id:
                for i in range(self.client_combo.count()):
                    if self.client_combo.itemData(i) == dlg.client_id:
                        self.client_combo.setCurrentIndex(i)
                        break
            QMessageBox.information(self, "تم", "✅ تم إضافة العميل بنجاح")

    def _load_services(self):
        services = db.get_services()
        self.service_combo.blockSignals(True)
        self.service_combo.clear()
        for s in services:
            self.service_combo.addItem(s["name"])
        self.service_combo.blockSignals(False)
        self.service_completer.setModel(self.service_combo.model())

    def _save_new_service(self, name):
        if not name.strip():
            return
        services = db.get_services()
        existing = [s["name"] for s in services]
        if name not in existing:
            db.add_service(name.strip())
            self._load_services()

    def _manage_services(self):
        dlg = ManageServicesDialog(self)
        dlg.exec_()
        self._load_services()

    def _refresh_invoice_number(self):
        self.current_invoice_number = db.get_next_invoice_number()
        self.inv_number_label.setText(self.current_invoice_number)

    def _to_float(self, val):
        if not val or not val.strip():
            return 0.0
        try:
            return float(val.strip().replace(",", "."))
        except ValueError:
            return 0.0

    def _calc_item_preview(self):
        length = self._to_float(self.length_input.text())
        width = self._to_float(self.width_input.text())
        area = length * width
        self.area_label.setText(f"{area:.2f} م²")

        price = self._to_float(self.price_input.text())
        qty = self.qty_spin.value()
        item_total = (area * price) * qty
        self.item_total_label.setText(f"{item_total:.2f}")

    def _add_item(self):
        length = self._to_float(self.length_input.text())
        width = self._to_float(self.width_input.text())
        price = self._to_float(self.price_input.text())

        if length <= 0 or width <= 0:
            QMessageBox.warning(
                self, "خطأ في الإدخال",
                "❌ الرجاء إدخال قيم صحيحة للطول والعرض (أرقام موجبة)"
            )
            return
        if price < 0:
            QMessageBox.warning(self, "خطأ في الإدخال", "❌ سعر المتر يجب أن يكون رقماً صحيحاً")
            return

        area = length * width
        qty = self.qty_spin.value()
        item_total = (area * price) * qty

        svc_name = self.service_combo.currentText().strip()
        self._save_new_service(svc_name)

        item = {
            "service_type": svc_name,
            "length": length,
            "width": width,
            "area": area,
            "unit_price": price,
            "quantity": qty,
            "total": item_total,
        }

        if self.editing_item_index is not None:
            self.items_list[self.editing_item_index] = item
            self.editing_item_index = None
            self.add_item_btn.setText("➕ إضافة إلى الفاتورة")
        else:
            self.items_list.append(item)

        self._rebuild_table()
        self._update_invoice_totals()
        self._clear_item_form()

    def _edit_item_from_table(self, row, col):
        if row < 0 or row >= len(self.items_list):
            return
        item = self.items_list[row]
        self.editing_item_index = row
        self.service_combo.setEditText(item["service_type"])
        self.length_input.setText(f"{item['length']}")
        self.width_input.setText(f"{item['width']}")
        self.price_input.setText(f"{item['unit_price']}")
        self.qty_spin.setValue(item["quantity"])
        self.add_item_btn.setText("✅ تحديث البند")
        self._calc_item_preview()
        self.length_input.setFocus()
        self.scroll_requested.emit(0)

    def _remove_item(self, index):
        if 0 <= index < len(self.items_list):
            reply = QMessageBox.question(
                self, "تأكيد الحذف", "هل أنت متأكد من حذف هذا البند؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.items_list[index]
        self._rebuild_table()
        self._update_invoice_totals()
        self.scroll_requested.emit(0)

    def _rebuild_table(self):
        self.items_table.setRowCount(0)
        for idx, item in enumerate(self.items_list):
            row = self.items_table.rowCount()
            self.items_table.insertRow(row)
            self.items_table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            self.items_table.setItem(row, 1, QTableWidgetItem(item["service_type"]))
            size_str = f"{item['length']:.2f} × {item['width']:.2f}"
            self.items_table.setItem(row, 2, QTableWidgetItem(size_str))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{item['area']:.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            self.items_table.setItem(row, 5, QTableWidgetItem(str(item["quantity"])))
            self.items_table.setItem(row, 6, QTableWidgetItem(f"{item['total']:.2f}"))
            del_btn = QPushButton("حذف")
            del_btn.setStyleSheet(STYLES["delete_btn"])
            del_btn.clicked.connect(lambda checked, i=idx: self._remove_item(i))
            self.items_table.setCellWidget(row, 7, del_btn)
            for col in range(7):
                self.items_table.item(row, col).setTextAlignment(Qt.AlignCenter)
        pass

    def _clear_item_form(self):
        self.length_input.clear()
        self.width_input.clear()
        self.price_input.clear()
        self.qty_spin.setValue(1)
        self.service_combo.setCurrentIndex(0)
        self.area_label.setText("0.00 م²")
        self.item_total_label.setText("0.00")
        self.editing_item_index = None
        self.add_item_btn.setText("➕ إضافة إلى الفاتورة")

    def _update_invoice_totals(self):
        total = sum(item["total"] for item in self.items_list)
        self.total_before_label.setText(f"{total:.2f} ر.س")
        self._calc_final_totals()

    def _get_total_before(self):
        return sum(item["total"] for item in self.items_list)

    def _calc_final_totals(self):
        total_before = self._get_total_before()
        discount = self._to_float(self.discount_input.text())
        final = max(total_before - discount, 0)
        self.final_total_label.setText(f"{final:.2f} ر.س")
        self._calc_remaining()

    def _calc_remaining(self):
        total_before = self._get_total_before()
        discount = self._to_float(self.discount_input.text())
        final = max(total_before - discount, 0)
        paid = self._to_float(self.paid_input.text())
        remaining = max(final - paid, 0)
        self.remaining_label.setText(f"{remaining:.2f} ر.س")

    def _get_final_total(self):
        total_before = self._get_total_before()
        discount = self._to_float(self.discount_input.text())
        return max(total_before - discount, 0)

    def load_invoice(self, invoice_id):
        inv = db.get_invoice_by_id(invoice_id)
        if not inv:
            QMessageBox.warning(self, "خطأ", "❌ لم يتم العثور على الفاتورة")
            return
        items = db.get_invoice_items(invoice_id)
        self._clear_all(skip_confirm=True)
        self.editing_invoice_id = invoice_id
        self.current_invoice_number = inv["invoice_number"]
        self.inv_number_label.setText(self.current_invoice_number)
        client_key = f"{inv.get('client_name', '')}  |  {inv.get('client_phone', '')}  |  {inv.get('client_address', '')}"
        idx = self.client_combo.findText(client_key)
        if idx >= 0:
            self.client_combo.setCurrentIndex(idx)
        else:
            for i in range(self.client_combo.count()):
                if inv.get("client_name", "") in self.client_combo.itemText(i):
                    self.client_combo.setCurrentIndex(i)
                    break
            else:
                self.client_combo.setEditText(inv.get("client_name", ""))
        self.discount_input.setText(f"{inv['discount']:.2f}")
        self.paid_input.setText(f"{inv['paid_amount']:.2f}")
        status_idx = self.status_combo.findText(inv["status"])
        if status_idx >= 0:
            self.status_combo.setCurrentIndex(status_idx)
        self.items_list = []
        for item in items:
            self.items_list.append({
                "service_type": item["service_type"],
                "length": item["length"],
                "width": item["width"],
                "area": item["area"],
                "unit_price": item["unit_price"],
                "quantity": item["quantity"],
                "total": item["total"],
            })
        self._rebuild_table()
        self._update_invoice_totals()

    def _validate_before_save(self):
        if not self.items_list:
            QMessageBox.warning(self, "تنبيه", "❌ لا توجد بنود في الفاتورة.\nالرجاء إضافة بند واحد على الأقل.")
            return False
        client_id = self._get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "تنبيه", "❌ الرجاء اختيار عميل من القائمة")
            return False
        return True

    def auto_save(self):
        if not self.items_list:
            return False
        client_id = self._get_selected_client_id()
        if client_id is None:
            return False
        date_str = QDate.currentDate().toString("yyyy/MM/dd")
        total_before = self._get_total_before()
        discount = self._to_float(self.discount_input.text())
        final_total = max(total_before - discount, 0)
        paid = self._to_float(self.paid_input.text())
        remaining = max(final_total - paid, 0)
        status = self.status_combo.currentText()
        try:
            if self.editing_invoice_id:
                db.update_invoice(
                    self.editing_invoice_id, client_id, date_str,
                    total_before, discount, final_total, paid, remaining,
                    status, self.items_list
                )
            else:
                db.save_invoice(
                    self.current_invoice_number, client_id, date_str,
                    total_before, discount, final_total, paid, remaining,
                    status, self.items_list
                )
            self._clear_all()
            return True
        except Exception:
            return False

    def _do_save(self, generate_pdf=False, force_telegram=False):
        if not self._validate_before_save():
            return False
        client_id = self._get_selected_client_id()
        date_str = QDate.currentDate().toString("yyyy/MM/dd")
        total_before = self._get_total_before()
        discount = self._to_float(self.discount_input.text())
        final_total = max(total_before - discount, 0)
        paid = self._to_float(self.paid_input.text())
        remaining = max(final_total - paid, 0)
        status = self.status_combo.currentText()
        invoice_id = None
        try:
            if self.editing_invoice_id:
                db.update_invoice(
                    self.editing_invoice_id, client_id, date_str,
                    total_before, discount, final_total, paid, remaining,
                    status, self.items_list
                )
                invoice_id = self.editing_invoice_id
            else:
                invoice_id = db.save_invoice(
                    self.current_invoice_number, client_id, date_str,
                    total_before, discount, final_total, paid, remaining,
                    status, self.items_list
                )
        except Exception as e:
            QMessageBox.critical(self, "خطأ في الحفظ", f"❌ حدث خطأ أثناء حفظ الفاتورة:\n{str(e)}")
            return False

        secure_code = None
        send_telegram = force_telegram or self.telegram_check.isChecked()
        if send_telegram or generate_pdf:
            secure_code = f"{random.randint(100, 999)}"
            db.save_secure_code(invoice_id, secure_code)

        pdf_path = None

        if generate_pdf or send_telegram:
            try:
                client = db.get_client_by_id(client_id)
                pdf_dir = "/home/mohamed/سطح المكتب/فواتير منظومة"
                os.makedirs(pdf_dir, exist_ok=True)
                pdf_path = os.path.join(
                    pdf_dir,
                    f"فاتورة_{self.current_invoice_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                )
                invoice_data = {
                    "number": self.current_invoice_number,
                    "date": date_str,
                    "total_before_discount": total_before,
                    "discount": discount,
                    "total_after_discount": final_total,
                    "paid_amount": paid,
                    "remaining_amount": remaining,
                    "status": status,
                }
                generate_invoice_pdf(invoice_data, self.items_list, client, pdf_path)
            except Exception as e:
                QMessageBox.warning(
                    self, "خطأ في PDF",
                    f"❌ حدث خطأ أثناء إنشاء PDF:\n{str(e)}"
                )
                if generate_pdf:
                    return False

        if send_telegram and secure_code:
            settings = db.get_company_settings()
            admin_id = settings.get("telegram_admin_id", "").strip()
            token = settings.get("telegram_bot_token", "").strip()
            if admin_id and token:
                client_info = db.get_client_by_id(client_id)
                cname = client_info["name"] if client_info else ""
                if pdf_path and os.path.exists(pdf_path):
                    self._send_pdf_to_admin(pdf_path, secure_code, admin_id, token, cname)
                else:
                    self._notify_admin_code(admin_id, secure_code, cname)
                self._upload_to_cloud(pdf_path, secure_code, cname, final_total)
            else:
                QMessageBox.warning(
                    self, "تنبيه",
                    "⚠️ لم يتم تعيين Telegram ID للمسؤول في الإعدادات.\n"
                    "الرجاء ضبطه من قسم الإعدادات."
                )
        elif force_telegram and not pdf_path:
            QMessageBox.warning(self, "خطأ", "❌ لم يتم إنشاء ملف PDF")

        if generate_pdf:
            msg = (
                f"✅ تم حفظ الفاتورة رقم {self.current_invoice_number} بنجاح\n"
                f"📄 تم إنشاء ملف PDF:\n{pdf_path}"
            )
            if secure_code:
                msg += f"\n🔐 كود الاستلام عبر Telegram: {secure_code}"
            QMessageBox.information(self, "تم الحفظ والطباعة", msg)
        elif not send_telegram:
            msg = f"✅ تم حفظ الفاتورة رقم {self.current_invoice_number} بنجاح"
            if secure_code:
                msg += f"\n🔐 كود الاستلام عبر Telegram: {secure_code}"
            QMessageBox.information(self, "تم الحفظ", msg)
        else:
            msg = f"✅ تم حفظ الفاتورة رقم {self.current_invoice_number} بنجاح"
            if secure_code:
                msg += f"\n🔐 كود الاستلام عبر Telegram: {secure_code}"
            QMessageBox.information(self, "تم الحفظ والإرسال", msg)
        self._clear_all()
        return True

    def _send_pdf_to_admin(self, pdf_path, secure_code, admin_id, token, client_name=""):
        """يرسل PDF الفاتورة + كود التحقق للمسؤول عبر تلجرام."""
        try:
            import requests
            url_doc = f"https://api.telegram.org/bot{token}/sendDocument"
            caption = (
                f"📄 فاتورة رقم: {self.current_invoice_number}\n"
                f"العميل: {client_name}\n"
                f"━━━━━━━━━━━━━━\n"
                f"🔐 كود التحقق: {secure_code}\n"
                f"⚠️ أرسل العميل هذا الكود للبوت لاستلام الفاتورة."
            )
            with open(pdf_path, "rb") as f:
                files = {"document": (os.path.basename(pdf_path), f, "application/pdf")}
                data = {"chat_id": admin_id, "caption": caption}
                resp = requests.post(url_doc, files=files, data=data, timeout=60)
            if resp.status_code == 200 and resp.json().get("ok"):
                logging.info(f"PDF + code sent to admin for invoice {self.current_invoice_number}")
            else:
                err = resp.json().get("description", str(resp.status_code))
                QMessageBox.warning(self, "خطأ", f"❌ فشل إرسال PDF للمسؤول:\n{err}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"❌ فشل إرسال PDF للمسؤول:\n{str(e)}")

    def _notify_admin_code(self, admin_id, secure_code, client_name=""):
        settings = db.get_company_settings()
        token = settings.get("telegram_bot_token", "")
        if not token:
            QMessageBox.warning(self, "خطأ", "❌ لا يوجد توكن بوت Telegram في الإعدادات")
            return
        try:
            import requests
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            msg = (
                f"🔐 كود استلام فاتورة جديد\n"
                f"━━━━━━━━━━━━━━\n"
                f"رقم الفاتورة: {self.current_invoice_number}\n"
                f"العميل: {client_name}\n"
                f"كود التحقق: {secure_code}\n"
                f"━━━━━━━━━━━━━━\n"
                f"⚠️ يجب على العميل إرسال هذا الكود للبوت لاستلام الفاتورة.\n"
                f"الكود صالح للاستخدام مرة واحدة فقط."
            )
            resp = requests.post(url, data={"chat_id": admin_id, "text": msg}, timeout=10)
            if resp.status_code != 200:
                err = resp.json().get("description", str(resp.status_code))
                QMessageBox.warning(self, "خطأ", f"❌ فشل إرسال الإشعار للمسؤول:\n{err}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"❌ فشل إرسال الإشعار للمسؤول:\n{str(e)}")

    def _upload_to_cloud(self, pdf_path, secure_code, client_name, total):
        """يرفع الفاتورة + الكود للسيرفر السحابي عشان العميل يقدر يستلمها لما الابتوب يكون مقفل."""
        settings = db.get_company_settings()
        cloud_url = (settings.get("cloud_server_url") or "").rstrip("/")
        cloud_api_key = settings.get("cloud_api_key") or ""
        if not cloud_url or not cloud_api_key or not pdf_path or not os.path.exists(pdf_path):
            return
        try:
            import requests
            with open(pdf_path, "rb") as f:
                files = {"pdf": (os.path.basename(pdf_path), f, "application/pdf")}
                data = {
                    "secure_code": secure_code,
                    "invoice_number": self.current_invoice_number,
                    "client_name": client_name,
                    "total": str(total),
                }
                resp = requests.post(
                    f"{cloud_url}/add-invoice",
                    files=files,
                    data=data,
                    headers={"X-API-KEY": cloud_api_key},
                    timeout=30
                )
                if resp.status_code == 200:
                    logging.info(f"Invoice {self.current_invoice_number} uploaded to cloud")
                    return True
                else:
                    logging.warning(f"Cloud upload failed: {resp.status_code}")
        except Exception as e:
            logging.warning(f"Cloud upload error: {e}")
        # فشل → نحطها في قائمة الانتظار عشان نعيد المحاولة لاحقاً
        from cloud_sync import add_pending
        add_pending(pdf_path, secure_code, client_name, total, self.current_invoice_number)
        return False

    def _send_via_telegram(self, pdf_path, invoice_id, client_id, client_name, telegram_id, total=0, secure_code=""):
        settings = db.get_company_settings()
        admin_id = settings.get("telegram_admin_id", "")
        self.sender_thread = TelegramSender(
            pdf_path, invoice_id, self.current_invoice_number,
            client_id, client_name, telegram_id, total, admin_id, secure_code
        )
        self.sender_thread.finished.connect(self._on_telegram_sent)
        self.sender_thread.start()

    def _on_telegram_sent(self, success, message):
        if success:
            QMessageBox.information(self, "Telegram", f"✅ {message}")
        else:
            QMessageBox.warning(self, "Telegram", f"❌ {message}")
        self.sender_thread.deleteLater()

    def _save_and_print(self):
        self._do_save(generate_pdf=True)

    def _save_only(self):
        self._do_save(generate_pdf=False)

    def _save_and_send_telegram(self):
        self._do_save(generate_pdf=False, force_telegram=True)

    def _clear_all(self, skip_confirm=False):
        if self.items_list and not skip_confirm:
            reply = QMessageBox.question(
                self, "تأكيد التفريغ", "سيتم مسح جميع البيانات المدخلة. هل أنت متأكد؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        self.items_list.clear()
        self.editing_invoice_id = None
        self.items_table.setRowCount(0)
        self._clear_item_form()
        self.discount_input.clear()
        self.paid_input.clear()
        self.total_before_label.setText("0.00 ر.س")
        self.final_total_label.setText("0.00 ر.س")
        self.remaining_label.setText("0.00 ر.س")
        self.status_combo.setCurrentIndex(0)
        self.client_combo.setCurrentText("")
        self._refresh_invoice_number()


class ManageServicesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إدارة الخدمات")
        self.setLayoutDirection(Qt.RightToLeft)
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(STYLES["dialog"])
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("⚙️ إدارة أنواع الخدمات")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QHBoxLayout()
        self.new_svc_input = QLineEdit()
        self.new_svc_input.setPlaceholderText("اكتب اسم خدمة جديدة...")
        form.addWidget(self.new_svc_input, 1)
        add_btn = QPushButton("➕ إضافة")
        add_btn.setStyleSheet(
            f"background-color:{SUCCESS}; color:white; "
            f"padding:8px 20px; font-weight:bold; border-radius:8px; border:none; font-size:13px;"
        )
        add_btn.clicked.connect(self._add)
        self.new_svc_input.returnPressed.connect(self._add)
        form.addWidget(add_btn)
        layout.addLayout(form)

        self.services_list = QTableWidget()
        self.services_list.setColumnCount(2)
        self.services_list.setHorizontalHeaderLabels(["الخدمة", "حذف"])
        h = self.services_list.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Stretch)
        self.services_list.verticalHeader().setVisible(False)
        self.services_list.setStyleSheet(STYLES["table"])
        layout.addWidget(self.services_list, 1)

        close_btn = QPushButton("❌ إغلاق")
        close_btn.setStyleSheet(
            f"padding: 9px 28px; font-weight: bold; color: white; "
            f"background-color: {BTN_NEUTRAL}; border-radius: 8px; border: none; font-size: 13px;"
        )
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

    def _load(self):
        services = db.get_services()
        self.services_list.setRowCount(0)
        for idx, s in enumerate(services):
            row = self.services_list.rowCount()
            self.services_list.insertRow(row)
            self.services_list.setItem(row, 0, QTableWidgetItem(s["name"]))
            del_btn = QPushButton("🗑️")
            del_btn.setStyleSheet(
                f"background-color:{DANGER}; color:white; "
                f"border-radius:5px; padding:4px 12px; border:none; font-size:12px;"
            )
            del_btn.clicked.connect(lambda checked, sid=s["id"]: self._delete(sid))
            self.services_list.setCellWidget(row, 1, del_btn)

    def _add(self):
        name = self.new_svc_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "❌ الرجاء إدخال اسم الخدمة")
            return
        result = db.add_service(name)
        if result is None:
            QMessageBox.warning(self, "تنبيه", "⚠️ هذه الخدمة موجودة مسبقاً")
        else:
            self.new_svc_input.clear()
            self._load()

    def _delete(self, service_id):
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     "هل أنت متأكد من حذف هذه الخدمة؟",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.delete_service(service_id)
            self._load()
