# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 10:35:04 2018

@author: maozh
"""

import sys
import shutil

if sys.version[0:3]=='3.6':
    shutil.copytree('C:\\AutoStrategy\\AutoStrategyRelease36', 'C:\\tools\\Anaconda3\\Lib\\site-packages\\AutoStrategy')
    print (1)
    
elif sys.version[0:3]=='3.5':
    shutil.copytree('C:\\AutoStrategy\\AutoStrategyRelease35', 'C:\\tools\\Anaconda3\\Lib\\site-packages\\AutoStrategy')
    print (1)
else:
    print ('failed to copy AutoStrategy')