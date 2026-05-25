import os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTabWidget,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import database as db
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
    "alert_banner": f"""
        QLabel {{ background-color: #332822; color: {WARNING};
            padding: 10px; font-weight: bold; border-radius: 8px;
            border: 1px solid {WARNING}; }}
    """,
    "btn_add": f"""
        QPushButton {{ background-color: {SUCCESS}; color: white;
            padding: 8px 20px; font-weight: bold; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {SUCCESS_HOVER}; }}
    """,
    "btn_del": f"""
        QPushButton {{ background-color: {DANGER}; color: white;
            padding: 8px 20px; font-weight: bold; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {DANGER_HOVER}; }}
    """,
    "btn_edit": f"""
        QPushButton {{ background-color: {WARNING}; color: white;
            padding: 8px 20px; font-weight: bold; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: {WARNING_HOVER}; }}
    """,
    "btn_action": f"""
        QPushButton {{ background-color: {ACCENT}; color: white;
            padding: 8px 20px; font-weight: bold; border-radius: 8px; border: none; }}
        QPushButton:hover {{ background-color: #1d4ed8; }}
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

TAB_STYLE = f"""
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: 8px;
        background-color: transparent;
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {TAB_BG};
        color: {TEXT_SEC};
        padding: 9px 20px;
        margin-right: 3px;
        font-weight: bold;
        font-size: 13px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        border: 1px solid transparent;
        border-bottom: none;
    }}
    QTabBar::tab:selected {{
        background-color: {CARD};
        color: {ACCENT};
        border-color: {BORDER};
        border-bottom: 2px solid {ACCENT};
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {TAB_HOVER};
        color: {TEXT};
    }}
