/*
Copyright (C) 2011 by Florian Mayer <florian.mayer@bitsrc.org>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

#include <stdlib.h>
#include <math.h>
#include <assert.h>

#define SHIFT 5
#define BMAP ((1 << SHIFT) - 1)
#define BRANCH 32

#define relevant(hsh, shift) (hsh >> shift & BMAP)

#define raise(errno) return errno
#define ret(value) *ret = value; return 0;

typedef struct _node node;
typedef unsigned int hashtype;

typedef struct {
    node* (*assoc)(node*, hashtype, int, node*);
    node* (*without)(node*, hashtype, int, void*);
    node* (*get)(node*, hashtype, int, void*);
    void (*deref)(node*);
    unsigned char (*cmp)(void*, void*);
} node_cls;

struct _node {
    node_cls* cls;
    unsigned int refs;
};

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    node* members[BRANCH];
} dispatch_node;

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    hashtype hsh;
    void* k;
} set_node;

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    hashtype hsh;
    int nmembers;
    set_node** members;
} collision_node;

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    hashtype hsh;
    void* k;
    void* v;
} assoc_node;


dispatch_node* new_dispatch(node* members[]);
collision_node* new_collision(int nmembers, set_node** members);

dispatch_node* dispatch_two(
    int shf, set_node* one, set_node* other
    );

void incref(node* x) {
    ++x->refs;
}

void decref(node* x) {
    if (!--x->refs) {
        x->cls->deref(x);
    }
}

node* dispatch_assoc(node* this, hashtype hsh, int shf, set_node* n) {
    hashtype rel = relevant(hsh, shf);
    
    dispatch_node* self = (dispatch_node*) this;
    node** newmembers = calloc(BRANCH, sizeof(node*));
    
    if (self->members[rel]) {
        newmembers[rel] = (node*) ((node_cls*) self->members[rel])->assoc(
            newmembers[rel], hsh, shf + SHIFT, n
        );
    } else {
        newmembers[rel] = n;
    }
    
    node* r = new_dispatch(newmembers);
    free(newmembers);
    return r;
}

node* dispatch_without(node* this, hashtype hsh, int shf, void* k) {
    hashtype rel = relevant(hsh, shf);
    
    dispatch_node* self = (dispatch_node*) this;
    node* newmembers[BRANCH];
    
    if (!self->members[rel]) {
        return this;
    }
    newmembers[rel] = ((node_cls*) self->members[rel])->without(
        newmembers[rel], hsh, shf + SHIFT, k
    );
    
    return new_dispatch(newmembers);
}

node* dispatch_get(node* this, hashtype hsh, int shf, void* k) {
    hashtype rel = relevant(hsh, shf);
    
    dispatch_node* self = (dispatch_node*) this;
    node* newmembers[BRANCH];
    
    if (!self->members[rel]) {
        return NULL;
    }
    return ((node_cls*) self->members[rel])->get(
        newmembers[rel], hsh, shf + SHIFT, k
    );
}

void dispatch_deref(node* this) {
    dispatch_node* self = (dispatch_node*) this;
    
    unsigned int i;
    for (i=0; i < BRANCH; ++i) {
        if (self->members[i] != NULL) {
            decref(self->members[i]);
        }
    }
    
    free(self);
}

node* collision_assoc(node* this, hashtype hsh, int shf, set_node* n) {
    collision_node* self = (collision_node*) this;
    set_node** newmembers;
    
    int i;
    for (i = 0; i < self->nmembers; ++i) {
        if (n->cls->cmp(n->k, self->members[i]->k)) {
            newmembers = calloc(self->nmembers, sizeof(void));
            memcpy(self->members, newmembers, self->nmembers);
            newmembers[i] = n;
            return new_collision(self->nmembers, newmembers);
        }
    }
    
    newmembers = calloc(self->nmembers + 1, sizeof(void));
    memcpy(self->members, newmembers, self->nmembers);
    newmembers[self->nmembers + 1] = n;
    return new_collision(self->nmembers + 1, newmembers);
}

node* collision_without(node* this, hashtype hsh, int shf, void* k) {
    collision_node* self = (collision_node*) this;
    
    set_node** newmembers;
    
    int i, j;
    for (i = 0; i < self->nmembers; ++i) {
        if (self->members[i]->cls->cmp(self->members[i]->k, k)) {
            if (!(self->nmembers - 1)) {
                return NULL;
            }
            newmembers = calloc(self->nmembers - 1, sizeof(void));
            for (j = 0; j < self->nmembers; ++j) {
                if (j < i) {
                    newmembers[j] = self->members[j];
                } else if (j > i) {
                    newmembers[j - 1] = self->members[j];
                }
            }
            return new_collision(self->nmembers - 1, newmembers);
        }
    }
    return self;
}

node* collision_get(node* this, hashtype hsh, int shf, void* k) {
    collision_node* self = (collision_node*) this;
    set_node** newmembers;
    
    int i;
    for (i = 0; i < self->nmembers; ++i) {
        if (self->members[i]->cls->cmp(self->members[i]->k, k)) {
            return self->members[i];
        }
    }
    
    return NULL;
}

void collision_deref(node* this) {
    collision_node* self = (collision_node*) this;
    
    unsigned int i;
    for (i=0; i < self->nmembers; ++i) {
        if (self->members[i] != NULL) {
            decref(self->members[i]);
        }
    }
    
    free(self);
}


node* null_assoc(node* this, hashtype hsh, int shf, set_node* n) {
    return n;
}

node* null_without(node* this, hashtype hsh, int shf, void* k) {
    return this;
}

node* null_get(node* this, hashtype hsh, int shf, void* k) {
    return NULL;
}

void null_deref(node* this) {
}

node* assoc_assoc(node* this, hashtype hsh, int shf, set_node* n) {
    assoc_node* self = (assoc_node*) this;
    if (self->hsh == hsh && self->cls->cmp(self->k, n->k)) {
        return n;
    } else {
        return dispatch_two(shf, ((set_node*) this), n);
    }
}

node* assoc_without(node* this, hashtype hsh, int shf, void* k) {
    assoc_node* self = (assoc_node*) this;
    if (self->hsh == hsh && self->cls->cmp(self->k, k)) {
        return NULL;
    } else {
        return this;
    }
}

node* assoc_get(node* this, hashtype hsh, int shf, void* k) {
    assoc_node* self = (assoc_node*) this;
    if (self->hsh == hsh && self->cls->cmp(self->k, k)) {
        return this;
    }
    return NULL;
}


const node_cls dispatch =
    { dispatch_assoc, dispatch_without, dispatch_get, dispatch_deref, NULL };
const node_cls collision =
    { collision_assoc, collision_without, collision_get, collision_deref, NULL };
const node_cls null = { null_assoc, null_without, null_get, null_deref, NULL };

const node nullnode = { &null, 1 };

dispatch_node* new_dispatch(node* members[]) {
    dispatch_node* updated = calloc(1, sizeof(dispatch_node));
    updated->cls = &dispatch;
    updated->refs = 1;
    int i;
    for (i = 0; i < BRANCH; ++i) {
        if (members[i] != NULL) {
            incref(members[i]);
        }
        updated->members[i] = members[i];
    }
    
    return updated;
}

dispatch_node* empty_dispatch() {
    dispatch_node* updated = calloc(1, sizeof(dispatch_node));
    updated->cls = &dispatch;
    updated->refs = 1;
    int i;
    for (i = 0; i < BRANCH; ++i) {
        updated->members[i] = NULL;
    }
    
    return updated;
}

dispatch_node* dispatch_two(
    int shf, set_node* one, set_node* other
    ) {
    dispatch_node* nd = empty_dispatch();
    dispatch_node* nnd;
    
    nnd = dispatch_assoc(nd, one->hsh, shf, one);
    decref(nd);
    nd = dispatch_assoc(nnd, other->hsh, shf, other);
    decref(nnd);
    return nd;
}

collision_node* new_collision(int nmembers, set_node** members) {
    unsigned int i;
    
    for (i = 0; i < nmembers; ++i) {
        incref(members[i]);
    }
    collision_node* updated = calloc(1, sizeof(collision_node));
    updated->cls = &collision;
    updated->refs = 1;
    updated->nmembers = nmembers;
    updated->members = members;
    updated->hsh = members[0]->hsh;
    return updated;
}

#include <Python.h>

static PyObject* make_Node(node* root);

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    hashtype hsh;
    PyObject* k;
    PyObject* v;
} pyassoc_node;

unsigned char pyassoc_cmp(void* vone, void* vother) {
    return PyObject_RichCompareBool(
        (PyObject*) vone,
        (PyObject*) vother, Py_EQ
    );
}

void pyassoc_deref(node* this) {
    pyassoc_node* self = (pyassoc_node*) self;
    Py_DECREF(self->k);
    Py_DECREF(self->v);
}

const node_cls pyassoc = { assoc_assoc, assoc_without, assoc_get, pyassoc_deref, pyassoc_cmp };

pyassoc_node* new_pyassoc(hashtype hsh, PyObject* k, PyObject* v) {
    pyassoc_node* updated = calloc(1, sizeof(pyassoc_node));
    if (updated == NULL)
        return NULL
    Py_INCREF(k);
    Py_INCREF(v);
    updated->cls = &pyassoc;
    updated->refs = 1;
    updated->k = k;
    updated->v = v;
    updated->hsh = hsh;
    return updated;
}


typedef struct {
    PyObject_HEAD
    node* root;
    /* Type-specific fields go here. */
} _ctree_NodeObject;

