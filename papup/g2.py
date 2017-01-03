"""
Created on 2017-01-03

@author: Peer Springstübe
"""

import struct
import hashlib
import bz2

import unireedsolomon
import random
import uuid
import PIL.Image
import PIL.ImageDraw
import binascii
import math
import reportlab
from paper import PapupPage
from reportlab.lib.utils import ImageReader

fname = "gpl-3.0.txt"

with open(fname, "rb") as f:
    data = f.read()

LOGO = PIL.Image.open("logo.gif").convert("1")


def iterate_chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def rs_encode_data(n, k, data, pad_byte=b"\x55"):
    rs = unireedsolomon.RSCoder(n, k)
    chunks = []
    for chunk in iterate_chunks(data, k):
        if len(chunk) < k:
            # pad short chunks with \0 at end
            # this only happens for the last chunk
            pad = k - len(chunk)
            chunk += pad_byte * pad
        chunks.append(rs.encode(chunk).encode("L1"))
    return b"".join(chunks), pad


def rs_decode_data(n, k, data, length=None):
    rs = unireedsolomon.RSCoder(n, k)
    chunks = []
    for chunk in iterate_chunks(data[:-1], n):
        chunks.append(rs.decode(chunk)[0].encode("L1"))
    # concat:
    joined = b"".join(chunks)
    # include optionally cutting the padding for convenience:
    if length is None:
        return joined
    else:
        return joined[:length]


class PapupPayload():

    def __init__(self, redundancy=1, compression=1, encryption=0):
        self.padding = None
        self.data = None
        self.redundancy = redundancy
        self.compression = compression
        self.encryption = encryption

    def set_data(self, data):
        self.data = data
        self.raw_data_length = len(self.data)
        self.raw_data_sha1 = hashlib.sha1(self.data)

    def do_compression(self):
        if self.compression == 0:
            # no compression
            pass
        elif self.compression == 1:
            # bz2, 9
            self.data = bz2.compress(self.data)
        else:
            raise ValueError(
                "Invalid compression method: {}".format(self.compression))


class PapupFile():
    INDENT = b"PAPUP"
    VERSION = 0
    BLOCK_PAYLOAD = 124
    BLOCK_WIDTH = 32
    PAGE_HEADER_SIZE = 64

    def __init__(self, data):
        self.uuid = uuid.uuid4()
        self.data = data
        self.payload = None
        self.data_pos = 0
        self.pages = []

    def generate_payload(self):
        n = 255
        k = 191
        #self.payload = self.data
        # return
        data_bz2 = bz2.compress(self.data)
        pl_data, pad = rs_encode_data(n, k, data_bz2)
        pl_head = struct.pack("!QBBBB", len(pl_data), pad, 1, 1, 0)
        assert(len(pl_head) == 12)
        rs = unireedsolomon.RSCoder(32, 12)
        pl_head_rs = rs.encode(pl_head).encode("L1")
        assert(len(pl_head_rs) == 32)
        self.payload = pl_head_rs + pl_data

    def data_left(self):
        return self.data_pos < len(self.payload)

    def cut_next_page(self, cols, rows):
        # calculate space in page:
        blocks = cols * rows - 1
        space = self.BLOCK_PAYLOAD * blocks - self.PAGE_HEADER_SIZE
        # get data
        page_data = self.payload[self.data_pos:self.data_pos + space]
        self.pages.append(PapupPage(len(self.pages), page_data, cols, rows))
        self.data_pos += space

    def cut_pages(self):
        self.cut_next_page(16, 20)
        while self.data_left():
            self.cut_next_page(16, 24)
        for page in self.pages:
            page.file_id = self.uuid
            page.total_pages = len(self.pages)

    def generate_page_images(self):
        for page in self.pages:
            page.generate_page_legend()
            page.generate_page_image()


pf = PapupFile(data)
pf.generate_payload()
pf.cut_pages()
pf.generate_page_images()
print(pf.pages[0].page_legend)
# pf.pages[0].image.show()

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import Image

pdfmetrics.registerFont(TTFont('Mono', 'DejaVuSansMono.ttf'))

top = 820
c = canvas.Canvas("p1.pdf", bottomup=True)
c.setFont('Mono', 10)
p = pf.pages[0]
for n, line in enumerate(p.page_legend):
    c.drawString(20, top - 10 * n - 5, line)
c.drawImage(ImageReader(p.image), 12, top - 30 - p.image.size[1])
#c.drawInlineImage(ImageReader(p.image.convert("RGB")), 10, 50)
c.save()
