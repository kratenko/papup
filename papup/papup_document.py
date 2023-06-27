import json
import math
import textwrap

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas


def get_font_height(name, size):
    face = pdfmetrics.getFont(name).face
    return (face.ascent - face.descent) / 1000 * size


class PapupDocument:
    def __init__(self, pu):
        self.page_size = A4
        self.border_top = 1 * cm
        self.border_bottom = 1 * cm
        self.border_left = 1 * cm
        self.border_right = 1 * cm
        self.file_name = "out.pdf"
        self.canvas = canvas.Canvas(self.file_name, pagesize=self.page_size)
        self.pu = pu

    def header_height(self):
        font_name = "Courier"
        font_size = 11
        font_height = get_font_height(font_name, font_size)
        # logo
        h = 2 * cm + 0.5 * font_height
        # "description" paragraph
        text = "description: " + self.pu.description
        for t in textwrap.wrap(text, width=80, subsequent_indent=""):
            h += font_height * 1.5
        h += font_height * 0.5
        # instruction paragraph (five lines)
        font_name = "Courier"
        font_size = 9
        font_height = get_font_height(font_name, font_size)
        h += font_height * 1.5 * 5
        # spacing
        h += 0.5 * cm
        return h

    def header2_height(self):
        font_name = "Courier-Bold"
        font_size = 15
        font_height = get_font_height(font_name, font_size)
        return 1.5 * font_height

    def footer_height(self):
        font_name = "Courier"
        font_size = 9
        font_height = get_font_height(font_name, font_size)
        return 1.5 * font_height

    def draw_header(self, page, pages):
        # logo and first header
        font_name = "Courier-Bold"
        font_size = 15
        font_height = get_font_height(font_name, font_size)
        self.canvas.setFont(font_name, font_size)
        w0 = self.border_left
        h0 = self.page_size[1] - self.border_top
        self.canvas.drawInlineImage("logo.gif", w0, h0 - 2 * cm, 2 * cm, 2 * cm)
        self.canvas.drawString(w0 + 2 * cm + 0.2 * cm, h0 - font_height, "PAPUP FILE PRINTOUT v0.1")
        hd = font_height * 1.5
        # id and page number
        font_name = "Courier"
        font_size = 15
        font_height = get_font_height(font_name, font_size)
        self.canvas.setFont(font_name, font_size)
        page_text = f"ID: {self.pu.ident} - Page 1/{pages}"
        text_width = pdfmetrics.stringWidth(page_text, font_name, font_size)
        self.canvas.drawString(self.page_size[0] - self.border_right - text_width, h0 - font_height, page_text)
        # meta data:
        font_name = "Courier"
        font_size = 11
        font_height = get_font_height(font_name, font_size)
        self.canvas.setFont(font_name, font_size)
        self.canvas.drawString(w0 + 2*cm + 0.2*cm, h0 - hd - font_height, f"sha256: {self.pu.sha256.hexdigest()}")
        hd += font_height * 1.5
        self.canvas.drawString(w0 + 2*cm + 0.2*cm, h0 - hd - font_height,
                               f"size: {self.pu.length} B    parts: {self.pu.part_count}    part size: {self.pu.part_size} B")
        hd += font_height * 1.5
        self.canvas.drawString(w0 + 2*cm + 0.2*cm, h0 - hd - font_height,
                               f"name: {self.pu.filename}    mime: {self.pu.mime[0]}")
        # description:
        hd = 2 * cm + 0.5 * font_height
        text = "description: " + self.pu.description
        for t in textwrap.wrap(text, width=80, subsequent_indent=""):
            self.canvas.drawString(w0, h0 - hd - font_height, t)
            hd += font_height * 1.5
        hd += font_height * 0.5
        # instruction:
        font_name = "Courier"
        font_size = 9
        font_height = get_font_height(font_name, font_size)
        self.canvas.setFont(font_name, font_size)
        self.canvas.drawString(w0, h0 - hd - font_height,
                        "PAPUP is a standard for printing files on paper - see https://github.com/kratenko/papup")
        hd += font_height * 1.5
        self.canvas.drawString(w0, h0 - hd - font_height,
                        "This printout holds a single file. Each QR-Code starting with 'PUD:' hold hex-encoded data.")
        hd += font_height * 1.5
        self.canvas.drawString(w0, h0 - hd - font_height,
                        "Format: 'PUD:<file-id>:<part_number>/<total_parts>:<hexdata>', part number starts at 1.")
        hd += font_height * 1.5
        self.canvas.drawString(w0, h0 - hd - font_height,
                        "QR-Codes starting with 'PUM:' hold metadata, QR-Codes starting with 'PUR': hold redundancy (parity).")
        hd += font_height * 1.5
        self.canvas.drawString(w0, h0 - hd - font_height,
                        "Concatenate the data from QR-Codes with 'PUD:' to restore the file. Verify using sha256 checksum.")
        hd += font_height * 1.5
        # footer:
        self.canvas.drawString(w0, cm, f"Page {1}/{pages} - ID:{self.pu.ident}")
        text = "https://github.com/kratenko/papup"
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        self.canvas.drawString(self.page_size[0] - 1*cm - text_width, 1*cm, text)

    def draw_header2(self, page, pages):
        self.canvas.setFillGray(0.0)
        font_name = "Courier-Bold"
        font_size = 15
        font_height = get_font_height(font_name, font_size)
        self.canvas.setFont(font_name, font_size)
        w0 = self.border_left
        h0 = self.page_size[1] - self.border_top
        self.canvas.drawString(w0, h0 - font_height, "PAPUP FILE PRINTOUT v0.1")
        hd = font_height * 1.5
        # id and page number
        font_name = "Courier"
        font_size = 15
        font_height = get_font_height(font_name, font_size)
        self.canvas.setFont(font_name, font_size)
        page_text = f"ID: {self.pu.ident} - Page {page}/{pages}"
        text_width = pdfmetrics.stringWidth(page_text, font_name, font_size)
        self.canvas.drawString(self.page_size[0] - self.border_right - text_width, h0 - font_height, page_text)
        # footer:
        font_name = "Courier"
        font_size = 9
        font_height = get_font_height(font_name, font_size)
        self.canvas.setFont(font_name, font_size)
        self.canvas.drawString(self.border_left, cm, f"Page {page}/{pages} - ID:{self.pu.ident}")
        text = "https://github.com/kratenko/papup"
        text_width = pdfmetrics.stringWidth(text, font_name, font_size)
        self.canvas.drawString(self.page_size[0] - 1*cm - text_width, 1*cm, text)
        # restore
        font_name = "Courier"
        font_size = 7
        self.canvas.setFont(font_name, font_size)
        self.canvas.setFillGray(.5)


    def total_qr(self):
        header_json = json.dumps(self.pu.get_header())
        h_cnt = int(math.ceil(len(header_json) / self.pu.part_size))
        return h_cnt + self.pu.part_count

    def all_qr(self):
        header_json = json.dumps(self.pu.get_header())
        h_cnt = int(math.ceil(len(header_json) / self.pu.part_size))
        for n in range(h_cnt):
            title = f"PUM:{self.pu.ident}:{n+1}/{h_cnt}"
            data = title + ":" + header_json[n*self.pu.part_size:(n+1)*self.pu.part_size]
            yield data, title
        for y in self.pu.qr_parts_with_title():
            yield y

    def render(self):
        # how many qrs do we have:
        total = self.total_qr()
        # calculate view port for page 1:
        header_height = self.header_height()
        footer_height = self.footer_height()
        vp_width = self.page_size[0] - self.border_left - self.border_right
        vp_height = self.page_size[1] - header_height - footer_height - self.border_top - self.border_bottom
        space = 0.3 * cm
        per_row = 6
        # calculate qr code size:
        qw = (vp_width - (per_row - 1) * space) / per_row
        qh = qw + 0.7 * cm
        per_col = int((vp_height+0.7*cm) // qh)
        qrs_page1 = per_row * per_col
        # calculate view port for page 2:
        header2_height = self.header2_height()
        vp_height2 = self.page_size[1] - header2_height - footer_height - self.border_top - self.border_bottom
        per_col2 = int((vp_height2+0.7*cm) // qh)
        qrs_page2 = per_row * per_col2
        print(total, qrs_page1, qrs_page2)
        if total <= qrs_page1:
            pages = 1
        else:
            pages = 1 + int(math.ceil((total - qrs_page1) / qrs_page2))
        self.draw_header(1, pages)

        font_name = "Courier"
        font_size = 7
        self.canvas.setFont(font_name, font_size)
        self.canvas.setFillGray(.5)
        font_height = get_font_height(font_name, font_size)
        page = 1
        qx, qy = 0, 0
        w0 = self.border_left
        h0 = self.border_bottom + footer_height + vp_height
        per_page = qrs_page1
        on_page = 0
        for part, title in self.all_qr():
            on_page += 1
            if on_page == 1 and page != 1:
                self.canvas.showPage()
                self.draw_header2(page, pages)
            qr = qrcode.QRCode(border=0)
            qr.add_data(part)
            img = qr.make_image()
            x = w0 + qx * (space + qw)
            y = h0 - qy * qh
            self.canvas.drawString(x, y - font_height, title)
            y -= font_height * 1.8
            self.canvas.drawInlineImage(img,
                                 x, y - qw,
                                 width=qw, height=qw)
            qx += 1
            if qx >= per_row:
                qx = 0
                qy += 1
            if on_page == per_page:
                if page == 1:
                    per_page = qrs_page2
                    h0 = self.border_bottom + footer_height + vp_height2
                on_page = 0
                qy = 0
                page += 1

        self.canvas.save()
