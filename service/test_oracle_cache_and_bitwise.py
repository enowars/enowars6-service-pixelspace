import datetime
import sys
import os
import secrets

def assert_equal(l,r):
    # assume equal length
    if len(l) == 0 and len(r) == 0:
        return
    if l[0] != r[0]:
        raise AssertionError
    assert_equal(l[1:], r[1:])

def main():
    n = 100000
    print("Gen random")
    strings = [bin(secrets.randbits(128)) for _ in range(n)]
    strings2 = [bin(secrets.randbits(128)) for _ in range(n)]
    print("Start comparisons")
    st = datetime.datetime.now()
    for i in range(len(strings)):
        assert_equal(strings[i], strings2[i])


    et = datetime.datetime.now()
    print("avg: {}ms".format(((et - st).total_seconds() / n) * 1000))

if __name__ == "__main__":
    main()