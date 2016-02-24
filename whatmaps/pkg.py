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

import re
import string
import subprocess

class PkgError(Exception):
    pass


class Pkg(object):
    """
    A package in a distribution
    @var services:  list of services provided by package
    @var shared_objects: list of shared objects shipped in this package
    @cvar type: package type (e.g. RPM or Debian)
    @cvar _so_regex: regex that matches shared objects in the list returned by
                     _get_contents
    @cvar _list_contents: command to list contents of a package, will be passed
                     to subprocess. "$pkg_name" will be replaced by the package
                     name.
    """

    type = None
    services = None
    _so_regex = re.compile(r'(?P<so>/.*\.so(\.[^/]*)?$)')
    _list_contents = None

    def __init__(self, name):
        self.name = name
        self._services = None
        self._shared_objects = None
        self._contents = None

    def __repr__(self):
        return "<%s Pkg object name:'%s'>" % (self.type, self.name)

    def _get_contents(self):
        """List of files in the package"""
        if self._contents:
            return self._contents
        else:
            cmd = [ string.Template(arg).substitute(arg, pkg_name=self.name)
                    for arg in self._list_contents ]
            list_contents = subprocess.Popen(cmd,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE)
        output = list_contents.communicate()[0]
        if list_contents.returncode:
            raise PkgError("Failed to list package contents for '%s'" % self.name)
        self._contents = output.decode('utf-8').split('\n')
        return self._contents

    @property
    def shared_objects(self):
        if self._shared_objects is not None:
            return self._shared_objects

        self._shared_objects = []
        contents = self._get_contents()

        for line in contents:
            m = self._so_regex.match(line)
            if m:
                self._shared_objects.append(m.group('so'))
        return self._shared_objects
