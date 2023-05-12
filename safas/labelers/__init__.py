#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import modules into global namespace of filters
"""

import pkgutil
from importlib import import_module

__all__ = []
loaded = []

for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
    
    loaded.append(module_name)

globals()["AVAILABLE_LABELERS"] = loaded