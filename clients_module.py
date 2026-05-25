from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog
)
from PyQt5.QtCore import Qt
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
    "btn_edit": f"""
        QPushButton {{ background-color: {WARNING}; color: white;
            border-radius: 5px; font-size: 12px; font-weight: bold; padding: 6px 14px; border: none; }}
        QPushButton:hover {{ background-color: {WARNING_HOVER}; }}
    """,
    "btn_delete": f"""
        QPushButton {{ background-color: {BTN_NEUTRAL}; color: white;
            border-radius: 5px; font-size: 12px; font-weight: bold; padding: 6px 14px; border: none; }}
        QPushButton:hover {{ background-color: {BTN_NEUTRAL_HOVER}; }}
    """,
}


class ClientsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayoutDirection(Qt.RightToLeft)
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setSpacing(8)
        main.setContentsMargins(20, 12, 20, 12)

        title = QLabel("👥 إدارة العملاء")
        title.setStyleSheet(STYLES["title"])
        title.setAlignment(Qt.AlignCenter)
        main.addWidget(title)

        search_row = QHBoxLayout()
        search_row.setSpacing(10)
        search_row.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث باسم العميل...")
        self.search_input.textChanged.connect(self._refresh)
        search_row.addWidget(self.search_input, 1)
        search_row.addStretch()
        main.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "#", "الاسم", "الهاتف", "العنوان", "Telegram ID", "الإجراءات"
        ])
        h = self.table.horizontalHeader()
        stretch_cols = [1, 2, 3, 4]
        for c in range(6):
            if c in stretch_cols:
                h.setSectionResizeMode(c, QHeaderView.Stretch)
            else:
                h.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        h.setMinimumSectionSize(80)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(STYLES["table"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        main.addWidget(self.table, 1)

    def _refresh(self):
        clients = db.get_clients()
        search_text = self.search_input.text().strip()
        if search_text:
            clients = [c for c in clients if search_text in c.get("name", "")]
        self.table.setRowCount(0)
        green = QColor(5, 150, 105)
        for idx, c in enumerate(clients):
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setRowHeight(row, 38)
            self.table.setItem(row, 0, QTableWidgetItem(str(idx + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(c["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(c.get("phone", "")))
            self.table.setItem(row, 3, QTableWidgetItem(c.get("address", "")))
            tid_val = c.get("telegram_id", "")
            tid_item = QTableWidgetItem(tid_val)
            if tid_val:
                tid_item.setForeground(green)
            self.table.setItem(row, 4, tid_item)

            actions_w = QWidget()
            actions_l = QHBoxLayout(actions_w)
            actions_l.setContentsMargins(4, 2, 4, 2)
            actions_l.setSpacing(6)

            edit_btn = QPushButton("✏️ تعديل")
            edit_btn.setStyleSheet(STYLES["btn_edit"])
            edit_btn.setFixedSize(85, 28)
            cid = c["id"]
            edit_btn.clicked.connect(lambda checked, cid=cid: self._edit_client(cid))
            actions_l.addWidget(edit_btn)

            del_btn = QPushButton("🗑️ حذف")
            del_btn.setStyleSheet(STYLES["btn_delete"])
            del_btn.setFixedSize(85, 28)
            del_btn.clicked.connect(lambda checked, cid=cid: self._delete_client(cid))
            actions_l.addWidget(del_btn)

            self.table.setCellWidget(row, 5, actions_w)

            for col in range(5):
                it = self.table.item(row, col)
                if it:
                    it.setTextAlignment(Qt.AlignCenter)

    def _edit_client(self, client_id):
        clients = db.get_clients()
        client = next((c for c in clients if c["id"] == client_id), None)
        if not client:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("تعديل العميل")
        dlg.setFixedSize(400, 320)
        dlg.setLayoutDirection(Qt.RightToLeft)
        dlg.setStyleSheet(
            f"QDialog {{ background-color: {CARD}; }}"
            f"QLineEdit {{ padding: 8px 12px; border: 1.5px solid {BORDER}; "
            f"border-radius: 8px; background-color: {INPUT_BG}; color: {TEXT}; font-size: 13px; }}"
            f"QLineEdit:focus {{ border-color: {BORDER_FOCUS}; background-color: {INPUT_FOCUS}; }}"
        )
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("تعديل بيانات العميل")
        title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {PRIMARY};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        form.setSpacing(10)

        name_input = QLineEdit(client["name"])
        form.addRow("الاسم:", name_input)

        phone_input = QLineEdit(client.get("phone", ""))
        form.addRow("الهاتف:", phone_input)

        address_input = QLineEdit(client.get("address", ""))
        form.addRow("العنوان:", address_input)

        telegram_input = QLineEdit(client.get("telegram_id", ""))
        telegram_input.setPlaceholderText("معرف Telegram (رقمي)")
        form.addRow("Telegram ID:", telegram_input)

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
        save_btn.clicked.connect(lambda: self._do_edit(dlg, client_id, name_input, phone_input, address_input, telegram_input))
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)
        dlg.exec_()

    def _do_edit(self, dlg, client_id, name_input, phone_input, address_input, telegram_input):
        name = name_input.text().strip()
        if not name:
            QMessageBox.warning(dlg, "تنبيه", "الرجاء إدخال اسم العميل")
            return
        conn = db.get_connection()
        c = conn.cursor()
        try:
            c.execute("UPDATE clients SET name=?, phone=?, address=?, telegram_id=? WHERE id=?",
                      (name, phone_input.text().strip(), address_input.text().strip(),
                       telegram_input.text().strip(), client_id))
            conn.commit()
            QMessageBox.information(dlg, "تم", "✅ تم تعديل العميل بنجاح")
            dlg.accept()
            self._refresh()
        except Exception as e:
            QMessageBox.critical(dlg, "خطأ", f"❌ {str(e)}")
        finally:
            conn.close()

    def _delete_client(self, client_id):
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM invoices WHERE client_id=?", (client_id,))
        inv_count = c.fetchone()["cnt"]
        conn.close()

        warning = f"هل أنت متأكد من حذف هذا العميل؟"
        if inv_count > 0:
            warning += f"\n⚠️ سيتم حذف {inv_count} فاتورة/فواتير مرتبطة بهذا العميل أيضاً."

        reply = QMessageBox.question(
            self, "تأكيد الحذف", warning,
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return
        conn = db.get_connection()
        c = conn.cursor()
        try:
            c.execute("DELETE FROM invoice_items WHERE invoice_id IN (SELECT id FROM invoices WHERE client_id=?)", (client_id,))
            c.execute("DELETE FROM invoices WHERE client_id=?", (client_id,))
            c.execute("DELETE FROM clients WHERE id=?", (client_id,))
            conn.commit()
            QMessageBox.information(self, "تم", "✅ تم حذف العميل وما يرتبط به من فواتير بنجاح")
            self._refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"❌ {str(e)}")
        finally:
            conn.close()
