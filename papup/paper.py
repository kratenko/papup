"""
Created on 2017-01-03

@author: Peer Springstübe
"""

import struct
import binascii
import math
import PIL.Image
import PIL.ImageDraw

import unireedsolomon
from __init__ import PAPUP_IDENT, PAPUP_VERSION


LOGO = None


def get_logo():
    global LOGO
    if LOGO is None:
        LOGO = PIL.Image.open("logo.gif").convert("1")
    return LOGO


def iterate_chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class PapupPage():
    BLOCK_PAYLOAD = 124
    BLOCK_WIDTH = 32
    PAGE_HEADER_SIZE = 64
    FILL_BYTE = b"\x55"

    def __init__(self, number, data, cols, rows):
        self.page_number = number
        self.total_pages = None
        self.file_id = None
        self.data = data
        self.cols = cols
        self.rows = rows
        self.page_image = None
        self.page_legend = None
        self.additional_legend = []
        #
        self.max_blocks = self.cols * self.rows - 1
        self.max_bytes = self.max_blocks * \
            self.BLOCK_PAYLOAD - self.PAGE_HEADER_SIZE
        self.actual_bytes = len(self.data)
        self.actual_blocks = int(
            math.ceil((self.actual_bytes + self.PAGE_HEADER_SIZE) / self.BLOCK_PAYLOAD))
        self.actual_rows = int(math.ceil((self.actual_blocks + 1) / self.cols))

    def generate_page_legend(self):
        # sane?
        assert(self.file_id is not None)
        assert(self.total_pages is not None)
        # build legend
        tmpl = "Papup version {version} file print out - see https://github.com/kratenko/papup for instructions\nID: {uuid} - Page: {page}/{pages} - Blocks: {blocks} - Columns: {columns}"
        txt = tmpl.format(version=0, uuid=self.file_id, page=self.page_number + 1,
                          pages=self.total_pages, blocks=self.actual_blocks, columns=self.cols)
        self.page_legend = txt.split("\n")

    def generate_page_header(self):
        header_raw = PAPUP_IDENT + struct.pack("!B", PAPUP_VERSION) + self.file_id.bytes + struct.pack(
            "!LLHH", self.page_number, self.total_pages, self.actual_blocks, self.cols)
        assert(len(header_raw) == 34)
        rs = unireedsolomon.RSCoder(64, 34)
        header_rs = rs.encode(header_raw).encode("L1")
        assert(len(header_rs) == 64)
        return header_rs

    def generate_page_image(self):
        # sane?
        assert(self.file_id is not None)
        assert(self.total_pages is not None)
        #
        page_header = self.generate_page_header()

        total_data = page_header + self.data

        block_images = self.generate_block_images(total_data)

        # generate total image and put blocks there
        iw = self.cols * (self.BLOCK_WIDTH + 3) + 1 + 2 * 4
        ih = self.actual_rows * (self.BLOCK_WIDTH + 3) + 1 + 2 * 4

        im = PIL.Image.new("1", (iw, ih), "white")
        for n, block in enumerate(block_images):
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
        for y in range(self.actual_rows + 1):
            yy = y * (self.BLOCK_WIDTH + 3) + 4
            draw.line((0, yy, im.size[0], yy), "black")
        im.paste(get_logo(), (5, 5))
        self.page_image = im

    def generate_block_image(self, data):
        assert(len(data) == self.BLOCK_PAYLOAD)
        data = data + struct.pack("!L", binascii.crc32(data))
        im = PIL.Image.new("1", (self.BLOCK_WIDTH, self.BLOCK_WIDTH), "white")
        for y in range(self.BLOCK_WIDTH):
            for x in range(self.BLOCK_WIDTH // 8):
                b = data[y * (self.BLOCK_WIDTH // 8) + x]
                for bn in range(8):
                    if (0x80 >> bn) & b:
                        im.putpixel((x * 8 + bn, y), 0x0)
        return im

    def generate_block_images(self, data):
        block_images = []
        for chunk in iterate_chunks(data, self.BLOCK_PAYLOAD):
            if len(chunk) < self.BLOCK_PAYLOAD:
                chunk += self.FILL_BYTE * (self.BLOCK_PAYLOAD - len(chunk))
            block_images.append(self.generate_block_image(chunk))
        return block_images
