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

from copy import copy, deepcopy
from itertools import izip

SENTINEL = object()

SHIFT = 5
BMAP = (1 << SHIFT) - 1
BRANCH = 2 ** SHIFT

MAXBITMAPDISPATCH = 16

def relevant(hsh, shift):
    """ Return the relevant part of the hsh on the level shift. """
    return hsh >> shift & BMAP


POPCOUNT_TBL = [0] * (2 ** 16)
for idx in xrange(2 ** 16):
    POPCOUNT_TBL[idx] = (idx & 1) + POPCOUNT_TBL[idx >> 1]

def bit_count(v):
    return (POPCOUNT_TBL[v & 0xffff] +
            POPCOUNT_TBL[(v >> 16) & 0xffff])


def doc(docstring):
    """ Decorator to set docstring of function to docstring. """
    def deco(fn):
        """ Implementation detail. """
        fn.__doc__ = docstring
        return fn
    return deco


ASSOC = "\n".join([
    "Add AssocNode node whose key's hash is hsh to the node or its children.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH. If a node with the same key already",
    "exists, override it.",
])

IASSOC = "\n".join([
    "Modify so that the AssocNode whose key's hash is hsh is added to it.",
    "USE WITH CAUTION.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH. If a node with the same key already",
    "exists, override it.",
])

GET = "\n".join([
    "Get value of the AssocNode with key whose hash is hsh in the subtree.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH.",
])

WITHOUT = "\n".join([
    "Remove AssocNode with key whose hash is hsh from the subtree.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH.",
])

IWITHOUT = "\n".join([
    "Modify so that the AssocNode whose key's hash is hsh is removed from it.",
    "USE WITH CAUTION.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH.",
])


class Node(object):
    __slots__ = []
    def __and__(self, other):
        new = NULLNODE
        
        for node in other:
            try:
                self.get(hash(node.key), 0, node.key)
            except KeyError:
                pass
            else:
                new = new._iassoc(hash(node.key), 0, node)
        return new
    
    def __xor__(self, other):
        new = self
        for node in other:
            new = new.xor(node.hsh, 0, node)
        return new
    
    def __or__(self, other):
        new = self
        for node in other:
            new = new.assoc(node.hsh, 0, node)
        return new
    
    def __eq__(self, other):
        return all(node == othernode for node, othernode in izip(self, other))
    
    def __neq__(self, other):
        return any(node != othernode for node, othernode in izip(self, other))


class NullNode(Node):
    """ Dummy node being the leaf of branches that have no entries. """
    __slots__ = []
    def xor(self, hsh, shift, node):
        return node
    
    _ixor = xor
    
    @doc(ASSOC)
    def assoc(self, hsh, shift, node):
        # Because there currently no node, the new node
        # is the node to be added.
        return node
    
    # The NullNode does not need to be modified if a new association is
    # created because it only returns the new node, hence _iassoc = assoc.
    _iassoc = assoc
    
    def get(self, hsh, shift, key):
        # There is no entry with the searched key because the hash leads
        # to a branch ending in a NullNode.
        raise KeyError(key)
    
    @doc(WITHOUT)
    def without(self, hsh, shift, key):
        # There is no entry with the key to be removed because the hash leads
        # to a branch ending in a NullNode.
        raise KeyError(key)
    
    _iwithout = without
    
    def __iter__(self):
        # There are no keys contained in a NullNode. Hence, an empty
        # iterator is returned.
        return iter([])
    
    # Likewise, there are no values and items in a NullNode.
    iteritems = itervalues = __iter__
    
    def __copy__(self):
        return self
    
    def cutoff(self, hsh):
        return self


# We only need one instance of a NullNode because it does not contain
# any data.
NULLNODE = NullNode()


