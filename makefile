#
#   make file
#   %make% VRL=0.9.4 WC=NO all
#   %make% VRL=0.9.4 WC=YES all    (take from working copy not from committed version in SVN)
#

#.SILENT: clean env nose-cover test-cover qa test doc release upload
.PHONY: clean release docs

#VERSION=2.7
#PYPI=http://pypi.python.org/simple
#DIST_DIR=dist

PYTHON=python
#SED=C:\BAT\UnxUtils\upd\sed
MED=$(PYUSP)\massedit.py    # user's appdata sitepackages directory
THISYEAR=2023
SUBP=base           # subpackage
PACK=adapya-$(SUBP) # adapya package
MAKDIR=$(USERPROFILE)\adas\temp\apy


#EASY_INSTALL=env/bin/easy_install-$(VERSION)
#PYTEST=env/bin/py.test-$(VERSION)
#NOSE=env/bin/nosetests-$(VERSION

APYURL=http://redsvngis.eur.ad.sag/ADA/adapy
APYWC=$(USERPROFILE)\adas\adapy
GITDIR=$(USERPROFILE)\adas\git

#SVN="C:\Program Files\TortoiseSVN\bin\svn.exe"
#SVNVERSION="C:\Program Files\TortoiseSVN\bin\svnversion.exe"
SVN="svn"
SVNVERSION="svnversion"

# VRL version.release.level (e.g. 1.2.3) must be set from outside
!IF "$(VRL)" == ""
!ERROR Input define VRL for makefile missing
!ENDIF


# WC=YES take working copy otherwise from repository (new members must be committed in SVN)
!IF "$(WC)" == "YES"
APYURL=$(APYWC)
!ENDIF


all: clean release docs

info:
    $(SVN) info  . $(APYURL)/trunk
    $(SVNVERSION)


clean:
    cd $(MAKDIR)
    -rd $(PACK)-$(VRL) /s /q
    -del $(PACK)-$(VRL).*

#        find src/ -type d -name __pycache__ | xargs rm -rf
#        find src/ -name '*.py[co]' -delete
#        find src/ -name '*.so' -delete
#        rm -rf dist/ build/ doc/_build/ MANIFEST src/*.egg-info .cache .coverage

release:
    cd $(MAKDIR)
    $(SVN) export $(APYURL)/trunk/adapya-base $(PACK)-$(VRL) --depth=files
    $(SVN) export $(APYURL)/trunk/adapya $(PACK)-$(VRL)/adapya --depth=files
    $(SVN) export $(APYURL)/trunk/adapya/base $(PACK)-$(VRL)/adapya/base
    $(SVN) export $(APYURL)/trunk/adapya-base/doc/source $(PACK)-$(VRL)/adapya/base/doc
    cd $(PACK)-$(VRL)
    rem call prune.bat
    rem del prune.bat
    rem $(SED) -i "s/v.r.l/$(VRL)/" setup.py adapya\base\*.py adapya\base\doc\*.py adapya\base\doc\*.rst
    rem $(SED) -i "s/ThisYear/$(THISYEAR)/" adapya\base\*.py  adapya\base\doc\*.py adapya\base\doc\*.rst
    rem python $(MED) -w -e "re.sub('v.r.l', '$(VRL)', line)"          setup.py adapya\base\*.py adapya\base\doc\*.py adapya\base\doc\*.rst
    python $(MED) -w -e "re.sub('v.r.l', '$(VRL)', line)"          setup.py
    python $(MED) -v -w -e "re.sub('v.r.l', '$(VRL)', line)"       adapya\base\*.py
    python $(MED) -w -e "re.sub('v.r.l', '$(VRL)', line)"          adapya\base\doc\*.py
    python $(MED) -w -e "re.sub('v.r.l', '$(VRL)', line)"          adapya\base\doc\*.rst
    rem
    python $(MED) -w -e "re.sub('ThisYear', '$(THISYEAR)', line)"  adapya\base\*.py
    python $(MED) -w -e "re.sub('ThisYear', '$(THISYEAR)', line)"  adapya\base\doc\*.py
    python $(MED) -w -e "re.sub('ThisYear', '$(THISYEAR)', line)"  adapya\base\doc\*.rst
    rem --- delete  GIT directory mirror but leave hidden files (.git)
    del /A-H /q $(GITDIR)\$(PACK)\*.*
    del /S /q $(GITDIR)\$(PACK)\adapya
    xcopy /s /y /q * $(GITDIR)\$(PACK)
    cd $(GITDIR)\$(PACK)
    cd $(MAKDIR)/$(PACK)-$(VRL)
    rem ---
    $(PYTHON) setup.py sdist --formats=gztar,zip
    cd ..
    xcopy $(PACK)-$(VRL)\dist\* ..\apy

tag:
    $(SVN) copy $(APYURL)/trunk/adapya-base \
         $(APYURL)/tags/adapya-base-$(VRL)\
         -m "Tagging the $(VRL) release of the 'adapya-base' project."

upload:
    cd $(MAKDIR)
    xcopy /D /Y $(PACK)-$(VRL).* V:\tools\Python\adapya
    cd C:$(PACK)-$(VRL)/adapya/$(SUBP)
    xcopy /S /D /Y doc\_build V:\tools\Python\adapya\doc\$(SUBP)

# XCOPY /D copies files only newer than target /S include subdir /Y no prompt for existing file

docs:
    cd $(MAKDIR)/$(PACK)-$(VRL)/adapya/base
    sphinx-build -a doc/ doc/_build/
    rem # copy .nojekyll file to docs dir: this will disable GIGHUB's own pages formatting
    xcopy /D $(APYWC)\trunk\*.nojekyll $(GITDIR)\$(PACK)\docs
    xcopy /s /y /q doc\_build\* $(GITDIR)\$(PACK)\docs

