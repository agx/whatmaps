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
        self.assertRaises(Distro.pkg, None, None, NotImplementedError)
        self.assertRaises(Distro.pkg_by_file, None, NotImplementedError)
        self.assertRaises(Distro.restart_service_cmd, None, NotImplementedError)
        self.assertRaises(Distro.restart_service, None, NotImplementedError)
        # Lookup methods
        self.assertEqual(Distro.pkg_services(Pkg), [])
        self.assertEqual(Distro.pkg_service_blacklist(Pkg), [])
        self.assertFalse(Distro.has_apt())

    def test_detect_via_lsb_release_module(self):
        "Detect distro via lsb_release"
        with patch('lsb_release.get_distro_information', return_value={'ID': 'Debian'}):
            # Make sure we don't use the fallback
            with patch('os.path.exists', return_value=False):
                d = detect()
                self.assertEqual(d.id, 'Debian')
