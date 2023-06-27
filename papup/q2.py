import re

from PIL import Image
from pyzbar.pyzbar import decode


class Papdown:
    def __init__(self, ident):
        self.ident = ident
        self.pud = {}
        self.pud_count = 0
        self.pud_re = re.compile(rf"^PUD:{self.ident}:(\d+)/(\d+):([0-9A-F]+)$")
        self.pum = {}
        self.pum_count = 0
        self.pum_re = re.compile(rf"^PUM:{self.ident}:(\d+)/(\d+):(.+)$")

    def read_pum(self, n, total, data):
        if self.pum_count == 0:
            self.pum_count = total
        elif self.pum_count != total:
            print("Conflicting PUM count")
            return
        if n in self.pum:
            if self.pum[n] != data:
                print("Conflicting PUM content")
                return
        else:
            self.pum[n] = data

    def read_pud(self, n, total, data):
        total = int(total)
        n = int(n)
        if self.pud_count == 0:
            self.pud_count = total
        elif self.pud_count != total:
            print("Conflicting PUD count")
            return
        if n in self.pud:
            if self.pud[n] != data:
                print("Conflicting PUD content")
                return
        else:
            self.pud[n] = data

    def read_code(self, data):
        m = self.pum_re.match(data)
        if m:
            self.read_pum(*m.groups())
            return
        m = self.pud_re.match(data)
        if m:
            self.read_pud(*m.groups())
            return

    def get_data(self):
        data = b""
        for n in range(1, self.pud_count + 1):
            part = self.pud[n]
            data += bytearray.fromhex(part)
        return data

class Scanner:
    MATCH = re.compile(r"^PU[DM]:([0-9A-Z]+):")

    def __init__(self):
        self.store = {}

    def read_code(self, data):
        if type(data) == bytes:
            data = data.decode()
        m = self.MATCH.match(data)
        if m:
            ident = m.group(1)
            if ident not in self.store:
                self.store[ident] = Papdown(ident)
            pd = self.store[ident]
            pd.read_code(data)

    def dump(self):
        for k, v in self.store.items():
            print(k, v.pum, v.pud)

    def restore(self):
        for k, v in self.store.items():
            d = v.get_data()
            with open(f"{k}.jpg", "wb") as f:
                f.write(d)

    def scan(self, img):
        for d in decode(img):
            self.read_code(d.data)


img = Image.open('qrdings.jpg')
scanner = Scanner()
scanner.scan(img)
#scanner.dump()
scanner.restore()
