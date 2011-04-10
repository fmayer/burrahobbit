from burrahobbit._tree import BitMapDispatch, ListDispatch

def test_dispatch():
    nd = BitMapDispatch()
    for key in xrange(16):
        nd = nd.replace(key, None)
    assert isinstance(nd, BitMapDispatch)
    nd = nd.replace(17, None)
    assert isinstance(nd, ListDispatch)
