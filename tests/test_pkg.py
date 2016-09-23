# vim: set fileencoding=utf-8 :
# (C) 2014 Guido Günther <agx@sigxcpu.org>
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
"""Test L{whatmaps.process} config"""

import unittest
from mock import patch

from whatmaps.pkg import Pkg, PkgError

from . import context


class TestPkg(unittest.TestCase):
    def setUp(self):
        self.tmpdir = context.new_tmpdir(__name__)

    def test_abstract(self):
        """Check abstract method signatures"""
        self.assertIsNone(Pkg.type)
        self.assertIsNone(Pkg.services)

    def test_repr(self):
        p = Pkg('apckage')
        self.assertEqual(str(p), "<None Pkg object name:'apckage'>")

    def test_list_contents(self):
        with patch('subprocess.Popen') as mock:
            p = Pkg('doesnotmatter')
            p._list_contents = '/does/not/matter'
            PopenMock = mock.return_value
            PopenMock.communicate.return_value = [
                b'/package/content',
                b'/more/package/content',
            ]
            PopenMock.returncode = 0
            result = p._get_contents()
            self.assertIn('/package/content', result)
            self.assertNotIn('/more/package/content', result)

            # We want to check that we don't invoke Popen on
            # a second call so let it fail
            PopenMock.returncode = 1

            result = p._get_contents()
            self.assertIn('/package/content', result)
            self.assertNotIn('/more/package/content', result)

    def test_shared_objects(self):
        """Test that we properly match shared objects"""
        with patch('subprocess.Popen') as mock:
            p = Pkg('doesnotmatter')
            p._list_contents = '/does/not/matter'
            PopenMock = mock.return_value
            PopenMock.communicate.return_value = [b'\n'.join([
                b'/lib/foo.so.1',
                b'/lib/bar.so',
                b'/not/a/shared/object',
                b'/not/a/shared/object.soeither',
            ])]
            PopenMock.returncode = 0
            result = p.shared_objects
            self.assertIn('/lib/foo.so.1', result)
            self.assertIn('/lib/bar.so', result)
            self.assertNotIn('/not/a/shred/object', result)
            self.assertNotIn('/not/a/shred/object.soeither', result)

            # We want to check that we don't invoke Popen on
            # a second call so let it fail.
            PopenMock.returncode = 1
            result = p._get_contents()
            self.assertIn('/lib/foo.so.1', result)
            self.assertNotIn('/not/a/shred/object', result)

    def test_shared_object_error(self):
        """Test that we raise PkgError"""
        with patch('subprocess.Popen') as mock:
            p = Pkg('doesnotmatter')
            p._list_contents = '/does/not/matter'
            PopenMock = mock.return_value
            PopenMock.communicate.return_value = ['']
            PopenMock.returncode = 1
            try:
                p.shared_objects
                self.fail("PkgError exception not raised")
            except PkgError:
                pass
            except Exception as e:
                self.fail("Raised '%s is not PkgError" % e)

    def tearDown(self):
        context.teardown()