class HashCollisionNode(Node):
    """ If hashes of two keys collide, store them in a list and when a key
    is searched, iterate over that list and find the appropriate key. """
    __slots__ = ['children', 'hsh']
    def __init__(self, nodes):
        self.children = nodes
        self.hsh = hash(nodes[0].hsh)

    def xor(self, hsh, shift, node):
        if not any(node.key == child.key for child in self.children):
            return HashCollisionNode(self.children + [node])
        return self
    
    def _ixor(self, hsh, shift, node):
        if not any(node.key == child.key for child in self.children):
            self.children.append(node)
        return self
    
    @doc(GET)
    def get(self, hsh, shift, key):
        # To get the child we want we need to iterate over all possible ones.
        # The contents of children are always AssocNodes,
        # so we can safely access the key member.
        for node in self.children:
            if key == node.key:
                return node
        raise KeyError(key)
    
    @doc(ASSOC)
    def assoc(self, hsh, shift, node):
        # If we have yet another key with a colliding key, return a new node
        # with it added to the children, otherwise return a DispatchNode.
        if hsh == self.hsh:
            return HashCollisionNode(self.children + [node])
        return DispatchNode.make(shift, [self, node])
    
    @doc(IASSOC)
    def _iassoc(self, hsh, shift, node):
        # If we have yet another key with a colliding key, add it to the
        # children, otherwise return a DispatchNode.
        if hsh == self.hsh:
            self.children.append(node)
            return self
        return DispatchNode.make(shift, [self, node])
    
    @doc(WITHOUT)
    def without(self, hsh, shift, key):
        # Remove the node whose key is key from the children. If it was the
        # last child, return NULLNODE. If there was no member with a
        # matching key, raise KeyError.
        newchildren = [node for node in self.children if node.key != key]
        if not newchildren:
            return NULLNODE
        
        if newchildren == self.children:
            raise KeyError(key)
        
        return HashCollisionNode(newchildren)
    
    @doc(IWITHOUT)
    def _iwithout(self, hsh, shift, key):
        newchildren = [node for node in self.children if node.key != key]
        if not newchildren:
            return NULLNODE
        
        if newchildren == self.children:
            raise KeyError(key)
        
        self.children = newchildren
        return self
    
    def __iter__(self):
        for node in self.children:
            for elem in node:
                yield elem
    
    def __copy__(self):
        return HashCollisionNode(map(copy, self.children))
    
    def cutoff(self, hsh):
        if self.hsh <= hsh:
            return NULLNODE
        return self


class ListDispatch(Node):
    """ Light weight dictionary like object for a little amount of items.
    Only feasable for a little amount of items as a list of length nitems 
    is always stored.
    
    Only accepts integers as keys. """
    __slots__ = ['items']
    
    def __init__(self, nitems=None, items=None):
        if items is None:
            items = [SENTINEL for _ in xrange(nitems)]
        self.items = items
    
    def replace(self, key, item):
        """ Return a new ListDispatch with the the keyth item replaced
        with item. """
        return ListDispatch(
            None,
            self.items[:key] +
            [item] +
            self.items[key + 1:]
        )
    
    def _ireplace(self, key, item):
        """ Replace keyth item with item.
        
        USE WITH CAUTION. """
        self.items[key] = item
        return self
    
    def __getitem__(self, key):
        value = self.items[key]
        if value is SENTINEL:
            raise KeyError(key)
        return value
    
    def get(self, key, default):
        """ Get keyth item. If it is not present, return default. """
        value = self.items[key]
        if value is not SENTINEL:
            return value
        return default
    
    def remove(self, key):
        """ Return new ListDispatch with keyth item removed.
        Will not raise KeyError if it was not present. """        
        return self.replace(key, SENTINEL)

    def _iremove(self, key):
        """ Remove keyth item. Will not raise KeyError if it was not present.
        
        USE WITH CAUTION. """
        self._ireplace(key, SENTINEL)
        return self
    
    def to_bitmapdispatch(self):
        dispatch = BitMapDispatch()
        for key, value in enumerate(self.items):
            if value is not SENTINEL:
                dispatch._ireplace(key, value)
        return dispatch
    
    def __iter__(self):
        return (item for item in self.items if item is not SENTINEL)
    
    def __copy__(self):
        return ListDispatch(items=self.items[:])
    
    def __deepcopy__(self):
        return ListDispatch(items=map(deepcopy, self.items))
    
    def map(self, fn):
        return ListDispatch(
            items=[SENTINEL if elem is SENTINEL else fn(elem)
                   for elem in self.items]
        )


