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


class PapupPage():
    BLOCK_PAYLOAD = 124
    BLOCK_WIDTH = 32
    PAGE_HEADER_SIZE = 64

    def __init__(self, number, data, cols, rows):
        self.number = number
        self.data = data
        self.cols = cols
        self.rows = rows
        self.image = None
        self.blocks = rows * cols - 1
        self.actual_blocks = None

    def generate_legend(self, file_id, total_pages):
        tmpl = "PAPUP file print out Version {version} - go to https://github.com/kratenko/papup for further information\nID: {uuid} - Page: {page}/{pages} - Blocks: {blocks} - Columns: {columns}"
        txt = tmpl.format(version=0, uuid=file_id, page=self.number + 1,
                          pages=total_pages, blocks=self.actual_blocks, columns=self.cols)
        return txt

    def generate_image(self, file_id, total_pages):
        header = b"PAPUP\0" + file_id.bytes + \
            struct.pack(
                "!HHHH", self.number, total_pages, self.blocks, self.cols)
        assert(len(header) == 30)
        rs = unireedsolomon.RSCoder(64, 30)
        header_rs = rs.encode(header).encode("L1")
        assert(len(header_rs) == 64)
        total_data = header_rs + self.data
        blocks = []
        for chunk in iterate_chunks(total_data, 124):
            if len(chunk) < 124:
                chunk += b"\x55" * (124 - len(chunk))
            blocks.append(self.generate_block(chunk))
        self.actual_blocks = len(blocks)
        actual_rows = int(math.ceil((self.actual_blocks + 1) / self.cols))
        # generate total image and put blocks there
        iw = self.cols * (self.BLOCK_WIDTH + 3) + 1 + 2 * 4
        ih = actual_rows * (self.BLOCK_WIDTH + 3) + 1 + 2 * 4
        im = PIL.Image.new("1", (iw, ih), "white")
        for n, block in enumerate(blocks):
            bx = (n + 1) % self.cols
            by = (n + 1) // self.cols
            x = bx * (self.BLOCK_WIDTH + 3) + 4
            y = by * (self.BLOCK_WIDTH + 3) + 4
            im.paste(block, (x + 2, y + 2))
        draw = PIL.ImageDraw.Draw(im)
        # draw vertical grid lines
        for x in range(self.cols + 1):
            xx = x * (self.BLOCK_WIDTH + 3) + 4
            draw.line((xx, 0, xx, im.size[1]), "black")
        # draw horizontal grid lines
        for y in range(actual_rows + 1):
            yy = y * (self.BLOCK_WIDTH + 3) + 4
            draw.line((0, yy, im.size[0], yy), "black")
        im.paste(LOGO, (5, 5))
        self.image = im

    def generate_block(self, data):
        assert(len(data) == self.BLOCK_PAYLOAD)
        data = data + struct.pack("!L", binascii.crc32(data))
        im = PIL.Image.new("1", (self.BLOCK_WIDTH, self.BLOCK_WIDTH), "white")
        for y in range(self.BLOCK_WIDTH):
            for x in range(self.BLOCK_WIDTH // 8):
                b = data[y * (self.BLOCK_WIDTH // 8) + x]
                for bn in range(8):
                    if (0x80 >> bn) & b:
                        im.putpixel((x * 8 + bn, y), 1)
        return im

    def generate_logo(self):
        im = PIL.Image.new("1", (34, 34), "black")
        draw = PIL.ImageDraw.Draw(im)
        rects = [
            (1 + 4, 1 + 4, 4 + 4 - 1, 4 + 24 - 1),
            (1 + 4 + 12, 1 + 4, 4 + 12 + 3 - 1, 4 + 16 - 1),
            (1 + 4 + 4, 1 + 4, 4 + 4 + 8 - 1, 4 + 4 - 1),
            (1 + 4 + 4, 1 + 4 + 12, 4 + 4 + 8 - 1, 4 + 12 + 4 - 1),
            (1 + 24, 1 + 4, 24 + 4 - 1, 4 + 24 - 1),
            (1 + 12, 1 + 24, 12 + 12 - 1, 24 + 4 - 1),
        ]
        for rect in rects:
            draw.rectangle(rect, "white")
        return im


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

    def generate_page_images(self):
        self.page_imgs = []
        for page in self.pages:
            page.generate_image(self.uuid, len(self.pages))
            print(page.generate_legend(self.uuid, len(self.pages)))


pf = PapupFile(data)
pf.generate_payload()
pf.cut_pages()
pf.generate_page_images()
pf.pages[0].image.show()
exit()
