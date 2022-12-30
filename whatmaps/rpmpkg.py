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

import os
import re

from . pkg import Pkg


class RpmPkg(Pkg):
    type = 'RPM'
    _init_script_re = re.compile(r'/etc/rc.d/init.d/[\w\-\.]')
    _list_contents = ['rpm', '-ql', '$pkg_name']

    def __init__(self, name):
        Pkg.__init__(self, name)

    @property
    def services(self):
        if self._services is not None:
            return self._services

        self._services = []
        contents = self._get_contents()
        # Only supports sysvinit so far:
        for line in contents:
            if self._init_script_re.match(line):
                self._services.append(os.path.basename(line.strip()))
        return self._services
