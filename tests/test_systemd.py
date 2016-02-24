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

from whatmaps.systemd import Systemd
from whatmaps.process import Process

class Process(object):
    def __init__(self, pid):
        self.pid = pid

class TestSystemd(unittest.TestCase):
    def test_is_init(self):
        """Check if we create a systemd object if systemd is the init system in use"""
        with patch('os.path.exists', return_value=True):
            self.assertIsNotNone(Systemd())

    def test_is_not_init(self):
        """Check if we raise an exception if systemd isn't tthe init system in use"""
        with patch('os.path.exists', return_value=False):
            self.assertRaises(ValueError, Systemd)

    def test_process_to_unit(self):
        p = Process(952)
        output = """libvirt-bin.service - Virtualization daemon
   Loaded: loaded (/lib/systemd/system/libvirt-bin.service; enabled)
   Active: active (running) since Fr 2014-07-11 16:10:55 CEST; 50min ago
     Docs: man:libvirtd(8)
           http://libvirt.org
 Main PID: 952 (libvirtd)
   CGroup: name=systemd:/system/libvirt-bin.service
           ├─ 952 /usr/sbin/libvirtd
           └─1355 /usr/sbin/dnsmasq --conf-file=/var/lib/libvirt/dnsmasq/default.conf
    """.encode('utf-8')
        with patch('os.path.exists', return_value=True):
            with patch('subprocess.Popen') as mock:
                PopenMock = mock.return_value
                PopenMock.communicate.return_value = [output]
                PopenMock.returncode = 0
                result = Systemd().process_to_unit(p)
                self.assertEqual(result, 'libvirt-bin.service')

                PopenMock.returncode = 1
                result = Systemd().process_to_unit(p)
                self.assertIsNone(result)

