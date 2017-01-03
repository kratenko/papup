"""
Created on Jan 1, 2017

@author: Peer Springstübe <peer@garstig.org>
"""

import struct
import binascii
import PIL
import uuid
import hashlib
import unireedsolomon

"""
# compression:
0: none
1: bzip(9)
# encryption:
0: none
# redundancy:
0: none
1: rs, 255/247 (8)
1: rs, 255/239 (16)
2: rs, 255/223 (32)
3: rs, 255/191 (64)
4: rs, 255/127 (128)
5: rs, 255/63 (192)
"""


class Document():
    IDENTOR = b"PAPUP"

    def __init__(self):
        self.version_byte = 0x01
        self.uuid = uuid.uuid4()
        self.rs_n = 255
        self.rs_k = 191

    def set_data(self, data):
        self.data = data

    def prepare_data(self):
        self.sha1 = hashlib.sha1(self.data)
        self.raw_size = len(self.data)
        self.compression()
        self.compressed_size = len(self.data)
        self.encryption()
        self.encrypted_size = len(self.data)
        self.redundancy()
        self.redundant_size = len(self.data)

    def compression(self):
        pass

    def encryption(self):
        pass

    def redundancy(self):
        pos = 0
        rs = unireedsolomon.RSCoder(self.rs_n, self.rs_k)
        chunks = []
        while len(self.data) - pos:
            in_chunk = self.data[pos:pos + self.rs_k]
            pos += len(in_chunk)
            out_chunk = rs.encode(in_chunk)
            chunks.append(out_chunk)
        self.data = b"".join(chunks)

    def header1(self):
        return self.IDENTOR + self.version_byte + self.uuid.bytes

    def header2(self):
        return


class Generator():
    # side length of block
    BLOCK_SIZE = 32
    # number of bytes used for crc
    CRC_BYTES = 4
    # number of bytes in a block
    BLOCK_BYTES = 32 * 32 // 8
    # number of bytes in block without crc
    BLOCK_PAYLOAD = ((32 * 32) - 32) // 8
    # byte used for padding last block
    FILL_BYTE = b"\x55"
    # magic numbers
    crc_bits = 32
    block_side = 32

    def __init__(self):
        self._pre_calc()

    def draw_block(self, data):
        assert(len(data) == self.BLOCK_BYTES)
        im = PIL.Image.new("1", (self.BLOCK_SIZE, self.BLOCK_SIZE), "white")
        bytes_per_line = self.BLOCK_SIZE // 8
        for n, b in enumerate(data):
            by = n // bytes_per_line
            bx = (n % bytes_per_line) * 8
            for s in range(8):
                if b & (0x1 << s):
                    im.putpixel((bx + s, by), 0x00)
        return im

    def header1(self):
        return b"PAPUP0x01"

    def _pre_calc(self):
        assert(self.crc_bits == 32)  # for now, at least
        assert(self.crc_bits % 8 == 0)
        self.crc_bytes = self.crc_bits // 8
        self.bits_per_block = self.block_side * self.block_side
        assert(self.bits_per_block % 8 == 0)
        self.bytes_per_block = self.bits_per_block // 8
        self.stored_per_block = self.bytes_per_block - self.crc_bytes

    def block_storage_chunks(self, data):
        pos = 0
        while len(data) - pos > self.stored_per_block:
            yield data[pos:pos + self.stored_per_block]
            pos += self.stored_per_block
        left = len(data) - pos
        fill = self.stored_per_block - left
        yield data[pos:] + (b'\x55' * fill)

    def block_data_chunks(self, data):
        for payload in self.block_storage_chunks(data):
            crc = binascii.crc32(payload)
            yield payload + struct.pack(">I", crc)
