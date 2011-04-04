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

from copy import deepcopy, copy

from burrahobbit._tree import NULLNODE, SENTINEL
from burrahobbit.set import SetNode

class AssocNode(SetNode):
    """ A AssocNode contains the actual key-value mapping. """
    __slots__ = ['value']
    def __init__(self, key, value):
        SetNode.__init__(self, key)
        self.value = value
    
    def __repr__(self):
        return '<AssocNode(%r, %r)>' % (self.key, self.value)
    
    def __copy__(self):
        return AssocNode(self.key, self.value)


class PersistentTreeMap(object):
    __slots__ = ['root']
    def __init__(self, root=NULLNODE):
        self.root = root
    
    def __getitem__(self, key):
        return self.root.get(hash(key), 0, key).value
    
    def __and__(self, other):
        return PersistentTreeMap(self.root & other.root)
    
    def __xor__(self, other):
        return PersistentTreeMap(self.root ^ other.root)
    
    def __or__(self, other):
        return PersistentTreeMap(self.root | other.root)
    
    def assoc(self, key, value):
        """ Return copy of self with an association between key and value.
        May override an existing association. """
        return PersistentTreeMap(
            self.root.assoc(hash(key), 0, AssocNode(key, value))
        )
    
    def without(self, key):
        """ Return copy of self with key removed. """
        return PersistentTreeMap(
            self.root.without(hash(key), 0, key)
        )
    
    def __iter__(self):
        for node in self.root:
            yield node.key
    
    iterkeys = __iter__
    
    def iteritems(self):
        for node in self.root:
            yield node.key, node.value
    
    def itervalues(self):
        for node in self.root:
            yield node.value
    
    @staticmethod
    def from_dict(dct):
        """ Create PersistentTreeMap from existing dictionary. """
        mp = VolatileTreeMap()
        for key, value in dct.iteritems():
            mp = mp.assoc(key, value)
        return mp.persistent()
    
    def volatile(self):
        return VolatileTreeMap(copy(self.root))
    
    @staticmethod
    def construct(argument=SENTINEL, **kwargs):
        if kwargs:
            if argument is not SENTINEL:
                kwargs['argument'] = argument
            return PersistentTreeMap.from_dict(kwargs)
        
        if argument is SENTINEL:
            return PersistentTreeMap()
        
        mp = VolatileTreeMap()
        # Let the TypeError propagate.
        for key, value in argument:
            mp.assoc(key, value)
        return mp.persistent()


class VolatileTreeMap(PersistentTreeMap):
    def assoc(self, key, value):
        """ Update this VolatileTreeMap to contain an association between
        key and value.
        
        USE WITH CAUTION: This should only be used if no other reference
        to the PersistentTreeMap may exist. """
        self.root = self.root._iassoc(hash(key), 0, AssocNode(key, value))
        return self
    
    def without(self, key):
        """ Remove key.
        
        USE WITH CAUTION: This should only be used if no other reference
        to the PersistentTreeMap may exist. """
        self.root = self.root._iwithout(hash(key), 0, key)
        return self
    
    def persistent(self):
        return PersistentTreeMap(self.root)


def main():    
    mp = PersistentTreeMap()
    mp1 = mp.assoc('a', 'hello')
    assert mp1['a'] == 'hello'
    mp2 = mp1.assoc('b', 'world')
    assert mp2['a'] == 'hello'
    assert mp2['b'] == 'world'
    mp3 = mp2.without('a')
    assert mp3['b'] == 'world'
    try:
        assert mp3['a'] == 'hello'
    except KeyError, e:
        if e.args[0] != 'a':
            assert False
    else:
        assert False
    
    assert set(mp2.iterkeys()) == set(mp2) == set(['a', 'b'])
    assert set(mp2.itervalues()) == set(['hello', 'world'])
    assert set(mp2.iteritems()) == set([('a', 'hello'), ('b', 'world')])
    
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
    
    mp4 = mp3.volatile()
    mp5 = mp4.assoc('foo', 'bar')
    assert mp4['foo'] == 'bar'
    assert mp5['foo'] == 'bar'
    assert mp4 is mp5
    
    mp6 = mp5.persistent()
    mp7 = mp6.assoc('foo', 'spam')
    assert mp4['foo'] == 'bar'
    assert mp5['foo'] == 'bar'
    assert mp6['foo'] == 'bar'
    assert mp7['foo'] == 'spam'
    
    try:
        mp3['foo']
    except KeyError:
        assert True
    else:
        assert False
    
    bar = []
    mpv = VolatileTreeMap()
    mpv.assoc("foo", bar)
    mpp = mpv.persistent()
    bar.append("test")
    assert mpp["foo"] == mpv["foo"] == bar
    
    mp = PersistentTreeMap()
    bar = []
    mp = mp.assoc("foo", bar)
    mv = mp.volatile()
    bar.append("test")
    assert mp["foo"] == mv["foo"] == bar



if __name__ == '__main__':
    main()
