import os
import tempfile
from datetime import datetime
from fpdf import FPDF
import arabic_reshaper
from bidi.algorithm import get_display
import qrcode
import database as db

FONT_DIR = "/usr/share/fonts/truetype"
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
]

HEADER_COLOR = (26, 82, 118)
TABLE_HEADER_COLOR = (44, 62, 80)
TABLE_ALT_COLOR = (241, 245, 249)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (192, 57, 43)
GREEN = (39, 174, 96)
GRAY = (128, 128, 128)


def ar(text):
    try:
        reshaped = arabic_reshaper.reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)


def resh(text):
    try:
        return arabic_reshaper.reshape(str(text))
    except Exception:
        return str(text)


def fmt_cur(amount, symbol):
    clean = symbol.split(" (")[0].strip() if " (" in symbol else symbol
    return f"{amount:.2f}  {resh(clean)}"


def find_arabic_font():
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    for root, dirs, files in os.walk(FONT_DIR):
        for f in files:
            if f.lower().endswith(".ttf"):
                full = os.path.join(root, f)
                try:
                    with open(full, "rb") as fh:
                        header = fh.read(4)
                    if header == b"\x00\x01\x00\x00" or header == b"OTTO":
                        return full
                except Exception:
                    continue
    return None


def find_bold_font(regular_path):
    if not regular_path:
        return None
    base = regular_path.replace(".ttf", "-Bold.ttf")
    if os.path.exists(base):
        return base
    base2 = regular_path.replace(".ttf", "Bold.ttf")
    if os.path.exists(base2):
        return base2
    alt = os.path.join(os.path.dirname(regular_path), "DejaVuSans-Bold.ttf")
    if os.path.exists(alt):
        return alt
    return regular_path


