#!/bin/sh
#
# This script merely copies __init__.py and patches it to make it easier to
# keep in sync with upstream.

CWD=`pwd`
cd `dirname $0`
cp __init__.py facebook.py
for patch in `ls *.patch`; do
    patch facebook.py < $patch
done;
rm facebook.py.orig
mv facebook.py ../fbuploader/
cd $CWD
