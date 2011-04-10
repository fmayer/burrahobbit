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

from burrahobbit.treeset import PersistentTreeSet


class HashCollision(object):
    def __init__(self, item, hsh):
        self.item = item
        self.hsh = hsh
    
    def __hash__(self):
        return self.hsh
    
    def __eq__(self, other):
        return isinstance(other, HashCollision) and self.item == other.item


def random_set(size):
    return set(os.urandom(20) for _ in xrange(size))


def test_or():
    some = random_set(1000)
    some.update(['a', 'b', 'c'])
    other = random_set(1000)
    other.update(set(['a', 'c', 'd']))
    
    df = PersistentTreeSet.from_set(some) | PersistentTreeSet.from_set(other)
    some.update(other)
    assert set(df) == some


def test_xor():
    some = random_set(1000)
    some.update(['a', 'b', 'c'])
    other = random_set(1000)
    other.update(set(['a', 'c', 'd']))
    
    df = PersistentTreeSet.from_set(some) ^ PersistentTreeSet.from_set(other)
    
    assert set(df) == some ^ other


def test_and():
    some = random_set(1000)
    some.update(['a', 'b', 'c'])
    other = random_set(1000)
    other.update(set(['a', 'c', 'd']))
    
    df = PersistentTreeSet.from_set(some) & PersistentTreeSet.from_set(other)
    
    assert set(df) == some & other


def test_fromset():
    st = random_set(1000)
    mp = PersistentTreeSet.from_set(st)
    for elem in st:
        assert elem in mp


def test_persistence():
    mp = PersistentTreeSet()
    mp1 = mp.add('a')
    assert 'a' in mp1
    mp2 = mp1.add('b')
    assert 'a' in mp2
    assert 'b' in mp2
    assert 'b' not in mp1
    mp3 = mp2.without('a')
    assert 'b' in mp3
    assert 'a' not in mp3


def test_iteration():
    st = random_set(1000)
    mp = PersistentTreeSet.from_set(st)
    assert set(mp) == st


def test_transient():
    mp = PersistentTreeSet.from_set(set(['foo']))
    mp2 = mp.transient()
    mp3 = mp2.add('bar')
    assert mp2 is mp3
    assert 'foo' in mp2
    assert 'bar' in mp2
    assert 'foo' in mp3
    assert 'bar' in mp3
    
    mp4 = mp3.persistent()
    mp5 = mp4.add('baz')
    assert 'baz' not in mp2
    assert 'baz' not in mp3
    assert 'baz' not in mp4
    assert 'baz' in mp5
    assert mp5 is not mp4


def test_collision():
    HASH = 13465345
    mp = PersistentTreeSet()
    mp = mp.add(HashCollision("hello", HASH))
    mp = mp.add(HashCollision("answer", HASH))
    assert HashCollision("hello", HASH) in mp
    assert HashCollision("answer", HASH) in mp