"""


class MaterialDialog(QDialog):
    def __init__(self, parent=None, material=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إضافة مادة" if not material else "تعديل مادة")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet(STYLES["dialog"])
        self.material = material
        self._build_ui()
        if material:
            self._load(material)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        title = QLabel("➕ إضافة مادة جديدة" if not self.material else "✏️ تعديل المادة")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PRIMARY}; padding: 4px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("اسم المادة (مثال: رول بنر)")
        form.addRow("الاسم:", self.name_input)

        self.unit_input = QComboBox()
        self.unit_input.addItems(["متر", "رول", "كجم", "قطعة", "متر مربع", "لتر"])
        self.unit_input.setEditable(True)
        form.addRow("الوحدة:", self.unit_input)

        self.min_qty_input = QDoubleSpinBox()
        self.min_qty_input.setRange(0, 999999)
        self.min_qty_input.setValue(5)
        self.min_qty_input.setDecimals(1)
        form.addRow("حد الأمان (أقل كمية):", self.min_qty_input)

        self.price_input = QDoubleSpinBox()
        self.price_input.setRange(0, 999999)
        self.price_input.setValue(0)
        self.price_input.setDecimals(2)
        form.addRow("سعر الوحدة:", self.price_input)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("ملاحظات إضافية...")
        form.addRow("ملاحظات:", self.notes_input)

        layout.addLayout(form)

        btn_box = QDialogButtonBox()
        save_btn = btn_box.addButton("💾 حفظ", QDialogButtonBox.AcceptRole)
        cancel_btn = btn_box.addButton("❌ إلغاء", QDialogButtonBox.RejectRole)
        save_btn.setStyleSheet(
            f"background-color:{SUCCESS}; color:white; "
            f"padding:9px 28px; font-weight:bold; border-radius:8px; border:none; font-size:13px;"
        )
        cancel_btn.setStyleSheet(
            f"background-color:{BTN_NEUTRAL}; color:white; "
            f"padding:9px 28px; font-weight:bold; border-radius:8px; border:none; font-size:13px;"
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load(self, m):
        self.name_input.setText(m["name"])
        idx = self.unit_input.findText(m["unit"])
        if idx >= 0:
            self.unit_input.setCurrentIndex(idx)
        else:
            self.unit_input.setEditText(m["unit"])
        self.min_qty_input.setValue(m["min_quantity"])
        self.price_input.setValue(m["unit_price"])
        self.notes_input.setPlainText(m.get("notes", ""))

    def _on_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "تنبيه", "❌ الرجاء إدخال اسم المادة")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "unit": self.unit_input.currentText().strip(),
            "min_qty": self.min_qty_input.value(),
            "price": self.price_input.value(),
            "notes": self.notes_input.toPlainText().strip(),
        }


class StockDialog(QDialog):
    def __init__(self, parent=None, material=None, invoice_id=None):
        super().__init__(parent)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setWindowTitle("إضافة حركة مخزنية")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet(STYLES["dialog"])
        self.material = material
        self.invoice_id = invoice_id
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        title = QLabel("📦 إضافة حركة للمخزن")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PRIMARY}; padding: 4px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        if self.material:
            ml = QLabel(self.material["name"])
            ml.setStyleSheet("font-weight: bold;")
            form.addRow("المادة:", ml)
        else:
            self.material_combo = QComboBox()
            self._load_materials()
            form.addRow("المادة:", self.material_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["add", "remove", "consume"])
        self.type_combo.setItemText(0, "🔵 إضافة (ورود)")
        self.type_combo.setItemText(1, "🔴 صرف (خروج)")
        self.type_combo.setItemText(2, "🟡 استهلاك (إنتاج)")
        form.addRow("نوع الحركة:", self.type_combo)

        self.qty_input = QDoubleSpinBox()
        self.qty_input.setRange(0.01, 999999)
        self.qty_input.setValue(1)
        self.qty_input.setDecimals(2)
        form.addRow("الكمية:", self.qty_input)

        self.date_input = QLineEdit(QDate.currentDate().toString("yyyy/MM/dd"))
        form.addRow("التاريخ:", self.date_input)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("ملاحظات...")
        form.addRow("ملاحظات:", self.notes_input)

        layout.addLayout(form)

        btn_box = QDialogButtonBox()
        save_btn = btn_box.addButton("💾 تسجيل", QDialogButtonBox.AcceptRole)
        cancel_btn = btn_box.addButton("❌ إلغاء", QDialogButtonBox.RejectRole)
        save_btn.setStyleSheet(
            f"background-color:{ACCENT}; color:white; "
            f"padding:9px 28px; font-weight:bold; border-radius:8px; border:none; font-size:13px;"
        )
        cancel_btn.setStyleSheet(
            f"background-color:{BTN_NEUTRAL}; color:white; "
            f"padding:9px 28px; font-weight:bold; border-radius:8px; border:none; font-size:13px;"
        )
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_materials(self):
        mats = db.get_materials()
        self.material_combo.clear()
        for m in mats:
            self.material_combo.addItem(m["name"], m["id"])

    def _on_accept(self):
        if not self.material:
            if self.material_combo.currentIndex() < 0:
                QMessageBox.warning(self, "تنبيه", "❌ الرجاء اختيار المادة")
                return
        self.accept()

    def get_data(self):
        t = self.type_combo.currentText()
        if "إضافة" in t:
            ttype = "add"
        elif "صرف" in t:
            ttype = "remove"
        else:
            ttype = "consume"
        qty = self.qty_input.value()
        if ttype in ("remove", "consume"):
            qty = -qty
        mat_id = self.material["id"] if self.material else self.material_combo.currentData()
        return {
            "material_id": mat_id,
            "change_amount": qty,
            "trans_type": ttype,
            "date": self.date_input.text().strip(),
            "invoice_id": self.invoice_id,
            "notes": self.notes_input.text().strip(),
        }


class InventoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(8)
        main.setContentsMargins(20, 12, 20, 12)

        title = QLabel("📦 نظام إدارة المخازن والجرد")
        title.setStyleSheet(STYLES["title"])
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        self.alert_banner = QLabel()
        self.alert_banner.setVisible(False)
        self.alert_banner.setStyleSheet(STYLES["alert_banner"])
        self.alert_banner.setWordWrap(True)
        main.addWidget(self.alert_banner)

        self.tabs = QTabWidget()
        self.tabs.setLayoutDirection(Qt.RightToLeft)
        self.tabs.setStyleSheet(TAB_STYLE)

        self._build_materials_tab()
        self._build_transactions_tab()
        self._build_audit_tab()

        main.addWidget(self.tabs, 1)

        row = QHBoxLayout()
        row.addStretch()
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setStyleSheet(STYLES["btn_action"])
        refresh_btn.clicked.connect(self._refresh)
        row.addWidget(refresh_btn)
        main.addLayout(row)

    def _build_materials_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        row = QHBoxLayout()
        add_btn = QPushButton("➕ إضافة مادة جديدة")
        add_btn.setStyleSheet(STYLES["btn_add"])
        add_btn.clicked.connect(self._add_material)
        row.addWidget(add_btn)
        row.addStretch()
        layout.addLayout(row)

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(7)
        self.materials_table.setHorizontalHeaderLabels([
            "#", "اسم المادة", "الوحدة", "الكمية الحالية",
            "حد الأمان", "سعر الوحدة", "ملاحظات"
        ])
        h = self.materials_table.horizontalHeader()
        stretch_cols = [1, 2, 3, 4, 5, 6]
        for c in range(7):
            if c in stretch_cols:
                h.setSectionResizeMode(c, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        h.setMinimumSectionSize(80)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setStyleSheet(STYLES["table"])
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.materials_table, 1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        edit_btn = QPushButton("✏️ تعديل")
        edit_btn.setStyleSheet(STYLES["btn_edit"])
        edit_btn.clicked.connect(self._edit_material)
        row2.addWidget(edit_btn)

        del_btn = QPushButton("🗑️ حذف")
        del_btn.setStyleSheet(STYLES["btn_del"])
        del_btn.clicked.connect(self._delete_material)
        row2.addWidget(del_btn)

        stock_btn = QPushButton("📦 حركة مخزنية")
        stock_btn.setStyleSheet(STYLES["btn_action"])
        stock_btn.clicked.connect(self._stock_transaction)
        row2.addWidget(stock_btn)

        row2.addStretch()
        layout.addLayout(row2)

        self.tabs.addTab(tab, "📦 المواد الخام")

    def _build_transactions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(QLabel("تصفية حسب المادة:"))
        self.trans_filter = QComboBox()
        self.trans_filter.addItem("الكل", None)
        row.addWidget(self.trans_filter)
        row.addStretch()
        layout.addLayout(row)

        self.trans_table = QTableWidget()
        self.trans_table.setColumnCount(7)
        self.trans_table.setHorizontalHeaderLabels([
            "#", "التاريخ", "المادة", "نوع الحركة",
            "الكمية", "رقم الفاتورة", "ملاحظات"
        ])
        h = self.trans_table.horizontalHeader()
        stretch_cols = [1, 2, 3, 4, 5, 6]
        for c in range(7):
            if c in stretch_cols:
                h.setSectionResizeMode(c, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        h.setMinimumSectionSize(80)
        self.trans_table.setAlternatingRowColors(True)
        self.trans_table.setStyleSheet(STYLES["table"])
        self.trans_table.verticalHeader().setVisible(False)
        layout.addWidget(self.trans_table, 1)

        self.trans_filter.currentIndexChanged.connect(self._refresh_transactions)
        self.tabs.addTab(tab, "📋 سجل الحركات")

    def _build_audit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        layout.addWidget(QLabel(
            f"<b style='color:{TEXT_SEC}'>📊 الجرد بأثر رجعي</b> - مراجعة المواد المستهلكة في الفواتير"
        ))

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(QLabel("رقم الفاتورة:"))
        self.audit_inv_input = QLineEdit()
        self.audit_inv_input.setPlaceholderText("بحث...")
        row.addWidget(self.audit_inv_input)

        search_btn = QPushButton("🔍 بحث")
        search_btn.setStyleSheet(STYLES["btn_action"])
        search_btn.clicked.connect(self._audit_search)
        row.addWidget(search_btn)
        row.addStretch()
        layout.addLayout(row)

        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(5)
        self.audit_table.setHorizontalHeaderLabels([
            "#", "المادة", "الوحدة", "الكمية المستهلكة", "تاريخ الحركة"
        ])
        h = self.audit_table.horizontalHeader()
        stretch_cols = [1, 2, 3, 4]
        for c in range(5):
            if c in stretch_cols:
                h.setSectionResizeMode(c, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        h.setMinimumSectionSize(80)
        self.audit_table.setAlternatingRowColors(True)
        self.audit_table.setStyleSheet(STYLES["table"])
        self.audit_table.verticalHeader().setVisible(False)
        layout.addWidget(self.audit_table, 1)

        self.tabs.addTab(tab, "📊 الجرد والمراجعة")

    def _refresh(self):
        self._refresh_materials()
        self._refresh_transactions()
        self._check_alerts()
        self._audit_search()

    def _refresh_materials(self):
        mats = db.get_materials()
        self.materials_table.setRowCount(0)
        red_color = QColor(220, 38, 38)
        for idx, m in enumerate(mats):
            row = self.materials_table.rowCount()
            self.materials_table.insertRow(row)
            self.materials_table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            self.materials_table.setItem(row, 1, QTableWidgetItem(m["name"]))
            self.materials_table.setItem(row, 2, QTableWidgetItem(m["unit"]))
            qty_item = QTableWidgetItem(f"{m['current_quantity']:.2f}")
            if m["current_quantity"] <= m["min_quantity"]:
                qty_item.setForeground(red_color)
                qty_item.setToolTip("⚠️ أقل من حد الأمان!")
            self.materials_table.setItem(row, 3, qty_item)
            self.materials_table.setItem(row, 4, QTableWidgetItem(f"{m['min_quantity']:.2f}"))
            self.materials_table.setItem(row, 5, QTableWidgetItem(f"{m['unit_price']:.2f}"))
            self.materials_table.setItem(row, 6, QTableWidgetItem(m.get("notes", "")))
            for col in range(7):
                it = self.materials_table.item(row, col)
                if it:
                    it.setTextAlignment(Qt.AlignCenter)

        self.trans_filter.blockSignals(True)
        self.trans_filter.clear()
        self.trans_filter.addItem("الكل", None)
        for m in mats:
            self.trans_filter.addItem(m["name"], m["id"])
        self.trans_filter.blockSignals(False)

    def _refresh_transactions(self):
        mat_id = self.trans_filter.currentData()
        trans = db.get_material_transactions(material_id=mat_id)
        self.trans_table.setRowCount(0)
        red_q = QColor(220, 38, 38)
        green_q = QColor(5, 150, 105)
        for idx, t in enumerate(trans):
            row = self.trans_table.rowCount()
            self.trans_table.insertRow(row)
            self.trans_table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            self.trans_table.setItem(row, 1, QTableWidgetItem(t["date"]))
            self.trans_table.setItem(row, 2, QTableWidgetItem(t["material_name"]))
            ttype_text = {"add": "➕ إضافة", "remove": "➖ صرف", "consume": "🔸 استهلاك"}
            self.trans_table.setItem(row, 3, QTableWidgetItem(ttype_text.get(t["transaction_type"], t["transaction_type"])))
            change = QTableWidgetItem(f"{t['change_amount']:+.2f}")
            change.setForeground(red_q if t["change_amount"] < 0 else green_q)
            self.trans_table.setItem(row, 4, change)
            self.trans_table.setItem(row, 5, QTableWidgetItem(t.get("invoice_number", "")))
            self.trans_table.setItem(row, 6, QTableWidgetItem(t.get("notes", "")))
            for col in range(7):
                it = self.trans_table.item(row, col)
                if it:
                    it.setTextAlignment(Qt.AlignCenter)

    def _check_alerts(self):
        low = db.get_low_stock_materials()
        if low:
            names = "، ".join(m["name"] for m in low)
            self.alert_banner.setText(f"⚠️ تنبيه: المواد التالية قاربت على النفاد: {names}")
            self.alert_banner.setVisible(True)
        else:
            self.alert_banner.setVisible(False)

    def _add_material(self):
        dlg = MaterialDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                db.add_material(data["name"], data["unit"], 0,
                                data["min_qty"], data["price"], data["notes"])
                self._refresh()
                QMessageBox.information(self, "تم", "✅ تمت إضافة المادة بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"❌ {str(e)}")

    def _edit_material(self):
        sel = self.materials_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد مادة من الجدول")
            return
        mats = db.get_materials()
        if sel >= len(mats):
            return
        dlg = MaterialDialog(self, material=mats[sel])
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                db.update_material(mats[sel]["id"], data["name"], data["unit"],
                                   data["min_qty"], data["price"], data["notes"])
                self._refresh()
                QMessageBox.information(self, "تم", "✅ تم تعديل المادة بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"❌ {str(e)}")

    def _delete_material(self):
        sel = self.materials_table.currentRow()
        if sel < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء تحديد مادة من الجدول")
            return
        mats = db.get_materials()
        if sel >= len(mats):
            return
        reply = QMessageBox.question(self, "تأكيد الحذف",
                                     f"هل أنت متأكد من حذف المادة '{mats[sel]['name']}'؟",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            db.delete_material(mats[sel]["id"])
            self._refresh()

    def _stock_transaction(self):
        sel = self.materials_table.currentRow()
        mats = db.get_materials()
        mat = mats[sel] if 0 <= sel < len(mats) else None
        dlg = StockDialog(self, material=mat)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_data()
            try:
                db.add_material_transaction(
                    data["material_id"], data["change_amount"],
                    data["trans_type"], data["date"],
                    data["invoice_id"], data["notes"]
                )
                self._refresh()
                QMessageBox.information(self, "تم", "✅ تم تسجيل الحركة بنجاح")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"❌ {str(e)}")

    def _audit_search(self):
        inv_number = self.audit_inv_input.text().strip()
        if not inv_number:
            self.audit_table.setRowCount(0)
            return
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM invoices WHERE invoice_number LIKE ?",
                  (f"%{inv_number}%",))
        inv_rows = c.fetchall()
        conn.close()
        all_consumption = []
        for inv_row in inv_rows:
            all_consumption.extend(db.get_material_consumption_summary(inv_row["id"]))
        self.audit_table.setRowCount(0)
        for idx, t in enumerate(all_consumption):
            row = self.audit_table.rowCount()
            self.audit_table.insertRow(row)
            self.audit_table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            self.audit_table.setItem(row, 1, QTableWidgetItem(t["material_name"]))
            self.audit_table.setItem(row, 2, QTableWidgetItem(t.get("unit", "")))
            self.audit_table.setItem(row, 3, QTableWidgetItem(f"{abs(t['change_amount']):.2f}"))
            self.audit_table.setItem(row, 4, QTableWidgetItem(t["date"]))
            for col in range(5):
                it = self.audit_table.item(row, col)
                if it:
                    it.setTextAlignment(Qt.AlignCenter)
