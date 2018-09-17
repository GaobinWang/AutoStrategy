# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 16:59:22 2018

@author: pc
"""

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
from Cython.Build import cythonize

ext_modules = cythonize(
	[
    Extension('AutoStrategy', ['AutoStrategy.py']),
    Extension("AutomatedCTAGenerator.*",  ["AutomatedCTAGenerator/*.py"]),
    Extension("Backtest.*",  ["Backtest/*.py"]),
    Extension("Feature.*",  ["Feature/*.py"]),
    Extension("IOdata.*",  ["IOdata/*.py"]),
    Extension("TradingSystem.*",  ["TradingSystem/*.py"]),
    Extension("PositionSizing.*",  ["PositionSizing/*.py"]),
    Extension("LoginAccount.*",  ["LoginAccount/*.py"])
    #   ... all your modules that need be compiled ...
    ],
    build_dir="build",
    compiler_directives=dict(
    always_allow_keywords=True
    ))


#ext_modules =	[
#    Extension('AutoStrategy', ['AutoStrategy.py']),
#    Extension("AutomatedCTAGenerator.*",  ["AutomatedCTAGenerator/*.py"]),
#    Extension("Backtest.*",  ["Backtest/*.py"]),
#    Extension("Feature.*",  ["Feature/*.py"]),
#    Extension("IOdata.*",  ["IOdata/*.py"]),
#    Extension("TradingSystem.*",  ["TradingSystem/*.py"]),
#    Extension("PositionSizing.*",  ["PositionSizing/*.py"])
#    #   ... all your modules that need be compiled ...
#    ]
    
setup(
    name = 'AutoStrategy',
    cmdclass = {'build_ext': build_ext},
    ext_modules = ext_modules,
    packages=["AutoStrategy"]
)
