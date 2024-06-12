#!/usr/bin/env python
# -*- coding: "utf-8" -*-

from setuptools import setup
import unittest


def test():
    loader = unittest.TestLoader()
    suite = loader.discover("test")
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if not result.wasSuccessful():
        raise Exception("Test Failed: Aborting install")


#test()

setup(
        name='bla',
        version='0.1.1',
        author='Julien Tayon',
        author_email='julien@tayon.net',
        packages=['bla', ],
        install_requires=["ldap3", "tempdir", "PyYAML", "ipython",
            "pygments-ldif"],
        keywords=['cli', 'ldap', ],
        url='http://bla.readthedocs.org/',
        scripts=["scripts/bla", "scripts/lhl"],
        license=open('LICENSE.txt').read(),
        description='Building a convenient CLI on top of LDAP3',
        classifiers=(
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Python Software Foundation License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          ),
)
print("dont forget to install gssapi to use kerberos support")
