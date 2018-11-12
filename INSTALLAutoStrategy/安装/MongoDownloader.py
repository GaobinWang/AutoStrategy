# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 18:15:58 2018

@author: maozh
"""

import wget
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

print('Beginning file download with MongoDB')

url = 'https://fastdl.mongodb.org/win32/mongodb-win32-x86_64-2008plus-ssl-4.0.4-signed.msi'  
wget.download(url, 'C:\\tools\\mongodb-win32-x86_64-2008plus-ssl-4.0.4-signed.msi')  