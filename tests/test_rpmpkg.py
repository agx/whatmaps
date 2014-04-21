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

from whatmaps.rpmpkg import RpmPkg

class TestRpmPkg(unittest.TestCase):
    def test_services(self):
        with patch('whatmaps.pkg.Pkg._get_contents') as mock:
            mock.return_value = ['/etc/rc.d/init.d/aservice', '/usr/bin/afile']
            p = RpmPkg('doesnotmatter')
            self.assertEqual(p.services, ['aservice'])
