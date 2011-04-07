Persistent Sets
===============
A persistent set is created by calling :func:`burrahobbit.set` which returns
an object of the :class:`PersistentTreeSet` type (see below for a documentation
of its methods). :func:`burrahobbit.set` behaves exactly the way the
builtin :func:`set` function of Python does, barring that it returns
instances of :class:`PersistentTreeSet` instead of regular dicts.

In addition to the methods described below, sets implement
the binary operators &, | and ^ (and, or, xor): `a & b` returns a
new value of `b`'s type consisting of all items of `b` whose key is
also present in `a`; `a | b`
returns `a` updated with the elements in `b`; `a ^ b` returns a new
persistent set with all items that are only contained in
exactly one of them. The return value of `a & b` is always the same type
as `b` is (the rationale for this behaviour is that `a & b` only
contains nodes from `b`).


.. autoclass:: burrahobbit.treeset.PersistentTreeSet
    :members:
    :exclude-members: from_set

.. autoclass:: burrahobbit.treeset.VolatileTreeSet
    :members: persistent
    
    All methods of PersistentTreeSet available, with the addition of
    :meth:`persistent`.