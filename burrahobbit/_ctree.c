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
/* This is currently not used as it is only C99. Kept here for reference */
#define call(obj, fun, ...) ((node_cls*) obj->cls)->fun(obj, __VA_ARGS__)

typedef struct _node node;
typedef struct _key key;	
typedef int hashtype;

struct _key {
    unsigned char (*cmp)(key*, key*);
    void* value;
};

typedef struct {
    node* (*assoc)(node*, hashtype, int, key*, node*);
    node* (*without)(node*, hashtype, int, key*);
    node* (*get)(node*, hashtype, int, key*);
    void (*deref)(node*);
} node_cls;

struct _node {
    node_cls* cls;
    unsigned int refs;
};

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    void* members[BRANCH];
} dispatch_node;

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    unsigned int hsh;
    key* k;
} set_node;

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    unsigned int hsh;
    int nmembers;
    set_node** members;
} collision_node;

typedef struct {
    node_cls* cls;
    unsigned int refs;
    
    unsigned int hsh;
    key* k;
    void* v;
} assoc_node;


dispatch_node* new_dispatch(void* members[]);
collision_node* new_collision(int nmembers, set_node** members);
assoc_node* new_assoc(unsigned int hsh, key* k, void* v);

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

void* dispatch_assoc(void* this, hashtype hsh, int shf, key* k, void* n) {
    hashtype rel = relevant(hsh, shf);
    
    dispatch_node* self = (dispatch_node*) this;
    node** newmembers = calloc(BRANCH, sizeof(node*));
    
    if (self->members[rel]) {
        newmembers[rel] = (void*) ((node_cls*) self->members[rel])->assoc(
            newmembers[rel], hsh, shf + SHIFT, k, n
        );
    } else {
        newmembers[rel] = n;
    }
    
    void* r = new_dispatch(newmembers);
    free(newmembers);
    return r;
}

void* dispatch_without(void* this, hashtype hsh, int shf, key* k) {
    hashtype rel = relevant(hsh, shf);
    
    dispatch_node* self = (dispatch_node*) this;
    void* newmembers[BRANCH];
    
    if (!self->members[rel]) {
        return this;
    }
    newmembers[rel] = ((node_cls*) self->members[rel])->without(
        newmembers[rel], hsh, shf + SHIFT, k
    );
    
    return new_dispatch(newmembers);
}

void* dispatch_get(void* this, hashtype hsh, int shf, key* k) {
    hashtype rel = relevant(hsh, shf);
    
    dispatch_node* self = (dispatch_node*) this;
    void* newmembers[BRANCH];
    
    if (!self->members[rel]) {
        return NULL;
    }
    return ((node_cls*) self->members[rel])->get(
        newmembers[rel], hsh, shf + SHIFT, k
    );
}

void dispatch_deref(void* this) {
    dispatch_node* self = (dispatch_node*) this;
    
    unsigned int i;
    for (i=0; i < BRANCH; ++i) {
        if (self->members[i] != NULL) {
            decref(self->members[i]);
        }
    }
    
    free(self);
}

