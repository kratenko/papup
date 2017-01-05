"""
Created on Jan 4, 2017

@author: kratenko
"""

import hashlib
import bz2
import struct
import unireedsolomon


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


class PapupPayload:

    def __init__(self, redundancy=3, compression=1, encryption=0):
        self.data = None
        # payload header data:
        self.payload_size = None
        self.redundancy = redundancy
        self.redundancy_padding = 0
        self.compression = compression
        self.compression_padding = 0
        self.encryption = encryption
        self.encryption_padding = 0
        # clear meta
        self.clear_meta_size = 0
        self.clear_meta_data = None
        self.crypt_meta_size = 0
        self.crypt_meta_data = None

    def set_content(self, content):
        self.data = content
        self.raw_data_length = len(self.data)
        self.raw_data_sha1 = hashlib.sha1(self.data)

    def pack_payload(self):
        self.do_crypt_meta()
        self.do_compression()
        self.do_encryption()
        self.do_clear_meta()
        self.do_redundancy()
        self.do_payload_header()

    def do_compression(self):
        if self.compression == 0:
            # no compression
            print("no compression")
            pass
        elif self.compression == 1:
            # bz2, 9
            print("bz2 compression")
            self.data = bz2.compress(self.data)
        else:
            raise ValueError(
                "Invalid compression method: {}".format(self.compression))

    def do_encryption(self):
        if self.encryption == 0:
            # no encryption
            pass
        else:
            raise ValueError(
                "Invalid encryption method: {}".format(self.encryption))

    def do_redundancy(self):
        if self.redundancy == 0:
            # 0 -> no redundancy
            self.redundancy_padding = 0
        elif self.redundancy == 1:
            # 1 -> 8 in 255 bytes
            self.data, self.redundancy_padding = rs_encode_data(
                255, 247, self.data)
        elif self.redundancy == 1:
            # 2 -> 16 in 255 bytes:
            self.data, self.redundancy_padding = rs_encode_data(
                255, 239, self.data)
        elif self.redundancy == 3:
            # 3 -> 32 in 255 bytes (common standard):
            self.data, self.redundancy_padding = rs_encode_data(
                255, 223, self.data)
        elif self.redundancy == 4:
            # 4 -> 64 in 255 bytes:
            self.data, self.redundancy_padding = rs_encode_data(
                255, 191, self.data)
        elif self.redundancy == 5:
            # 5 -> 128 in 255 bytes:
            self.data, self.redundancy_padding = rs_encode_data(
                255, 127, self.data)
        else:
            raise ValueError(
                "Invalid redundancy method: {}".format(self.redundancy))

    def do_crypt_meta(self):
        if self.crypt_meta_data is None:
            self.crypt_meta_size = 0
            d = struct.pack("!H", self.crypt_meta_size)
        else:
            self.crypt_meta_size = len(self.crypt_meta_data)
            d = struct.pack("!H", self.crypt_meta_size) + self.crypt_meta_data
        self.data = d + self.data

    def do_clear_meta(self):
        if self.clear_meta_data is None:
            self.clear_meta_size = 0
            d = struct.pack("!H", self.clear_meta_size)
        else:
            self.clear_meta_size = len(self.clear_meta_data)
            d = struct.pack("!H", self.clear_meta_size) + self.clear_meta_data
        self.data = d + self.data

    def generate_payload_header(self):
        self.payload_size = len(self.data)
        header = struct.pack("!QBBBBBB", self.payload_size, self.redundancy, self.redundancy_padding,
                             self.encryption, self.encryption_padding, self.compression, self.compression_padding)
        rs = unireedsolomon.RSCoder(32, 14)
        self.payload_header = rs.encode(header).encode("L1")

    def do_payload_header(self):
        self.generate_payload_header()
        self.data = self.payload_header + self.data
