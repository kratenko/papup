"""
Created on 2017-01-03

@author: Peer Springstübe
"""

import uuid

from paper import PapupPage
from pdf import build_pdf
from payload import PapupPayload

fname = "faust1.txt"

with open(fname, "rb") as f:
    data = f.read()


class PapupFile():
    INDENT = b"PAPUP"
    VERSION = 0
    BLOCK_PAYLOAD = 124
    BLOCK_WIDTH = 32
    PAGE_HEADER_SIZE = 64

    def __init__(self, payload):
        self.uuid = uuid.uuid4()
        self.payload = payload
        self.data_pos = 0
        self.pages = []

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
        self.cut_next_page(15, 16)
        while self.data_left():
            self.cut_next_page(15, 20)
        for page in self.pages:
            page.file_id = self.uuid
            page.total_pages = len(self.pages)

    def generate_page_images(self):
        for page in self.pages:
            page.generate_page_legend()
            page.generate_page_image()


pl = PapupPayload()
pl.set_content(data)
pl.pack_payload()

pf = PapupFile(pl.data)
pf.cut_pages()
pf.generate_page_images()
print(pf.pages[0].page_legend)
# pf.pages[0].image.show()

build_pdf(pf, 'out.pdf')