static void
Node_dealloc(_ctree_NodeObject* self)
{
    decref(self->root);
    self->ob_type->tp_free((PyObject*)self);
}

static PyObject*
Node_assoc(_ctree_NodeObject* self, PyObject *args, PyObject *kwds) {
    hashtype hsh;
    unsigned int shift;
    _ctree_NodeObject* node;

    static char *kwlist[] = {"hsh", "shift", "node", NULL};

    if (!PyArg_ParseTupleAndKeywords(
        args, kwds, "|iiO", kwlist, &hsh, &shift, &node))
        return -1; 
    return make_Node(
        self->root->cls->assoc(self->root, hsh, shift, node->root)
    );
}

static PyObject*
Node_get(_ctree_NodeObject* self, PyObject *args, PyObject *kwds) {
    hashtype hsh;
    unsigned int shift;
    PyObject key;

    static char *kwlist[] = {"hsh", "shift", "key", NULL};

    if (!PyArg_ParseTupleAndKeywords(
        args, kwds, "|iiO", kwlist, &hsh, &shift, &key))
        return -1; 
    return make_Node(
        (node*) self->root->cls->get(self->root, hsh, shift, &key));
}
    

static PyMethodDef Node_methods[] = {
    {NULL}  /* Sentinel */
};

static PyTypeObject _ctree_NodeType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
    "_ctree.Node",             /*tp_name*/
    sizeof(_ctree_NodeObject), /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    Node_dealloc,                         /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Node objects",           /* tp_doc */
    0,		               /* tp_traverse */
    0,		               /* tp_clear */
    0,		               /* tp_richcompare */
    0,		               /* tp_weaklistoffset */
    0,		               /* tp_iter */
    0,		               /* tp_iternext */
    Node_methods,             /* tp_methods */
    0,             /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    0,      /* tp_init */
    0,                         /* tp_alloc */
    0,                 /* tp_new */
};

static PyMethodDef _ctree_methods[] = {
    {NULL}  /* Sentinel */
};

static PyObject *
make_Node(node* root) {
    _ctree_NodeObject* self =
        (_ctree_NodeObject *)(_ctree_NodeType.tp_alloc(&_ctree_NodeType, 0));
    if (self != NULL) {
        self->root = root;
    }
    return (PyObject*) self;
}


#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
init_ctree(void) 
{
    PyObject* m;

    _ctree_NodeType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&_ctree_NodeType) < 0)
        return;

    m = Py_InitModule3("_ctree", _ctree_methods,
                       "Example module that creates an extension type.");

    Py_INCREF(&_ctree_NodeType);
    PyModule_AddObject(m, "NULLNODE", (PyObject *)(make_Node(&nullnode)));
}
