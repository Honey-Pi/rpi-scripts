#!/usr/bin/env python3
#Source: https://code.activestate.com/recipes/457667-superglobal-access-global-values-from-every-module/
# Licensed under the PSF License
# See file https://en.wikipedia.org/wiki/Python_Software_Foundation_License
# reworked to run on Python3

import __main__

class SuperGlobal:

    def __getattr__(self, name):
        return __main__.__dict__.get(name, None)
        
    def __setattr__(self, name, value):
        __main__.__dict__[name] = value
        
    def __delattr__(self, name):
        if __main__.__dict__.__contains__(name):
            del  __main__.__dict__[name]

if __name__ == '__main__':
    superglobal1 = SuperGlobal()
    superglobal1.test = 1
    print(superglobal1.test)
    superglobal2 = SuperGlobal()
    print(superglobal2.test)
    del superglobal2.test
    print(superglobal1.test)
    print(superglobal2.test)