
import hashlib
import math

# https://stackoverflow.com/a/26856771
def hsv_to_rgb(h, s, v):
    if s == 0.0: v*=255; return (v, v, v)
    i = int(h*6.) # XXX assume int() truncates!
    f = (h*6.)-i; p,q,t = int(255*(v*(1.-s))), int(255*(v*(1.-s*f))), int(255*(v*(1.-s*(1.-f)))); v*=255; i%=6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)


def get_color(name):
    hash = hashlib.md5((name).encode()).hexdigest()[::-1]
    h, s, v = [int(hash[i:i+4], base=16) / (16**4-1) for i in range(0, 12, 4)]
    rgb = hsv_to_rgb(h, 0.2 + 0.8*s, 0.4 + 0.6*v)
    colors = [hex(int(x))[2:].upper().zfill(2) for x in rgb]
    return "#" + "".join(colors)