void* collision_assoc(void* this, hashtype hsh, int shf, key* k, set_node* n) {
    collision_node* self = (collision_node*) this;
    set_node** newmembers;
    
    int i;
    for (i = 0; i < self->nmembers; ++i) {
        if (k->cmp(k, self->members[i]->k)) {
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

void* collision_without(void* this, hashtype hsh, int shf, key* k) {
    collision_node* self = (collision_node*) this;
    
    set_node** newmembers;
    
    int i, j;
    for (i = 0; i < self->nmembers; ++i) {
        if (k->cmp(k, self->members[i]->k)) {
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

void* collision_get(void* this, hashtype hsh, int shf, key* k) {
    collision_node* self = (collision_node*) this;
    set_node** newmembers;
    
    int i;
    for (i = 0; i < self->nmembers; ++i) {
        if (k->cmp(k, self->members[i]->k)) {
            return self->members[i];
        }
    }
    
    return NULL;
}

void collision_deref(void* this) {
    collision_node* self = (collision_node*) this;
    
    unsigned int i;
    for (i=0; i < self->nmembers; ++i) {
        if (self->members[i] != NULL) {
            decref(self->members[i]);
        }
    }
    
    free(self);
}


void* null_assoc(void* this, hashtype hsh, int shf, key* k, set_node* n) {
    return n;
}

void* null_without(void* this, hashtype hsh, int shf, key* k) {
    return this;
}

void* null_get(void* this, hashtype hsh, int shf, key* k) {
    return NULL;
}

void* null_deref(void* this) {
}

void* assoc_assoc(void* this, hashtype hsh, int shf, key* k, set_node* n) {
    assoc_node* self = (assoc_node*) this;
    if (self->hsh == hsh && self->k->cmp(self->k, k)) {
        return n;
    } else {
        return dispatch_two(shf, ((set_node*) this), n);
    }
}

void* assoc_without(void* this, hashtype hsh, int shf, key* k) {
    assoc_node* self = (assoc_node*) this;
    if (self->hsh == hsh && self->k->cmp(self->k, k)) {
        return NULL;
    } else {
        return this;
    }
}

void* assoc_get(void* this, hashtype hsh, int shf, key* k) {
    assoc_node* self = (assoc_node*) this;
    if (self->hsh == hsh && self->k->cmp(self->k, k)) {
        return this;
    }
    return NULL;
}

void* assoc_deref(void* this) {
}

const node_cls dispatch =
    { dispatch_assoc, dispatch_without, dispatch_get, dispatch_deref };
const node_cls collision =
    { collision_assoc, collision_without, collision_get, collision_deref };
const node_cls assoc = { assoc_assoc, assoc_without, assoc_get, assoc_deref };
const node_cls null = { null_assoc, null_without, null_get, null_deref };

const node nullnode = { &null, 1 };

dispatch_node* new_dispatch(void* members[]) {
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
    
    nnd = dispatch_assoc(nd, one->hsh, shf, one->k, one);
    decref(nd);
    nd = dispatch_assoc(nnd, other->hsh, shf, other->k, other);
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

assoc_node* new_assoc(unsigned int hsh, key* k, void* v) {
    assoc_node* updated = calloc(1, sizeof(assoc_node));
    updated->cls = &assoc;
    updated->refs = 1;
    updated->k = k;
    updated->v = v;
    updated->hsh = hsh;
    return updated;
}

/* For testing purposes only. */

typedef struct {
    unsigned char (*cmp)(void*, void*);
    char* value;
    size_t length;
} ckey;

unsigned char cmp_ckey(void* vone, void* vother) {
    if (vone == vother) {
        return 1;
    }
    ckey* one = (ckey*) vone;
    ckey* other = (ckey*) vother;
    if (one->length != other->length) {
        return 0;
    }
    
    return !memcmp(one->value, other->value, one->length);
}

unsigned long ocaml_hash(unsigned char *str, unsigned int len) {
    unsigned long hash = 0;
    unsigned int i;
    for (i=0; i<len; i++) {
        hash = hash*19 + str[i];
    }
    return hash;
}

unsigned int hash_ckey(ckey* key) {
    return ocaml_hash(key->value, key->length);
}

ckey* new_ckey(char* data, size_t n) {
    ckey* new = malloc(sizeof(ckey));
    new->cmp = cmp_ckey;
    new->value = data;
    new->length = n;
    return new;
}

int main(char** argv, size_t argc) {
    key* k = new_ckey("Hello", 6);
    key* k2 = new_ckey("Hello", 6);
    key* k3 = new_ckey("World", 6);
    assert(k->cmp(k, k));
    assert(k->cmp(k, k2));
    assert(!k->cmp(k, k3));
    assert(!k->cmp(k2, k3));
    assoc_node* a = new_assoc(hash_ckey(k), k, "World");
    incref(a); /* We are holding a ref outside of a map. */
    node* m = nullnode.cls->assoc(&nullnode, a->hsh, 0, a->k, a);
    assoc_node* b = m->cls->get(m, a->hsh, 0, a->k);
    printf("%s ", b->k->value);
    printf("%s!\n", b->v);
    assert(m->cls->get(m, hash_ckey(k3), 0, k3) == NULL);
    assert(m->cls->get(m, hash_ckey(k2), 0, k2) == a);
    assert(m == a);
    assoc_node* a2 = new_assoc(hash_ckey(k3), k3, "Eggs");
    incref(a2); /* We are holding a ref outside of a map. */
    node* m2 = m->cls->assoc(m, a2->hsh, 0, a2->k, a2);
    incref(a2);
    return 0;
}
