from __future__ import print_function          # PY3
# requires Python V2.7 or higher
#!/usr/bin/env python

import os,sys

try:
    from setuptools import setup
except:
    from distutils.core import setup  # noqa

pver=sys.version[0]
prel=sys.version[2]

print('Active runtime:',sys.version, pver, prel)

# check that ctypes is there (there are some platforms where this is missing)
#try:
#    import ctypes
#except:
#    print ('Installation of adabas requires package ctypes installed')
#    sys.exit(1)

#dfiles=[]
#ppacks=[]

# must tell in detail what to install: package (.py) or data_files (non .py file)
# we do this by walking the installation directory

#for root, dirs, files in os.walk(''):
#    root=os.path.normpath(root) # changes './adabas' or '.\adabas' to adabas
#    if root.startswith('adabas'):
#        dfile=[]
#        for file in files:
#            if file.endswith('.py'): # skip .py files
#                if file == '__init__.py':
#                    ppacks.append(root)
#                continue
#            dfile.append(os.path.join(root,file))
#        if len(dfile)>0:
#            dfiles.append([os.path.join('Lib/site-packages',root),dfile])

# print( dfiles)

extra = {}
#extra['install_requires'] = ['xxx']

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(  name='adapya-base',
    version='1.0.4',
    author='mmueller',
    author_email='mm@softwareag.com',
    description='adapya-base - base package for adapya',
    license='Apache License 2.0',
    url='http://tech.forums.softwareag.com/viewforum.php?f=171&C=11',
    classifiers = [
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Database',
        ],
    keywords='adabas database softwareag',
    long_description=README,
    # data_files=dfiles,
    scripts = ['adapya/base/scripts/ftpz.py','adapya/base/scripts/getfilez.py',
        'adapya/base/scripts/smfreaderz.py'],
    packages=['adapya','adapya.base','adapya.base.scripts'],
    #package_dir={ '':'../..'
    #            # 'adapya-base': '../../adapya/base',
    #            # 'adapya-base/scripts': '../../adapya/base/scripts',
    #            },  # new location : source location
    namespace_packages=['adapya'],
    zip_safe=False,
    #extras_require={
    #    'dev': [ 'coverage', 'nose', 'pytest', 'pytest-pep8', 'pytest-cov']
    #    },

    platforms='any',
    **extra
)
