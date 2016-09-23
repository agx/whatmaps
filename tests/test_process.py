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

import os
import unittest
import random

from whatmaps.process import Process

from . import context


class TestWhatmapsProcess(unittest.TestCase):
    def setUp(self):
        self.tmpdir = context.new_tmpdir(__name__)
        self.procfs = str(self.tmpdir)
        self.pid = random.randint(1, 65535)
        self.piddir = os.path.join(self.procfs, str(self.pid))
        os.mkdir(self.piddir)
        self.exe = os.path.join(self.piddir, 'exe')
        self.cmdline = os.path.join(self.piddir, 'cmdline')
        self.maps = os.path.join(self.piddir, 'maps')
        self._write_cmdline('doesnotmatter')  # Write at least an empty cmdline
        self._write_exe_symlink('acommand')
        self._write_maps([['f32b43221000-7f32b4522000',
                           '---p',
                           '00020000',
                           'fe:02',
                           '1704011',
                           '/lib/x86_64-linux-gnu/libselinux.so.1'],
                          ['7f32b4521000-7f32b4623000',
                           'r--p',
                           '00020000',
                           'fe:02',
                           '1704011',
                           '/lib/x86_64-linux-gnu/libselinux.so.1'],
                          ])

    def _write_exe_symlink(self, name):
        exe = os.path.join(str(self.tmpdir), name)
        os.symlink(exe, self.exe)

    def _write_cmdline(self, text=''):
        f = open(self.cmdline, 'w')
        f.write(text)
        f.close()

    def _write_maps(self, data):
        f = open(self.maps, 'w')
        f.write('\n'.join([' '.join(r) for r in data]))
        f.close()

    def test_nonexistent(self):
        """No exe link should create an 'empty' object"""
        os.unlink(self.exe)
        p = Process(self.pid, self.procfs)
        self.assertIsNone(p.exe)
        self.assertIsNone(p.cmdline)

    def test_deleted(self):
        """Handle symlink to deleted binaries"""
        exe = '/does/not/matter'
        os.unlink(self.exe)
        os.symlink(os.path.join(self.piddir, '%s (deleted)' % exe),
                   self.exe)

        p = Process(self.pid, procfs=self.procfs)
        self.assertEqual(p.exe, exe)
        self.assertTrue(p.deleted, True)
        self.assertEqual(p.cmdline, 'doesnotmatter')

    def test_existing(self):
        p = Process(self.pid, procfs=self.procfs)
        exe = os.path.join(str(self.tmpdir), 'acommand')
        self.assertEqual(p.exe, exe)
        self.assertEqual(p.cmdline, 'doesnotmatter')
        self.assertFalse(p.deleted)
        self.assertEqual(str(p),
                         "<Process object pid:%d>" % self.pid)

    def test_maps(self):
        """Check whether the process maps a shared object at path"""
        p = Process(self.pid, procfs=self.procfs)
        self.assertFalse(p.maps('/does/not/exist'))
        self.assertTrue(p.maps('/lib/x86_64-linux-gnu/libselinux.so.1'))

    def test_no_maps(self):
        """Check if we don't fail if the process went away"""
        os.unlink(self.maps)
        p = Process(self.pid, procfs=self.procfs)
        self.assertFalse(p.maps('/does/not/exist'))
        self.assertFalse(p.maps('/lib/x86_64-linux-gnu/libselinux.so.1'))

    def test_broken_maps(self):
        """Continue on unparseable map file"""
        # Provoke index error by to few items in line
        self._write_maps([['do', 'few', 'items']])
        p = Process(self.pid, procfs=self.procfs)
        self.assertFalse(p.maps('/does/not/exist'))
        self.assertFalse(p.maps('/lib/x86_64-linux-gnu/libselinux.so.1'))

    @unittest.skipIf(os.getuid() == 0, "Skip if root")
    def test_broken_unreadable_map(self):
        """Raise error if map file is unreadable"""
        os.chmod(self.maps, 0)
        p = Process(self.pid, procfs=self.procfs)
        self.assertRaises(IOError, p.maps, '/does/not/exist')

    def tearDown(self):
        context.teardown()
