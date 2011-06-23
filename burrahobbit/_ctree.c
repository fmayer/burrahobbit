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
#include <string.h>
#include "_ctree.h"

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
    dispatch_node* nd = copy_dispatch(self);
    
    if (nd->members[rel]) {
        nd->members[rel] = cassoc(
            nd->members[rel], hsh, shf + SHIFT, n
        );
    } else {
        nd->members[rel] = (node*) n;
    }
    return (node*) nd;
}

node* dispatch_without(node* this, hashtype hsh, int shf, void* k) {
    hashtype rel = relevant(hsh, shf);
    
    dispatch_node* self = (dispatch_node*) this;
    dispatch_node* n = copy_dispatch(self);
    n->members[rel] = n->members[rel]->cls->without(
        n->members[rel], hsh, shf + SHIFT, k
    );
    
    unsigned int i;
    for (i=0; i < BRANCH; ++i) {
        if (n->members[i] != NULL) {
            return (node*)n;
        }
    }
    free(n);
    return NULL;
}

node* dispatch_get(node* this, hashtype hsh, int shf, void* k) {
    hashtype rel = relevant(hsh, shf);    
    dispatch_node* self = (dispatch_node*) this;

    if (!self->members[rel]) {
        return NULL;
    }
    return cget(self->members[rel], hsh, shf + SHIFT, k);
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
        if (ccmp(n, self->members[i])) {
            newmembers = calloc(self->nmembers, sizeof(void));
            memcpy(self->members, newmembers, self->nmembers);
            newmembers[i] = n;
            return (node*) new_collision(self->nmembers, newmembers);
        }
    }
    
    newmembers = calloc(self->nmembers + 1, sizeof(void));
    memcpy(self->members, newmembers, self->nmembers);
    newmembers[self->nmembers + 1] = n;
    return (node*) new_collision(self->nmembers + 1, newmembers);
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
            return (node*) new_collision(self->nmembers - 1, newmembers);
        }
    }
    return this;
}

node* collision_get(node* this, hashtype hsh, int shf, void* k) {
    collision_node* self = (collision_node*) this;
    
    int i;
    for (i = 0; i < self->nmembers; ++i) {
        if (self->members[i]->cls->cmp(self->members[i]->k, k)) {
	  return (node*) self->members[i];
        }
    }
    
    return NULL;
}

void collision_deref(node* this) {
    collision_node* self = (collision_node*) this;
    
    unsigned int i;
    for (i=0; i < self->nmembers; ++i) {
        if (self->members[i] != NULL) {
            decref((node*) self->members[i]);
        }
    }
    
    free(self);
}


node* null_assoc(node* this, hashtype hsh, int shf, set_node* n) {
    return (node*) n;
}

node* null_without(node* this, hashtype hsh, int shf, void* k) {
    return (node*) this;
}

node* null_get(node* this, hashtype hsh, int shf, void* k) {
    return NULL;
}

void null_deref(node* this) {
}

node* assoc_assoc(node* this, hashtype hsh, int shf, set_node* n) {
    assoc_node* self = (assoc_node*) this;
    if (self->hsh == hsh && ccmp(self, n)) {
        return (node*) n;
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


node_cls dispatch =
    { dispatch_assoc, dispatch_without, dispatch_get, dispatch_deref, NULL };
node_cls collision =
    { collision_assoc, collision_without, collision_get, collision_deref, NULL };
node_cls null = { null_assoc, null_without, null_get, null_deref, NULL };

node nullnode = { &null, 1 };

dispatch_node* new_dispatch(node* members[]) {
    dispatch_node* updated = calloc(1, sizeof(dispatch_node));
    if (updated == NULL)
        return NULL;
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
    return updated;
}

dispatch_node* copy_dispatch(dispatch_node* node) {
    dispatch_node* n = empty_dispatch();
    
    unsigned int i;
    for (i=0; i < BRANCH; ++i) {
        n->members[i] = node->members[i];
    }
    return n;
}

node* dispatch_two(
    int shf, set_node* one, set_node* other
    ) {
    node* nd = (node*) empty_dispatch();
    node* nnd;
    
    nnd = cassoc(nd, one->hsh, shf, one);
    decref((node*) nd);
    nd = cassoc(nnd, other->hsh, shf, other);
    decref((node*) nnd);
    return nd;
}

collision_node* new_collision(int nmembers, set_node** members) {
    unsigned int i;
    
    for (i = 0; i < nmembers; ++i) {
        incref((node*) members[i]);
    }
    collision_node* updated = calloc(1, sizeof(collision_node));
    if (updated != NULL) {
        updated->cls = &collision;
	updated->refs = 1;
	updated->nmembers = nmembers;
	updated->members = members;
	updated->hsh = members[0]->hsh;
    }
    return updated;
}
