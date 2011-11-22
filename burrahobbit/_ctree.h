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

#define SHIFT 5
#define BMAP ((1 << SHIFT) - 1)
#define BRANCH 32

#define relevant(hsh, shift) (hsh >> shift & BMAP)

#define cassoc(this, hsh, shf, n) this->cls->assoc((node*) this, hsh, shf, n)
#define cwithout(this, hsh, shf, k) this->cls->without((node*) this, hsh, shf, k)
#define cget(this, hsh, shf, k) this->cls->get((node*) this, hsh, shf, k)
#define cderef(this) this->cls->deref((node*) this)
#define ccmp(one, other) one->cls->cmp(one->k, other->k)

#define checktype(type, this) (this->cls == type)

#define NODE_HEADER \
    node_cls* cls;  \
    size_t refs;

typedef struct _node node;
typedef struct _set_node set_node;
typedef unsigned int hashtype;


typedef struct {
    node* (*assoc)(node*, hashtype, int, set_node*);
    node* (*without)(node*, hashtype, int, void*);
    node* (*get)(node*, hashtype, int, void*);
    void (*deref)(node*);
    unsigned char (*cmp)(void*, void*);
} node_cls;

struct _node {
    NODE_HEADER
};

typedef struct {
    NODE_HEADER
    
    node* members[BRANCH];
} dispatch_node;

struct _set_node {
    NODE_HEADER
    
    hashtype hsh;
    void* k;
};

typedef struct {
    NODE_HEADER
    
    hashtype hsh;
    int nmembers;
    set_node** members;
} collision_node;

typedef struct {
    NODE_HEADER
    
    hashtype hsh;
    void* k;
    void* v;
} assoc_node;

dispatch_node* new_dispatch(node* members[]);
collision_node* new_collision(int nmembers, set_node** members);
dispatch_node* copy_dispatch(dispatch_node* node);

void incref(node* x);
void decref(node* x);

node* dispatch_two(int shf, set_node* one, set_node* other);

node* dispatch_assoc(node* this, hashtype hsh, int shf, set_node* n);
node* dispatch_without(node* this, hashtype hsh, int shf, void* k);
node* dispatch_get(node* this, hashtype hsh, int shf, void* k);
void dispatch_deref(node* this);

node* collision_assoc(node* this, hashtype hsh, int shf, set_node* n);
node* collision_without(node* this, hashtype hsh, int shf, void* k);
node* collision_get(node* this, hashtype hsh, int shf, void* k);
void collision_deref(node* this);

node* null_assoc(node* this, hashtype hsh, int shf, set_node* n);
node* null_without(node* this, hashtype hsh, int shf, void* k);
node* null_get(node* this, hashtype hsh, int shf, void* k);
void null_deref(node* this);

node* assoc_assoc(node* this, hashtype hsh, int shf, set_node* n);
node* assoc_without(node* this, hashtype hsh, int shf, void* k);
node* assoc_get(node* this, hashtype hsh, int shf, void* k);
/* assoc_deref missing because assoc is not a concrete type. */

node_cls dispatch;
node_cls collision;
node_cls null;
node nullnode;
