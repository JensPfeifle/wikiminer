#!/usr/bin/env python3

"""
unlinks (deletes) all files that are not listed in ./dont-delete.txt
"""

import os
import time
no_remove = set()
with open('./dont-delete.txt') as f:
     for line in f:
         no_remove.add(line.strip())
         no_remove.add('dont-delete.txt')
         no_remove.add('rm_except.py')

for root, dirs, files in os.walk('.'):
        relpath = os.path.relpath(root)
        print(relpath)
        for f in files:
            if relpath == '.':
                filepath = f
            else:
                filepath = os.path.join(relpath, f)
            if filepath not in no_remove:
                print('unlink:' + filepath ) 
                #os.unlink(filepath)
            else:
                print("\n Skipping {} \n".format(filepath))
            time.sleep(0.025)

