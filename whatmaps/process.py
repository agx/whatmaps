#!/usr/bin/python -u
# vim: set fileencoding=utf-8 :
#
# (C) 2010,2014 Guido Günther <agx@sigxcpu.org>
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
#

import errno
import logging
import os
import re

class Process(object):
    """A process - Linux only so far, needs /proc mounted"""
    deleted_re = re.compile(r"(?P<exe>.*) \(deleted\)$")

    def __init__(self, pid, procfs=None):
        self.procfs = procfs or '/proc'
        self.pid = pid
        self.mapped = []
        self.deleted = False
        try:
            self.exe = os.readlink(self._procpath(str(self.pid), 'exe'))
            m = self.deleted_re.match(self.exe)
            if m:
                self.exe = m.group('exe')
                self.deleted = True
                logging.debug("Using deleted exe %s", self.exe)
            if not os.path.exists(self.exe):
                logging.debug("%s doesn't exist", self.exe)
            self.cmdline = open(self._procpath('%d/cmdline' % self.pid)).read()
        except OSError:
            self.exe = None
            self.cmdline = None

    def _procpath(self, *args):
        """
        Return a path relative to the current procfs bsae
        """
        return os.path.join(self.procfs, *args)

    def _read_maps(self):
        """Read the SOs from /proc/<pid>/maps"""
        try:
            f = open(self._procpath('%d/maps' % self.pid))
        except IOError as e:
            # ignore killed process
            if e.errno != errno.ENOENT:
                raise
            return
        for line in f:
            try:
                so = line.split()[5].strip()
                self.mapped.append(so)
            except IndexError:
                pass

    def maps(self, path):
        """Check if the process maps the object at path"""
        if not self.mapped:
            self._read_maps()

        return True if path in self.mapped else False

    def __repr__(self):
        return "<Process object pid:%d>" % self.pid
