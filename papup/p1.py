# hamming code?
import json
import random
import string
import textwrap

import qrcode
import reportlab

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas, textobject
from reportlab.lib.units import mm, cm
from reportlab.pdfbase import pdfmetrics

from papup.papup_document import PapupDocument
from papup.papup_file import PapupFile, crc16


def gen_id():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=4))


def get_font_height(name, size):
    face = pdfmetrics.getFont(name).face
    return (face.ascent - face.descent) / 1000 * size


def draw_header(canv, pu):
    page_size = canv._pagesize
    font_name = "Courier-Bold"
    font_size = 15
    font_height = get_font_height(font_name, font_size)
    canv.setFont(font_name, font_size)
    w0 = 1 * cm
    h0 = page_size[1] - 1 * cm
    canv.drawInlineImage("logo.gif", w0, h0-2*cm, 2*cm, 2*cm)
    canv.drawString(w0 + 2*cm + 0.2*cm, h0 - font_height, "PAPUP FILE PRINTOUT v0.1")
    hd = font_height * 1.5

    font_name = "Courier"
    font_size = 15
    font_height = get_font_height(font_name, font_size)
    canv.setFont(font_name, font_size)
    page_text = f"ID:{pu.ident} - Page:1/XXX"
    text_width = pdfmetrics.stringWidth(page_text, font_name, font_size)
    canv.drawString(page_size[0] - 1*cm - text_width, h0 - font_height, page_text)

    font_name = "Courier"
    font_size = 11
    font_height = get_font_height(font_name, font_size)
    canv.setFont(font_name, font_size)
    canv.drawString(w0 + 2*cm + 0.2*cm, h0 - hd - font_height, f"sha256: {pu.sha256.hexdigest()}")
    hd += font_height * 1.5
    canv.drawString(w0 + 2*cm + 0.2*cm, h0 - hd - font_height, f"size: {pu.length} B    parts: {pu.part_count}    part size: {pu.part_size} B")
    hd += font_height * 1.5
    canv.drawString(w0 + 2*cm + 0.2*cm, h0 - hd - font_height, f"name: {pu.filename}    mime: {pu.mime[0]}")

    hd = 2*cm + 0.5 * font_height
    text = "description: " + pu.description
    for t in textwrap.wrap(text, width=80, subsequent_indent=""):
        canv.drawString(w0, h0 - hd - font_height, t)
        hd += font_height * 1.5
    hd += font_height * 0.5

    font_name = "Courier"
    font_size = 9
    font_height = get_font_height(font_name, font_size)
    canv.setFont(font_name, font_size)
    canv.drawString(w0, h0 - hd - font_height,
                    "PAPUP is a standard for printing files on paper - see https://github.com/kratenko/papup")
    hd += font_height * 1.5
    canv.drawString(w0, h0 - hd - font_height,
                    "This printout holds a single file. Each QR-Code starting with 'PUD:' hold hex-encoded data.")
    hd += font_height * 1.5
    canv.drawString(w0, h0 - hd - font_height,
                    "Format: 'PUD:<file-id>:<part_number>/<total_parts>:<hexdata>', part number starts at 1.")
    hd += font_height * 1.5
    canv.drawString(w0, h0 - hd - font_height,
                    "QR-Codes starting with 'PUM:' hold metadata, QR-Codes starting with 'PUR': hold redundancy (parity).")
    hd += font_height * 1.5
    canv.drawString(w0, h0 - hd - font_height,
                    "Concatenate the data from QR-Codes with 'PUD:' to restore the file. Verify using sha256 checksum.")
    hd += font_height * 1.5

    # https://www.sekretaria.de/bueroorganisation/korrespondenz/din-5008/falzmarke/
    if False:
        canv.setLineWidth(0.1 * mm)
        canv.setStrokeGray(.8)
        falz_w = 5 * mm
        falz_1 = page_size[1] - 87 * mm
        falz_2 = falz_1 - 105 * mm
        canv.line(0, falz_1, falz_w, falz_1)
        canv.line(0, falz_2, falz_w, falz_2)
        canv.line(0, page_size[1] / 2, 7 * mm, page_size[1] / 2)

    canv.drawString(w0, cm, f"Page {1}/XXX - ID:{pu.ident}")
    text = "https://github.com/kratenko/papup"
    text_width = pdfmetrics.stringWidth(text, font_name, font_size)
    canv.drawString(page_size[0] - 1*cm - text_width, 1*cm, text)

    return hd


