import struct

MAX_U32 = 2 ** 32
MAX_i64 = 2 ** 63


def u8x4_to_u32(buf):
    assert isinstance(buf, bytes)
    assert len(buf) == 4

    return struct.unpack("!I", buf[:4])[0]


def u8x1_to_u8(buf):
    assert isinstance(buf, bytes)
    assert len(buf) == 1

    return struct.unpack("!B", buf[:1])[0]


def u32_to_u8x4(u32):
    assert isinstance(u32, (int, str, bytes)), "Unknown Type: {} - {}".format(
        u32, type(u32)
    )
    if isinstance(u32, (str, bytes)):
        u32 = int(u32)

    assert u32 < MAX_U32

    return struct.pack("!I", u32)


def i64_to_u8x8(i64):
    assert isinstance(i64, (int, str, bytes)), "Unknown Type: {} - {}".format(
        i64, type(i64)
    )
    if isinstance(i64, (str, bytes)):
        i64 = int(i64)

    assert -MAX_i64 < i64 < MAX_i64

    return struct.pack("!q", i64)


def to_bytes(buf):
    assert isinstance(buf, (str, bytes))

    if isinstance(buf, str):
        return bytes(buf, "utf-8")
    return buf
