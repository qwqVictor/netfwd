# Modified by Victor Huang. Original: Copyright (C) 2011 by Ben Noordhuis <info@bnoordhuis.nl> https://gist.github.com/bnoordhuis/1035947
TMIN = 1
TMAX = 26
BASE = 36
SKEW = 38
DAMP = 700 # initial bias adaptation
INITIAL_N = 128
INITIAL_BIAS = 72
assert 0 <= TMIN <= TMAX <= (BASE - 1)
assert 1 <= SKEW
assert 2 <= DAMP
assert (INITIAL_BIAS % BASE) <= (BASE - TMIN) # always true if TMIN=1
class Error(Exception):
    pass

def basic(c):
    return c < 128

def encode_digit(d):
    return d + (97 if d < 26 else 22)

def decode_digit(d):
    if d >= 48 and d <= 57:
        return d - 22 # 0..9
    if d >= 65 and d <= 90:
        return d - 65 # A..Z
    if d >= 97 and d <= 122:
        return d - 97 # a..z
    raise Error('Illegal digit #%d' % d)

def next_smallest_codepoint(non_basic, n):
    m = 0x110000 # Unicode's upper bound + 1
    for c in non_basic:
        if c >= n and c < m:
            m = c
    assert m < 0x110000
    return m

def adapt_bias(delta, n_points, is_first):
    # scale back, then increase delta
    delta //= DAMP if is_first else 2
    delta += delta // n_points

    s = (BASE - TMIN)
    t = (s * TMAX) // 2 # threshold=455
    k = 0

    while delta > t:
        delta //= s
        k += BASE

    a = (BASE - TMIN + 1) * delta
    b = (delta + SKEW)

    return k + (a // b)

def threshold(k, bias):
    if k <= bias + TMIN:
        return TMIN
    if k >= bias + TMAX:
        return TMAX
    return k - bias

def encode_int(bias, delta):
    result = []

    k = BASE
    q = delta

    while True:
        t = threshold(k, bias)
        if q < t:
            result.append(encode_digit(q))
            break
        else:
            c = t + ((q - t) % (BASE - t))
            q = (q - t) // (BASE - t)
            k += BASE
            result.append(encode_digit(c))

    return result


def punycode_encode(input):
    input = [ord(c) for c in input]
    output = [c for c in input if basic(c)]
    non_basic = [c for c in input if not basic(c)]

    # remember how many basic code points there are 
    b = h = len(output)

    if output:
        output.append(ord('-'))

    n = INITIAL_N
    bias = INITIAL_BIAS
    delta = 0

    while h < len(input):
        m = next_smallest_codepoint(non_basic, n)
        delta += (m - n) * (h + 1)
        n = m

        for c in input:
            if c < n:
                delta += 1
                assert delta > 0
            elif c == n:
                output.extend(encode_int(bias, delta))
                bias = adapt_bias(delta, h + 1, b == h)
                delta = 0
                h += 1

        delta += 1
        n += 1

    return ''.join(chr(c) for c in output)[:-1]