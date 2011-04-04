# Copyright (C) 2011 by Florian Mayer <flormayer@aim.com>
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

import pytest

from burrahobbit.treedict import PersistentTreeMap, VolatileTreeMap

def test_fromdict():
    mp = PersistentTreeMap.from_dict(
        {'hello': 'world', 'spam': 'eggs'}
    )
    assert mp['hello'] == 'world'
    assert mp['spam'] == 'eggs'


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
    mp = PersistentTreeMap.from_dict({'a': 'hello', 'b': 'world'})
    assert set(mp.iterkeys()) == set(mp) == set(['a', 'b'])
    assert set(mp.itervalues()) == set(['hello', 'world'])
    assert set(mp.iteritems()) == set([('a', 'hello'), ('b', 'world')])


def test_novaluecopy():
    mp = PersistentTreeMap()
    bar = []
    mp = mp.assoc("foo", bar)
    mv = mp.volatile()
    bar.append("test")
    assert mp["foo"] == mv["foo"] == bar


def test_volatile():
    mp = PersistentTreeMap.from_dict({'foo': 'baz'})
    mp2 = mp.volatile()
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


def main():
    import os
    import time
    # Prevent expensive look-up in loop, hence the from-import.
    from copy import copy

    mp = PersistentTreeMap().volatile()
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
