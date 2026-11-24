import struct
import zlib


def read_png(path):
    """Renvoie (largeur, hauteur, lignes), chaque ligne étant une liste de tuples (r, g, b)."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} n'est pas un PNG")

    pos = 8
    width = height = 0
    bit_depth = color_type = interlace = None
    idat = b""
    while pos < len(data):
        length, chunk_type = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif chunk_type == b"IDAT":
            idat += chunk
        elif chunk_type == b"IEND":
            break

    if bit_depth != 8 or color_type not in (2, 6) or interlace != 0:
        raise ValueError(f"{path} : exportez en PNG RGB ou RGBA 8 bits, sans palette ni entrelacement")

    bpp = 3 if color_type == 2 else 4
    stride = width * bpp
    raw = zlib.decompress(idat)
    rows = []
    previous = bytearray(stride)
    i = 0
    for _ in range(height):
        filter_type = raw[i]
        i += 1
        line = bytearray(raw[i:i + stride])
        i += stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = previous[x]
            c = previous[x - bpp] if x >= bpp else 0
            if filter_type == 1:
                line[x] = (line[x] + a) & 0xFF
            elif filter_type == 2:
                line[x] = (line[x] + b) & 0xFF
            elif filter_type == 3:
                line[x] = (line[x] + ((a + b) >> 1)) & 0xFF
            elif filter_type == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                predictor = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + predictor) & 0xFF
        rows.append([tuple(line[x:x + 3]) for x in range(0, stride, bpp)])
        previous = line
    return width, height, rows