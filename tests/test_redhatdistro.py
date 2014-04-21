# vim: set fileencoding=utf-8 :
# (C) 2014 Guido Günther <agx@sigxcpu.org>
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""Test L{whatmaps.process} config"""

import unittest
from mock import patch

from whatmaps.redhatdistro import RedHatDistro
from whatmaps.rpmpkg import RpmPkg

class TestRedHatDistro(unittest.TestCase):
    def test_vars(self):
        """Check RedHat distro vars"""
        self.assertEqual(RedHatDistro.id, None)
        self.assertIsNotNone(RedHatDistro._pkg_services)
        self.assertIsNotNone(RedHatDistro._pkg_service_blacklist)
        self.assertIsNotNone(RedHatDistro.service_blacklist)
        self.assertEqual(RedHatDistro.restart_service_cmd('aservice'),
                         ['service', 'aservice', 'restart'])
        self.assertFalse(RedHatDistro.has_apt())

    def test_pkg_by_file(self):
        with patch('subprocess.Popen') as mock:
            PopenMock = mock.return_value
            PopenMock.returncode = 0
            PopenMock.communicate.return_value = ['apackage']

            pkg = RedHatDistro.pkg_by_file('afile')
            self.assertIsInstance(pkg, RpmPkg)
            self.assertEqual(pkg.name, 'apackage')
            PopenMock.communicate.assert_called_once_with()
            mock.assert_called_once_with(['rpm', '-qf', 'afile'],
                                         stderr=-1, stdout=-1)

    def test_pkg_by_file_failure(self):
        """Test if None is returned on subcommand erros"""
        with patch('subprocess.Popen') as mock:
            PopenMock = mock.return_value
            PopenMock.returncode = 1
            PopenMock.communicate.return_value = ['apackage']

            pkg = RedHatDistro.pkg_by_file('afile')
            self.assertIsNone(pkg)
            PopenMock.communicate.assert_called_once_with()
            mock.assert_called_once_with(['rpm', '-qf', 'afile'],
                                         stderr=-1, stdout=-1)
