import math
import mimetypes
import os.path
import string
import random
import time
from hashlib import sha256


def crc16(data: bytes):
    xor_in = 0x0000  # initial value
    xor_out = 0x0000  # final XOR value
    poly = 0x8005  # generator polinom (normal form)

    reg = xor_in
    for octet in data:
        # reflect in
        for i in range(8):
            topbit = reg & 0x8000
            if octet & (0x80 >> i):
                topbit ^= 0x8000
            reg <<= 1
            if topbit:
                reg ^= poly
        reg &= 0xFFFF
        # reflect out
    return reg ^ xor_out


class PapupFile:
    PART_SIZE = 128

    @staticmethod
    def gen_id(length=4):
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))

    @staticmethod
    def load(path):
        filename = os.path.basename(path)
        with open(path, "rb") as f:
            data = f.read()
        p = PapupFile(filename, data)
        p.mime = mimetypes.guess_type(path)
        return p

    def __init__(self, filename, data):
        self.filename = filename
        self.ident = PapupFile.gen_id()
        if type(data) == str:
            self.data = data.encode("utf-8")
        else:
            self.data = data
        self.length = len(data)
        self.part_size = PapupFile.PART_SIZE
        self.sha256 = sha256(data)
        self.date = time.time()
        self.description = ""
        self.part_count = int(math.ceil(self.length / self.part_size))
        self.mime = None

    def get_header(self):
        return {
            "version": "0.1",
            "id": self.ident,
            "size": self.length,
            "parts": self.part_count,
            "sha256": self.sha256.hexdigest(),
            "name": self.filename,
            "description": self.description,
            "mime": self.mime[0] if self.mime else "",
        }

    def get_part(self, n):
        return self.data[(n - 1) * self.part_size:n * self.part_size]

    def parts(self):
        for n in range(self.part_count):
            yield self.get_part(n+1)

    def qr_parts(self):
        for n in range(self.part_count):
            yield f"PUD:{self.ident}:{n+1}/{self.part_count}:" + "".join("%02X" % c for c in self.get_part(n+1))

    def qr_parts_with_title(self):
        for n in range(self.part_count):
            title = f"PUD:{self.ident}:{n+1}/{self.part_count}"
            qr_part = title + ":" + ("".join("%02X" % c for c in self.get_part(n+1)))
            yield qr_part, title