def generate_qr(data):
    qr = qrcode.QRCode(box_size=3, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    img.save(tmp.name)
    return tmp.name


class InvoicePDF(FPDF):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.currency = settings.get("currency", "د.ل")
        self.set_auto_page_break(auto=True, margin=28)
        font_path = find_arabic_font()
        self.font_name = "Arabic"
        if font_path:
            bold_path = find_bold_font(font_path)
            self.add_font(self.font_name, "", font_path, uni=True)
            if bold_path and os.path.exists(bold_path):
                self.add_font(self.font_name, "B", bold_path, uni=True)
            else:
                self.add_font(self.font_name, "B", font_path, uni=True)
        else:
            self.add_font(self.font_name, "", "", uni=True)
            self.add_font(self.font_name, "B", "", uni=True)

    def header(self):
        s = self.settings
        self.set_font(self.font_name, "B", 20)
        self.set_text_color(*HEADER_COLOR)
        self.cell(0, 10, ar(s.get("company_name", "شركتي")), ln=True, align="C")
        self.set_font(self.font_name, "", 9)
        self.set_text_color(*BLACK)
        phones = s.get("phone1", "")
        if s.get("phone2"):
            phones += f"  |  {s['phone2']}"
        addr = s.get("address", "")
        info = f"هاتف: {phones}"
        if addr:
            info += f"  |  {addr}"
        self.cell(0, 6, ar(info), ln=True, align="C")
        self.set_draw_color(*HEADER_COLOR)
        self.set_line_width(0.6)
        self.line(10, self.get_y() + 2, 200, self.get_y() + 2)
        self.ln(6)

    def footer(self):
        self.set_y(-30)
        self.set_font(self.font_name, "", 8)
        self.set_text_color(*GRAY)
        notes = self.settings.get("invoice_notes", "")
        if notes:
            self.multi_cell(0, 5, ar(notes), align="C")
            self.ln(2)
        self.set_font(self.font_name, "", 7)
        self.cell(0, 5, ar(f'صدرت في: {datetime.now().strftime("%Y/%m/%d %H:%M")}'),
                  ln=True, align="C")
        self.cell(0, 5, ar(f"الصفحة {self.page_no()}"), ln=True, align="C")


def number_to_words(num):
    if num == 0:
        return "صفر"
    ones = ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
    teens = ["", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر",
             "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"]
    tens = ["", "عشرون", "ثلاثون", "أربعون", "خمسون",
            "ستون", "سبعون", "ثمانون", "تسعون"]
    hundreds = ["", "مائة", "مائتان", "ثلاثمائة", "أربعمائة",
                "خمسمائة", "ستمائة", "سبعمائة", "ثمانمائة", "تسعمائة"]

    def under_1000(n):
        if n == 0:
            return ""
        h = n // 100
        rem = n % 100
        parts = []
        if h:
            if h == 2:
                parts.append("مائتان")
            elif h == 1:
                parts.append("مائة")
            else:
                parts.append(hundreds[h])
        if rem:
            sub = ""
            if rem == 10:
                sub = "عشرة"
            elif rem < 10:
                sub = ones[rem]
            elif rem < 20:
                sub = teens[rem - 10]
            else:
                t = rem // 10
                o = rem % 10
                if o:
                    sub = ones[o] + " و " + tens[t - 1]
                else:
                    sub = tens[t - 1]
            parts.append(sub)
        return " و ".join(parts)

    billions = num // 1000000000
    millions = (num % 1000000000) // 1000000
    thousands = (num % 1000000) // 1000
    remainder = num % 1000

    parts = []
    if billions:
        b_text = under_1000(billions)
        parts.append(b_text + " مليار" if billions != 2 else b_text + " ملياران")
    if millions:
        m_text = under_1000(millions)
        if 3 <= millions <= 10:
            parts.append(m_text + " ملايين")
        elif millions == 2:
            parts.append("مليونان")
        elif millions == 1:
            parts.append("مليون")
        else:
            parts.append(m_text + " مليون")
    if thousands:
        t_text = under_1000(thousands)
        if 3 <= thousands <= 10:
            parts.append(t_text + " آلاف")
        elif thousands == 2:
            parts.append("ألفان")
        elif thousands == 1:
            parts.append("ألف")
        else:
            parts.append(t_text + " ألف")
    if remainder:
        parts.append(under_1000(remainder))

    return " و ".join(parts) if parts else "صفر"


def generate_invoice_pdf(invoice_data, items, client_data, output_path, secure_code="", bot_username=""):
    settings = db.get_company_settings()
    pdf = InvoicePDF(settings)
    currency = settings.get("currency", "د.ل")
    pdf.add_page()

    if not bot_username:
        bot_username = settings.get("telegram_bot_username", "")
    if bot_username:
        bot_username = bot_username.lstrip("@")

    if secure_code and bot_username:
        qr_data = f"https://t.me/{bot_username}?start={secure_code}"
    else:
        qr_data = (
            f"رقم الفاتورة: {invoice_data['number']}\n"
            f"الإجمالي: {invoice_data['total_after_discount']:.2f} {currency}\n"
            f"التاريخ: {invoice_data['date']}\n"
            f"العميل: {client_data.get('name', '')}"
        )
    qr_path = generate_qr(qr_data)

    pdf.set_font(pdf.font_name, "B", 15)
    pdf.set_text_color(*RED)
    pdf.cell(0, 9, ar("فاتورة"), ln=True, align="C")
    pdf.ln(1)

    pdf.set_draw_color(*HEADER_COLOR)
    pdf.set_line_width(0.3)
    pdf.line(70, pdf.get_y(), 140, pdf.get_y())
    pdf.ln(4)

    meta_start_y = pdf.get_y()
    pdf.set_text_color(*BLACK)

    meta_items = [
        (ar("رقم الفاتورة"), invoice_data["number"]),
        (ar("التاريخ"), invoice_data["date"]),
        (ar("اسم العميل"), ar(client_data.get("name", ""))),
        (ar("هاتف العميل"), client_data.get("phone", "")),
        (ar("حالة الطلب"), ar(invoice_data["status"])),
    ]
    label_x = 155
    value_x = 90
    for label, value in meta_items:
        pdf.set_font(pdf.font_name, "B", 10)
        pdf.set_x(label_x)
        pdf.cell(40, 7, label, border=0)
        pdf.set_font(pdf.font_name, "", 10)
        pdf.set_x(value_x)
        pdf.cell(65, 7, value, border=0)
        pdf.ln()

    meta_end_y = pdf.get_y()

    qr_x = 12
    qr_y = meta_start_y - 2
    qr_size = 28
    if os.path.exists(qr_path):
        pdf.image(qr_path, x=qr_x, y=qr_y, w=qr_size, h=qr_size)

    pdf.set_y(max(meta_end_y, qr_y + qr_size + 4))
    try:
        os.unlink(qr_path)
    except Exception:
        pass

    pdf.ln(3)

    col_widths = [39, 16, 24, 24, 28, 50, 10]
    headers = [
        ar("الإجمالي"), ar("الكمية"), ar("سعر المتر"),
        ar("المساحة"), ar("المقاس"), ar("نوع الخدمة"), ar("#"),
    ]

    pdf.set_fill_color(*TABLE_HEADER_COLOR)
    pdf.set_text_color(*WHITE)
    pdf.set_font(pdf.font_name, "B", 9)
    pdf.set_x(10)
    for hdr, w in zip(headers, col_widths):
        pdf.cell(w, 10, hdr, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(*BLACK)
    pdf.set_font(pdf.font_name, "", 9)

    for idx, item in enumerate(items):
        size_str = f"{item['length']} × {item['width']}"
        pdf.set_x(10)
        row_data = [
            f"{item['total']:.2f}",
            str(item["quantity"]),
            f"{item['unit_price']:.2f}",
            f"{item['area']:.2f}",
            size_str,
            ar(item["service_type"]),
            str(idx + 1),
        ]
        if idx % 2 == 0:
            pdf.set_fill_color(*TABLE_ALT_COLOR)
            fill = True
        else:
            fill = False
        for data, w in zip(row_data, col_widths):
            pdf.cell(w, 8, data, border=1, align="C", fill=fill)
        pdf.ln()

    pdf.ln(4)

    value_w = 55
    label_w = 55
    table_right = 200
    value_x = table_right - label_w - value_w
    label_x = table_right - label_w

    total_items = [
        ("الإجمالي قبل الخصم", invoice_data['total_before_discount'], False, False),
        ("قيمة الخصم", invoice_data['discount'], False, False),
        ("الإجمالي النهائي", invoice_data['total_after_discount'], True, True),
        ("المبلغ المدفوع", invoice_data['paid_amount'], False, False),
        ("المبلغ المتبقي", invoice_data['remaining_amount'], True, False),
    ]
    for label_raw, value, highlight, is_red in total_items:
        if highlight:
            pdf.set_font(pdf.font_name, "B", 11)
            pdf.set_text_color(*RED) if is_red else pdf.set_text_color(*GREEN)
        else:
            pdf.set_font(pdf.font_name, "", 10)
            pdf.set_text_color(*BLACK)

        pdf.set_x(label_x)
        pdf.cell(label_w, 8, ar(label_raw), border=0, align="R")

        if highlight:
            pdf.set_font(pdf.font_name, "B", 11)
        else:
            pdf.set_font(pdf.font_name, "", 10)
        pdf.set_x(value_x)
        pdf.cell(value_w, 8, fmt_cur(value, currency), border=0, align="R", ln=True)

    pdf.ln(5)

    pdf.set_draw_color(*HEADER_COLOR)
    pdf.set_line_width(0.3)
    pdf.line(label_x, pdf.get_y(), table_right, pdf.get_y())
    pdf.ln(4)

    final_amount = invoice_data["total_after_discount"]
    words_raw = "فقط وقدره: " + number_to_words(int(final_amount))
    frac = int(round((final_amount - int(final_amount)) * 100))
    if frac > 0:
        words_raw += " و" + number_to_words(frac) + " قرشاً"
    else:
        words_raw += " دينار ليبي"
    words_raw += " لا غير"
    pdf.set_font(pdf.font_name, "B", 10)
    pdf.set_text_color(*HEADER_COLOR)
    pdf.set_x(15)
    pdf.multi_cell(180, 7, ar(words_raw), align="C")
    pdf.ln(3)

    pdf.set_draw_color(*HEADER_COLOR)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font(pdf.font_name, "", 9)
    pdf.set_text_color(*BLACK)
    pdf.cell(0, 7, ar("توقيع المستلم ..........................  |  ختم الشركة .........................."),
             ln=True, align="C")

    pdf.ln(3)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    return output_path


def generate_summary_report(invoices, output_path):
    settings = db.get_company_settings()
    currency = settings.get("currency", "د.ل")

    pdf = InvoicePDF(settings)
    pdf.add_page()

    pdf.set_font(pdf.font_name, "B", 16)
    pdf.set_text_color(*HEADER_COLOR)
    pdf.cell(0, 10, ar("تقرير شامل - جميع الأعمال"), ln=True, align="C")

    pdf.set_font(pdf.font_name, "", 9)
    pdf.set_text_color(*BLACK)
    pdf.cell(0, 6, ar(f'تم التصدير في: {datetime.now().strftime("%Y/%m/%d %H:%M")}'),
             ln=True, align="C")
    pdf.cell(0, 6, ar(f"إجمالي عدد الفواتير: {len(invoices)}"), ln=True, align="C")
    pdf.ln(4)

    pdf.set_draw_color(*HEADER_COLOR)
    pdf.set_line_width(0.6)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)

    col_widths = [46, 38, 70, 28, 8]
    headers = [
        ar("المدفوع"), ar("الإجمالي"), ar("اسم العميل"),
        ar("رقم الفاتورة"), ar("#"),
    ]

    pdf.set_fill_color(*TABLE_HEADER_COLOR)
    pdf.set_text_color(*WHITE)
    pdf.set_font(pdf.font_name, "B", 9)
    pdf.set_x(10)
    for hdr, w in zip(headers, col_widths):
        pdf.cell(w, 10, hdr, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(*BLACK)
    pdf.set_font(pdf.font_name, "", 9)
    grand_total = 0.0
    grand_paid = 0.0

    for idx, inv in enumerate(invoices):
        pdf.set_x(10)
        row_data = [
            f"{inv['paid_amount']:.2f}",
            f"{inv['total_after_discount']:.2f}",
            ar(inv.get("client_name", "")),
            ar(inv["invoice_number"]),
            str(idx + 1),
        ]
        if idx % 2 == 0:
            pdf.set_fill_color(*TABLE_ALT_COLOR)
            fill = True
        else:
            fill = False
        for data, w in zip(row_data, col_widths):
            pdf.cell(w, 8, data, border=1, align="C", fill=fill)
        pdf.ln()

        grand_total += inv["total_after_discount"]
        grand_paid += inv["paid_amount"]

    pdf.ln(4)

    value_w2 = 50
    label_w2 = 60
    table_right2 = 200
    value_x2 = table_right2 - label_w2 - value_w2
    label_x2 = table_right2 - label_w2

    grand_items = [
        ("الإجمالي الكلي لجميع الخدمات", grand_total),
        ("إجمالي المدفوع", grand_paid),
    ]
    for label_raw, val in grand_items:
        pdf.set_font(pdf.font_name, "B", 11)
        if label_raw == "الإجمالي الكلي لجميع الخدمات":
            pdf.set_text_color(*HEADER_COLOR)
        else:
            pdf.set_text_color(*GREEN)
        pdf.set_x(label_x2)
        pdf.cell(label_w2, 9, ar(label_raw), border=0, align="R")
        pdf.set_x(value_x2)
        pdf.cell(value_w2, 9, fmt_cur(val, currency), border=0, align="R", ln=True)

    pdf.ln(4)

    words_raw2 = "فقط وقدره: " + number_to_words(int(grand_total))
    frac2 = int(round((grand_total - int(grand_total)) * 100))
    if frac2 > 0:
        words_raw2 += " و" + number_to_words(frac2) + " قرشاً"
    else:
        words_raw2 += " دينار ليبي"
    words_raw2 += " لا غير"
    pdf.set_font(pdf.font_name, "B", 9)
    pdf.set_text_color(*HEADER_COLOR)
    pdf.set_x(15)
    pdf.multi_cell(180, 6, ar(words_raw2), align="C")
    pdf.ln(3)

    pdf.set_draw_color(*HEADER_COLOR)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font(pdf.font_name, "", 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, ar("نظام إدارة الفواتير - شركة الدعاية والإعلان"), ln=True, align="C")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pdf.output(output_path)
    return output_path
