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
from burrahobbit.treeset import SetNode

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
        """ Yield keys for all items. """
        for node in self.root:
            yield node.key
    
    iterkeys = __iter__
    
    def iteritems(self):
        """ Yield key, value pairs for all items. """
        for node in self.root:
            yield node.key, node.value
    
    def itervalues(self):
        """ Yield values for all items. """
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
        """ Return volatile (mutable) copy of self. Changing the copy will not
        affect the original object's immutability.
        
        See :class:`VolatileTreeMap`. """
        return VolatileTreeMap(copy(self.root))
    
    @staticmethod
    def construct(argument=SENTINEL, **kwargs):
        if kwargs:
            if argument is not SENTINEL:
                kwargs['argument'] = argument
            return PersistentTreeMap.from_dict(kwargs)
        
        if argument is SENTINEL:
            return PersistentTreeMap()
        
        return PersistentTreeMap.from_dict(argument)


class VolatileTreeMap(PersistentTreeMap):
    """
    VolatileTreeMaps are used if - and only if - one function does so many
    changes to a PersistentTreeMap the immutability would prove inefficient.
    
    The function has to return volatiletreemap.persistent() in order to ensure
    that the treemap cannot be changed afterwards. """
    _without = PersistentTreeMap.without
    _assoc = PersistentTreeMap.assoc
    
    def assoc(self, key, value):
        """ Update this VolatileTreeMap to contain an association between
        key and value and return self. You should never assume that the
        object really is mutated as this only is an optimization, thus, you
        should always bind the return value of this function to the 
        respective name, e.g., `mymap.assoc("spam", "eggs")` should be avoided
        and written as `mymap = mymap.assoc("spam", "eggs")` instead. """
        self.root = self.root._iassoc(hash(key), 0, AssocNode(key, value))
        return self
    
    def without(self, key):
        """ Remove key. """
        self.root = self.root._iwithout(hash(key), 0, key)
        return self
    
    def persistent(self):
        """ Make the VolatileTreeMap immutable and return it. Often used in
        the idiom `return mymap.persistent()`. """
        # By modifing the original object, it is ensured that even if another
        # reference is held, it cannot modify the underlying tree. If a copy
        # of the VolatileTreeMap with a reference to the original tree is held
        # somewhere, there is nothing we can do, though.
        self.without = self._without
        self.assoc = self._assoc
        return self
    
    def volatile(self):
        return self
