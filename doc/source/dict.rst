Persistent Dicts
================
A persistent dict is created by calling :func:`burrahobbit.dict` which returns
an object of the :class:`PersistentTreeMap` type (see below for a documentation
of its methods). :func:`burrahobbit.dict` behaves exactly the way the
builtin dict function of Python does, barring that it returns
instances of :class:`PersistentTreeMap` instead of regular dicts.

In addition to the methods described below, dictionaries implement
the binary operators &, | and ^ (and, or, xor): `a & b` returns a
new persistent dictionary containing a mapping from all the keys that are
contained in both `a` and `b` to the respective values in `b`; `a | b`
returns `a` updated with the mappings in `b` (if a key is defined in both
`a` and `b`, it is mapped to the value in `b`); `a ^ b` returns a new
persistent dictionary with all items whose key is only contained in
exactly one of them. The return value of `a & b` is always the same type
as `b` is (the rationale for this behaviour is that `a & b` only
contains nodes from `b`).

Example
-------

::

    >>> import burrahobbit
    >>> dct = burrahobbit.dict(foo=1)
    >>> dct["foo"]
    1
    >>> newdict = dct.assoc("bar", "spam")
    >>> dct["foo"]
    1
    >>> dct["bar"]
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/name/projects/burrahobbit/burrahobbit/treedict.py", line 46, in __getitem__
        return self.root.get(hash(key), 0, key).value
      File "/home/name/projects/burrahobbit/burrahobbit/treeset.py", line 46, in get
        raise KeyError(key)
    KeyError: 'bar'
    >>> newdict["foo"]
    1
    >>> newdict["bar"]
    'spam'
    >>> list(newdict)
    ['bar', 'foo']
    >>> list(newdict.iterkeys())
    ['bar', 'foo']
    >>> list(newdict.iteritems())
    [('bar', 'spam'), ('foo', 1)]
    >>> list(newdict.itervalues())
    ['spam', 1]
    >>> newerdict = newdict.without("foo")
    >>> newerdict["foo"]
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/home/name/projects/burrahobbit/burrahobbit/treedict.py", line 46, in __getitem__
        return self.root.get(hash(key), 0, key).value
      File "/home/name/projects/burrahobbit/burrahobbit/_tree.py", line 522, in get
        hsh, shift + SHIFT, key
      File "/home/name/projects/burrahobbit/burrahobbit/_tree.py", line 139, in get
        raise KeyError(key)
    KeyError: 'foo'
    >>> newerdict["bar"]
    'spam'
    >>>

API Reference
-------------

.. autoclass:: burrahobbit.treedict.PersistentTreeMap
    :members:
    :exclude-members: from_dict

.. autoclass:: burrahobbit.treedict.VolatileTreeMap
    :members: persistent
    
    All methods of PersistentTreeMap available, with the addition of
    :meth:`persistent`.
  