class BitMapDispatch(Node):
    """ Light weight dictionary like object for a little amount of items.
    Best used for as most as many items as an integer has bits (usually 32).
    Only accepts integers as keys.
    
    The items are stored in a list and whenever an item is added, the bitmap
    is ORed with (1 << key) so that the keyth bit is set.
    The amount of set bits before the nth bit is used to find the index of the
    item referred to by key in the items list.
    """
    __slots__ = ['bitmap', 'items']
    def __init__(self, bitmap=0, items=None):
        if items is None:
            items = []
        self.bitmap = bitmap
        self.items = items
    
    def replace(self, key, item):
        """ Return a new BitMapDispatch with the the keyth item replaced
        with item. """
        # If the item already existed in the list, we need to replace it.
        # Otherwise, it will be added to the list at the appropriate
        # position.
        if len(self.items) >= MAXBITMAPDISPATCH:
            new = self.to_listdispatch(BRANCH)
            return new._ireplace(key, item)
        
        notnew = bool(self.bitmap & 1 << key)
        newmap = self.bitmap | 1 << key
        idx = bit_count(self.bitmap & ((1 << key) - 1))
        return BitMapDispatch(
            newmap,
            # If notnew is True, the item that is replaced by the new item
            # is left out, otherwise the new item is inserted. Refer to
            # _ireplace for a more concise explanation.
            self.items[:idx] + [item] + self.items[idx+notnew:]
        )
    
    def _ireplace(self, key, item):
        """ Replace keyth item with item.
        
        USE WITH CAUTION. """
        if len(self.items) >= MAXBITMAPDISPATCH:
            new = self.to_listdispatch(BRANCH)
            return new._ireplace(key, item)
        
        notnew = bool(self.bitmap & 1 << key)
        self.bitmap |= 1 << key
        idx = bit_count(self.bitmap & ((1 << key) - 1))
        if idx == len(self.items):
            self.items.append(item)
        elif notnew:
            self.items[idx] = item
        else:
            self.items.insert(idx, item)
        
        return self
    
    def get(self, key, default=None):
        """ Get keyth item. If it is not present, return default. """
        if not self.bitmap & 1 << key:
            return default
        return self.items[bit_count(self.bitmap & ((1 << key) - 1))]
    
    def remove(self, key):
        """ Return new BitMapDispatch with keyth item removed.
        Will not raise KeyError if it was not present. """
        idx = bit_count(self.bitmap & ((1 << key) - 1))
        return BitMapDispatch(
            # Unset the keyth bit.
            self.bitmap & ~(1 << key),
            # Leave out the idxth item.
            self.items[:idx] + self.items[idx+1:]
        )
    
    def _iremove(self, key):
        """ Remove keyth item. Will not raise KeyError if it was not present.
        
        USE WITH CAUTION. """
        idx = bit_count(self.bitmap & ((1 << key) - 1))
        self.bitmap &= ~(1 << key)
        self.items.pop(idx)
        return self
    
    def __getitem__(self, key):
        if not self.bitmap & 1 << key:
            raise KeyError(key)
        return self.items[bit_count(self.bitmap & ((1 << key) - 1))]
    
    def to_listdispatch(self, nitems):
        """ Return ListDispatch with the same key to value connections as this
        BitMapDispatch. """
        return ListDispatch(
            None, [self.get(n, SENTINEL) for n in xrange(nitems)]
        )
    
    def __iter__(self):
        return iter(self.items)
    
    def __nonzero__(self):
        return bool(self.items)
    
    def __copy__(self):
        return BitMapDispatch(self.bitmap, self.items[:])
    
    def __deepcopy__(self):
        return BitMapDispatch(self.bitmap, map(deepcopy, self.items))
    
    def map(self, fn):
        return BitMapDispatch(
            self.bitmap,
            [fn(elem) for elem in self.items]
        )


