#!/usr/bin/env python
# -*- coding: us-ascii -*-

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

import sys

try:
    # If we got setuptools, use it so we get the nice develop cmd.
    from setuptools import setup
except:
    # Doesn't matter if we don't have it though.
    from distutils.core import setup


VERSION = '0.1.0'

extra = {}
if sys.version_info >= (3, 0):
    extra['use_2to3'] = True

setup(
    name='burrahobbit',
    version=VERSION,
    description='Persistent data-structures in Python.',
    author='Florian Mayer',
    author_email='florian.mayer@bitsrc.org',
    url='https://github.com/segfaulthunter/burrahobbit',
    keywords='persistent datastructures',
    license='MIT',
    zip_safe=True,
    packages=['burrahobbit', 'burrahobbit.test'],
    **extra
)
