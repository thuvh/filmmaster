from django.utils import unittest
from django.utils.importlib import import_module

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()

    for ver in ("1.0", "1.1", ):
        module = import_module('film20.api.api_%s.tests' % ver.replace(".", "_"))
        s.addTests(loader.loadTestsFromModule(module))
    return s
    
