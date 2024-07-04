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
    import lsb_release  # noqa: F401
    have_lsb_release = True
except ImportError:
    have_lsb_release = False
from whatmaps.distro import Distro, detect


class Pkg(object):
    name = 'doesnotmatter'


class TestDistro(unittest.TestCase):
    def test_abstract(self):
        """Check abstract method signatures"""
        # Variables
        self.assertEqual(Distro.service_blacklist, set())
        self.assertIsNone(Distro.id)
        # Pure virtual methods
        self.assertRaises(NotImplementedError, Distro.pkg, None)
        self.assertRaises(NotImplementedError, Distro.pkg_by_file, None)
        self.assertRaises(NotImplementedError, Distro.restart_service_cmd, None)
        self.assertRaises(NotImplementedError, Distro.restart_service, None)
        # Lookup methods
        self.assertEqual(Distro.pkg_services(Pkg), [])
        self.assertEqual(Distro.pkg_service_blacklist(Pkg), [])
        self.assertFalse(Distro.has_apt())

    @unittest.skipUnless(have_lsb_release, "lsb_release not installed")
    def test_detect_via_lsb_release_module(self):
        "Detect distro via lsb_release"
        with patch('lsb_release.get_distro_information', return_value={'ID': 'Debian'}):
            # Make sure we don't use the fallback
            with patch('os.path.exists', return_value=False):
                d = detect()
                self.assertEqual(d.id, 'Debian')

    def test_filter_services_empty(self):
        d = Distro()
        self.assertEqual(set(['foo', 'bar']),
                         d.filter_services(['foo', 'bar']))

    def test_filter_services_one(self):
        d = Distro()
        d.service_blacklist_re = ['^f..']
        self.assertEqual(set(['bar']),
                         d.filter_services(['foo', 'bar']))

    def test_filter_services_all(self):
        d = Distro()
        d.service_blacklist_re = ['^f..', '^b..']
        self.assertEqual(set(),
                         d.filter_services(['foo', 'bar']))
