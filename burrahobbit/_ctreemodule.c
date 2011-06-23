#include <Python.h>
#include "_ctree.h"

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

const node_cls pyassoc =
    { assoc_assoc, assoc_without, assoc_get, pyassoc_deref, pyassoc_cmp };

pyassoc_node* new_pyassoc(hashtype hsh, PyObject* k, PyObject* v) {
    pyassoc_node* updated = calloc(1, sizeof(pyassoc_node));
    if (updated == NULL)
        return NULL;
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
    {"assoc", (PyCFunction)Node_assoc, METH_KEYWORDS,
     "e"
    },
    {"get", (PyCFunction)Node_get, METH_KEYWORDS,
     "e"
    },
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

static PyObject*
AssocNode(_ctree_NodeObject* self, PyObject *args, PyObject *kwds) {
    PyObject* key = malloc(sizeof(PyObject));
    PyObject* value = malloc(sizeof(PyObject));

    static char *kwlist[] = {"key", "value", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OO", kwlist, key, value))
        return NULL;
    return make_Node(new_pyassoc(PyObject_Hash(key), key, value));
}



static PyMethodDef _ctree_methods[] = {
    {"AssocNode", (PyCFunction)AssocNode, METH_KEYWORDS,
     "e"
    },
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
