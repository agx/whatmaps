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
import subprocess

from . distro import Distro
from . rpmpkg import RpmPkg


class RedHatDistro(Distro):
    """RPM based distribution"""
    _pkg_re = re.compile(r'(?P<pkg>[\w\-\+]+)-(?P<ver>[\w\.]+)'
                         '-(?P<rel>[\w\.]+)\.(?P<arch>.+)')

    @classmethod
    def pkg(klass, name):
        return RpmPkg(name)

    @classmethod
    def pkg_by_file(klass, path):
        find_file = subprocess.Popen(['rpm', '-qf', path],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        output = find_file.communicate()[0]
        if find_file.returncode:
            return None
        m = klass._pkg_re.match(output.strip())
        if m:
            pkg = m.group('pkg')
        else:
            pkg = output.strip()
        return RpmPkg(pkg)

    @classmethod
    def restart_service_cmd(klass, name):
        return ['service', name, 'restart']


class FedoraDistro(RedHatDistro):
    id = 'Fedora'
