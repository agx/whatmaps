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
from unittest.mock import patch

try:
    import apt_pkg  # noqa: F401
    have_apt_pkg = True
except ImportError:
    have_apt_pkg = False

try:
    import lsb_release  # noqa: F401
    have_lsb_release = True
except ImportError:
    have_lsb_release = False

from whatmaps.debiandistro import DebianDistro
from whatmaps.debianpkg import DebianPkg


class TestDebianDistro(unittest.TestCase):
    def test_vars(self):
        """Check Debian distro vars"""
        self.assertEqual(DebianDistro.id, 'Debian')
        self.assertIsNotNone(DebianDistro._pkg_services)
        self.assertIsNotNone(DebianDistro._pkg_service_blacklist)
        self.assertIsNotNone(DebianDistro.service_blacklist)
        self.assertEqual(DebianDistro.restart_service_cmd('aservice'),
                         ['invoke-rc.d', 'aservice', 'restart'])
        self.assertTrue(DebianDistro.has_apt())

    def test_pkg_by_file(self):
        with patch('subprocess.Popen') as mock:
            PopenMock = mock.return_value
            PopenMock.returncode = 0
            PopenMock.communicate.return_value = ['apackage']

            pkg = DebianDistro.pkg_by_file('afile')
            self.assertIsInstance(pkg, DebianPkg)
            self.assertEqual(pkg.name, 'apackage')
            PopenMock.communicate.assert_called_once_with()
            mock.assert_called_once_with(['dpkg-query', '-S', 'afile'],
                                         stderr=-1, stdout=-1)

    def test_pkg_by_file_failure(self):
        """Test if None is returned on subcommand erros"""
        with patch('subprocess.Popen') as mock:
            PopenMock = mock.return_value
            PopenMock.returncode = 1
            PopenMock.communicate.return_value = ['apackage']

            pkg = DebianDistro.pkg_by_file('afile')
            self.assertIsNone(pkg)
            PopenMock.communicate.assert_called_once_with()
            mock.assert_called_once_with(['dpkg-query', '-S', 'afile'],
                                         stderr=-1, stdout=-1)

    def test_read_apt_pipeline(self):
        """Test our interaction with the apt pipeline"""
        class AptPipelineMock(object):
            def __init__(self):
                self.iter = self.lines()

            def lines(self):
                for line in ['VERSION 2', 'Whatmaps::Enable-Restart=1', '\n']:
                    yield line

            def readlines(self):
                return ['pkg1 0.0 c 1.0 **CONFIGURE**',
                        'pkg2 - c 1.0 **CONFIGURE**',
                        '']

            def readline(self):
                return next(self.iter)

        with patch('sys.stdin', new_callable=AptPipelineMock):
            pkgs = DebianDistro.read_apt_pipeline()
            self.assertEqual(len(pkgs), 1)
            self.assertIn('pkg1', pkgs)
            self.assertTrue(pkgs['pkg1'].name, 'pkg1')

    @patch('apt_pkg.init')
    @patch('apt_pkg.Acquire')
    @unittest.skipUnless(have_apt_pkg, "apt_pkg not installed")
    @unittest.skipUnless(have_lsb_release, "lsb_release not installed")
    def test_filter_security_updates(self, apt_pkg_acquire, apt_pkg_init):
        pkgs = {'pkg1': DebianPkg('pkg1'),
                'pkg2': DebianPkg('pkg2'),
                }
        with patch('apt_pkg.Cache'):
            DebianDistro.filter_security_updates(pkgs)
        apt_pkg_init.assert_called_once_with()
        apt_pkg_acquire.assert_called_once_with()
