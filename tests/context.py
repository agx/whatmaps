# this context.py should be included by all tests
# idea from http://kennethreitz.com/repository-structure-and-python.html
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import shutil
import sys
import tempfile

import whatmaps

sys.path.insert(0, os.path.abspath('..'))

# the top or root dir of the git-buildpackage source tree to be used by tests
projectdir = os.path.dirname(os.path.dirname(os.path.abspath(whatmaps.__file__)))

_chdir_backup = None
_tmpdirs = []


def chdir(dir):
    global _chdir_backup
    if not _chdir_backup:
        _chdir_backup = os.path.abspath(os.curdir)
    os.chdir(str(dir))


def new_tmpdir(name):
    global _tmpdirs
    prefix = 'whatmaps_%s_' % name
    tmpdir = TmpDir(prefix)
    _tmpdirs.append(tmpdir)
    return tmpdir


def teardown():
    if _chdir_backup:
        os.chdir(_chdir_backup)
    for tmpdir in _tmpdirs:
        tmpdir.rmdir()
    del _tmpdirs[:]


class TmpDir(object):

    def __init__(self, suffix='', prefix='tmp'):
        self.path = tempfile.mkdtemp(suffix=suffix, prefix=prefix)

    def rmdir(self):
        if self.path and not os.getenv("WHATMAPS_TESTS_NOCLEAN"):
            shutil.rmtree(self.path)
            self.path = None

    def __repr__(self):
        return self.path

    def join(self, *args):
        return os.path.join(self.path, *args)