class DispatchNode(Node):
    """ Dispatch to children nodes depending of the hsh value at the
    current level. """
    __slots__ = ['children']
    def __init__(self, children=None):
        if children is None:
            children = BitMapDispatch()
        
        self.children = children
    
    def xor(self, hsh, shift, node):
        rlv = relevant(hsh, shift)
        newchild = self.children.get(rlv, NULLNODE).xor(hsh, shift + SHIFT, node)
        if newchild is NULLNODE:
            # This makes sure no dead nodes remain in the tree after
            # removing an item.
            newchildren = self.children.remove(rlv)
            if not newchildren:
                return NULLNODE
        else:
            newchildren = self.children.replace(
                rlv, 
                newchild
            )
        
        return DispatchNode(newchildren)
    
    def _ixor(self, hsh, shift, node):
        rlv = relevant(hsh, shift)
        newchild = self.children[rlv].xor(hsh, shift + SHIFT, node)
        if newchild is NULLNODE:
            self.children = self.children._iremove(rlv)
            if not self.children:
                return NULLNODE
        else:
            self.children = self.children._ireplace(rlv, newchild)
        
        return self
    
    @doc(ASSOC)
    def assoc(self, hsh, shift, node):
        # We need not check whether the return value of
        # self.children.get(...).assoc is NULLNODE, because assoc never
        # returns NULLNODE.
        rlv = relevant(hsh, shift)
        return DispatchNode(
            self.children.replace(
                rlv,
                self.children.get(rlv, NULLNODE).assoc(
                    hsh, shift + SHIFT, node
                )
            )
        )
    
    @doc(IASSOC)
    def _iassoc(self, hsh, shift, node):
        rlv = relevant(hsh, shift)
        self.children = self.children._ireplace(
            rlv, 
            self.children.get(rlv, NULLNODE)._iassoc(hsh, shift + SHIFT, node)
        )
        return self
    
    @classmethod
    def make(cls, shift, many):
        # Because the object we create in this function is not yet exposed
        # to any other code, we may safely call _iassoc.
        dsp = cls()
        for elem in many:
            dsp._iassoc(elem.hsh, shift, elem)
        return dsp
    
    @doc(GET)
    def get(self, hsh, shift, key):
        return self.children.get(relevant(hsh, shift), NULLNODE).get(
            hsh, shift + SHIFT, key
        )
    
    @doc(WITHOUT)
    def without(self, hsh, shift, key):
        rlv = relevant(hsh, shift)
        newchild = self.children[rlv].without(hsh, shift + SHIFT, key)
        if newchild is NULLNODE:
            # This makes sure no dead nodes remain in the tree after
            # removing an item.
            newchildren = self.children.remove(rlv)
            if not newchildren:
                return NULLNODE
        else:
            newchildren = self.children.replace(
                rlv, 
                newchild
            )
        
        return DispatchNode(newchildren)
    
    @doc(IWITHOUT)
    def _iwithout(self, hsh, shift, key):
        rlv = relevant(hsh, shift)
        newchild = self.children[rlv]._iwithout(hsh, shift + SHIFT, key)
        if newchild is NULLNODE:
            self.children = self.children._iremove(rlv)
            if not self.children:
                return NULLNODE
        else:
            self.children = self.children._ireplace(rlv, newchild)
        
        return self
    
    def __iter__(self):
        for child in self.children:
            for elem in child:
                yield elem
    
    def __copy__(self):
        return DispatchNode(self.children.map(copy))
