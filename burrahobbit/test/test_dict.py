# Copyright (C) 2011 by Florian Mayer <florian.mayer@bitsrc.org>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os
import pytest

from copy import copy

from burrahobbit.treedict import PersistentTreeMap


class HashCollision(object):
    def __init__(self, item, hsh):
        self.item = item
        self.hsh = hsh
    
    def __hash__(self):
        return self.hsh
    
    def __eq__(self, other):
        return isinstance(other, HashCollision) and self.item == other.item


def random_dict(size):
    return dict((os.urandom(20), os.urandom(25)) for _ in xrange(size))


def test_or():
    some = random_dict(1000)
    some.update({'a': 'foo', 'b': 'bar', 'c': 'blub'})
    other = random_dict(1000)
    other = {'a': 'blub', 'c': 'blab', 'd': 'quuz'}
    
    df = PersistentTreeMap.from_dict(some) | PersistentTreeMap.from_dict(other)
    some.update(other)
    assert set(df.iteritems()) == set(some.iteritems())


def test_xor():
    some = random_dict(1000)
    some.update({'a': 'foo', 'b': 'bar', 'c': 'blub'})
    other = random_dict(1000)
    other.update({'a': 'blub', 'c': 'blab', 'd': 'quuz'})
    
    df = PersistentTreeMap.from_dict(some) ^ PersistentTreeMap.from_dict(other)
    
    for key, value in df.iteritems():
        assert (
            key in some and key not in other and some[key] == value
        ) or key in other and key not in some and other[key] == value


def test_and():
    some = random_dict(1000)
    some.update({'a': 'foo', 'b': 'bar', 'c': 'blub'})
    other = random_dict(1000)
    other.update({'a': 'blub', 'c': 'blab', 'd': 'quuz'})
    
    third = copy(some)
    third.update(other)
    
    df = PersistentTreeMap.from_dict(some) & PersistentTreeMap.from_dict(other)
    
    for key in third:
        if key in some and key in other:
            assert df[key] == other[key]


def test_fromdict():
    dct = random_dict(1000)
    mp = PersistentTreeMap.from_dict(dct)
    for key, value in dct.iteritems():
        assert mp[key] == value


def test_persistence():
    mp = PersistentTreeMap()
    mp1 = mp.assoc('a', 'hello')
    assert mp1['a'] == 'hello'
    mp2 = mp1.assoc('b', 'world')
    assert mp2['a'] == 'hello'
    assert mp2['b'] == 'world'
    mp3 = mp2.without('a')
    assert mp3['b'] == 'world'
    with pytest.raises(KeyError) as excinfo:
        assert mp3['a'] == 'hello'
    assert excinfo.value.args[0] == 'a'


def test_iteration():
    dct = random_dict(1000)
    mp = PersistentTreeMap.from_dict(dct)
    assert set(mp.iterkeys()) == set(mp) == set(dct.iterkeys())
    assert set(mp.itervalues()) == set(dct.itervalues())
    assert set(mp.iteritems()) == set(dct.iteritems())


def test_novaluecopy():
    mp = PersistentTreeMap()
    bar = []
    mp = mp.assoc("foo", bar)
    mv = mp.transient()
    bar.append("test")
    assert mp["foo"] == mv["foo"] == bar


def test_transient():
    mp = PersistentTreeMap.from_dict({'foo': 'baz'})
    mp2 = mp.transient()
    mp3 = mp2.assoc('foo', 'bar')
    assert mp2['foo'] == 'bar'
    assert mp3['foo'] == 'bar'
    assert mp2 is mp3
    assert mp['foo'] == 'baz'
    
    mp4 = mp3.persistent()
    mp5 = mp4.assoc('foo', 'spam')
    assert mp2['foo'] == 'bar'
    assert mp3['foo'] == 'bar'
    assert mp4['foo'] == 'bar'
    assert mp5['foo'] == 'spam'


def test_collision():
    HASH = 13465345
    mp = PersistentTreeMap()
    mp = mp.assoc(HashCollision("hello", HASH), "world")
    mp = mp.assoc(HashCollision("answer", HASH), 42)
    assert mp[HashCollision("hello", HASH)] == "world"
    assert mp[HashCollision("answer", HASH)] == 42


def test_neq():
    some = random_dict(1000)
    some.update({'a': 'foo', 'b': 'bar', 'c': 'blub'})
    other = random_dict(1000)
    other.update({'a': 'blub', 'c': 'blab', 'd': 'quuz'})
    assert (
        PersistentTreeMap.from_dict(some) != PersistentTreeMap.from_dict(other)
    )


def test_eq():
    some = random_dict(1000)
    assert (
        PersistentTreeMap.from_dict(some) == PersistentTreeMap.from_dict(some)
    )


def main():
    import os
    import time
    
    mp = PersistentTreeMap().transient()
    for _ in xrange(22500):
        one, other = os.urandom(20), os.urandom(25)
        mp2 = mp.assoc(one, other)
        assert mp[one] == other
        assert mp2[one] == other
        mp = mp2
    pmp = mp.persistent()    
    
    s = time.time()
    mp = PersistentTreeMap()
    for _ in xrange(225000):
        one, other = os.urandom(20), os.urandom(25)
        mp2 = mp.assoc(one, other)
        try:
            mp[one]
        except KeyError:
            assert True
        else:
            assert False
        try:
            mp2.without(one)[one]
        except KeyError:
            assert True
        else:
            assert False
        mp = mp2
        assert mp[one] == other
    print 'PersistentHashMap:', time.time() - s
    assert mp[one] == other
    # This /may/ actually fail if we are unlucky, but it's a good start.
    assert len(list(iter(mp))) == 225000


if __name__ == '__main__':
    main()
