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

from whatmaps.debianpkg import DebianPkg


class TestDebianPkg(unittest.TestCase):
    def test_services(self):
        with patch('whatmaps.pkg.Pkg._get_contents') as mock:
            mock.return_value = ['/etc/init.d/aservice', '/usr/bin/afile']
            p = DebianPkg('doesnotmatter')
            self.assertEqual(p.services, ['aservice'])
