************
Installation
************

Prerequisites
=============

Before installing adapya ensure the following:

- Python is available on the platform.

  adapya supports the Python versions 2.7 or 3.6 and higher

  If you have no Python on the system you may install Python
  the latest V3. The Python installer can be downloaded from

  http://www.python.org/download/

-  the **ctypes** package has been ported (usually installed with Python
   on Windows, Linux and Rocket Python on z/OS from version 2.7.12)

   On some platforms this may not be available because of issues with the
   underlying forreign function package that does not support the
   hardware.

-  Sudo rights simplify standard installation (Unix/Linux).

.. note:: Users starting with Python are advised to read the Python
   Tutorial available with function key F1 in the IDLE Python GUI or at
   `<https://docs.python.org/3/tutorial/index.html>`_


Installation with Package Installer
===================================

The Python package installer offers the most convenient method of
installing packages.

From Python package index web site::

  > pip install adapya-base

From zip file (similarly for tar file):

  > pip install adapya-base-1.3.0.zip

Additional z/OS Installation Notes
----------------------------------

As of March 2022, IBM has released for z/OS IBM Open Enterprise for Python V3.10.

Rocket Software had released Python versions 2.7 and 3.6 for z/OS
to run unter Unix System Services.

For installing the adapya-base package under one of those versions perform the following steps:

 - FTP transfer the zip file in binary mode
 - execute pip with the following parameters (in one line)::

     pip install -U --no-index --disable-pip-version-check --no-binary all adapya-base-1.3.0.zip


PYTHONPATH Installation
=======================

Alternatively, the PYTHONPATH installation allows for temporary
package installation by adding the location of the package to the
PYTHONPATH environment variable. As location may serve the directory
where the package was extracted to or the package zip file itself.

When the Python interpreter is started it evaluates the environment
variable **PYTHONPATH** and adds any directories listed to its search
path for modules.

For example, on Windows the following steps would do a PYTHONPATH installation:

- The zip file adapya-base-1.3.0.zip contains a directory adapya/base/\*

- Unzip adapya-base-1.3.0.zip to a convenient location e.g.::

    > C:/ADA/Python

  maintaining the subdirectory structure

- Set/check the following system variables

  On Windows (Win-key + PAUSE-key) open the System Control / select
  Extended Control / button Environment Variable::

    > REM adapya-base Python directory
    > set PYB=C:\ada\python\adapya-base-1.3.0
    > set PYTHONPATH=%PYB%;%PYTHONPATH%


- Open a cmd window and go to Adabas demo files directory::

    > cd %PYB%/adapya/base

- Check successful installation with dump.py to dump contents of file::

    > python dump.py -f future.py


Additional Windows Installation Notes
=====================================

Simplifying Execution of Python Scripts
---------------------------------------

The option to register Python files can be selected during the Python
installation. This binds certain Python file types and associations to the
Python executable being installed (or to the Python launcher py.exe).

For example for .py the following may have been set::

    ftype Python.File="C:\Windows\py.exe" "%L" %*
    ftype Python.ArchiveFile="C:\Windows\py.exe" "%L" %*
    ftype Python.CompiledFile="C:\Windows\py.exe" "%L" %*
    ftype Python.NoConArchiveFile="C:\Windows\pyw.exe" "%L" %*
    ftype Python.NoConFile="C:\Windows\pyw.exe" "%L" %*

    assoc .py=Python.File
    assoc .pyc=Python.CompiledFile
    assoc .pyo=Python.CompiledFile
    assoc .pyw=Python.NoConFile
    assoc .pyz=Python.ArchiveFile
    assoc .pyzw=Python.NoConArchiveFile

If you add **.py** and the corresponding compiled extensions
to the PATHEXT variable it is possible to run a script without
writing the extension ::

    set PATHEXT=.py;.pyc;.pyo;%PATHEXT%
    dump -h

rather than typing::

    dump.py -h

In Windows 10 it may be necessary to switch the "App Installer" for python.exe
or python3.exe to avoid Windows suggesting to install Python from the app store.
The switch is found on the "App execution aliases" page in Windows settings.


Unix/Linux PYTHONPATH Installation
==================================

The PYTHONPATH environment variable defines an extra search path for
python modules. If the path to the Adabas Python directory is added to
the variable it is included in the search::

    cd /FS/disk01/pya            # root directory
    tar xf adapya-base-1.3.0.tar # unpack to adapya-base-1.3.0
    setenv PYA "/FS/disk01/pya"
    setenv PYTHONPATH $PYA':'$PYTHONPATH # add PYA to PYTHONPATH
    cd $PYA/adapya/base # go to directory
    python dump.py -h


.. note::
   If your local internet is protected by a http proxy you may need to set
   the HTTP\_PROXY environment variable before running easy\_install (CYGWIN)::

       SET HTTP_PROXY=http://<httpprox.your-local.net>:<httpprox-port>

   Not setting it may result in timing out operations.

