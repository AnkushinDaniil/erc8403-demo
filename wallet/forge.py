from mc import *
def forged_header(bundle, height, priv):
    h = rlp.decode(bytes.fromhex(bundle['header']))
    h[8] = be(height)
    vanity = h[12][:-65]
    h[12] = vanity
    s = keys.PrivateKey(bytes.fromhex(priv)).sign_msg_hash(k256(rlp.encode(h)))
    h[12] = vanity + s.r.to_bytes(32, 'big') + s.s.to_bytes(32, 'big') + bytes([s.v])
    return rlp.encode(h)