def bxor(ba1, ba2):
    return bytes(a ^ b for a, b in zip(ba1, ba2))


def main():
    pu = PapupFile.load("rick.jpg")
    print(pu.filename, pu.length, pu.sha256.hexdigest())
    pu.description = "A valuable and treasured file that I care about deeply. Großartig. But then it is much too large for a single line, so what do we do?"
    #print(pu.get_header())
    #h = json.dumps(pu.get_header())
    #print(len(h), h)
    #for part in pu.qr_parts():
    #    print(part)
    pd = PapupDocument(pu)
    pd.render()
    exit()


    canv = canvas.Canvas("out.pdf", pagesize=A4)
    hd = draw_header(canv, pu)

    font_name = "Courier"
    font_size = 7
    canv.setFont(font_name, font_size)
    canv.setFillGray(.5)
    pagesize = canv._pagesize
    font_height = get_font_height(font_name, font_size)

    qx, qy = 0, 0
    num_row = 6
    space = 5 * mm
    w = pagesize[0] - 2 * cm
    h0 = pagesize[1] - 1 * cm
    qw = (w - (num_row - 1) * space) / num_row
    hd += 0.5 * cm
    for part, title in pu.qr_parts_with_title():
        qr = qrcode.QRCode(border=0)
        qr.add_data(part)
        img = qr.make_image()

        x = 1 * cm + qx * (space + qw)
        y = h0 - hd - qy * (qw + 0.7 * cm)
        canv.drawString(x, y - font_height, title)
        y -= font_height * 1.8
        canv.drawInlineImage(img,
                             x, y - qw,
                             # h0 + hd + qy * (qw + 0.7 * cm) + 1 * cm,
#                             qy * (qw + 0.7 * cm) + 1 * cm,
                             width=qw, height=qw)

        qx += 1
        if qx >= num_row:
            qx = 0
            qy += 1

    canv.save()
    exit()

    ident = gen_id()
    chunk_size = 128
    with open("logo.gif", "rb") as f:
        data = f.read()
    parts = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    print(f"parts: {len(parts)}")

    canv = canvas.Canvas("out.pdf", pagesize=A4, bottomup=1)
    draw_header(canv)

    canv.setFont("Courier", 7)
    pagesize = canv._pagesize
    w = pagesize[0] - 2 * cm
    num_row = 6
    space = 5 * mm
    qw = (w - (num_row - 1) * space) / num_row
    print(w, qw)
    qy = 0
    qx = 0
    for n, part in enumerate(parts):
        data = f"PUD:{ident}:{n+1}/{len(parts)}:" + "".join(["%02X" % c for c in part])
        print(data)
        qr = qrcode.QRCode(border=0)
        qr.add_data(data)
        print(f"Payload: {len(part)} Bytes, version: {qr.version}")
#    img = qrcode.make(data)
        img_name = f"qr-pud-{n+1}.png"
        img = qr.make_image()

#        img.save(img_name)

        x = 1 * cm + qx * (space + qw)
        canv.drawInlineImage(img, x, qy * (qw + 0.7 * cm) + 1 * cm, width=qw, height=qw)
        canv.drawString(x, qy * (qw + 0.7 * cm) + qw + 1.3 * cm, f"PUD:{ident}:{n+1}/{len(parts)}")
        qx += 1
        if qx >= num_row:
            qx = 0
            qy += 1

    canv.setFont("Courier", 8)
    pdata = bytes(range(32))
    print(pdata)
    c16 = crc16(pdata)
    print("%04X" % c16)
    t = " ".join(["%02X" % c for c in pdata])
    tt = "00056    " + t # + "    " + ("%04X" % c16)
    canv.drawString(1.5*cm, 10*cm, tt)
    canv.save()


if __name__ == "__main__":
    main()
