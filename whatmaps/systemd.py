# vim: set fileencoding=utf-8 :
#
# (C) 2014,2015 Guido Günther <agx@sigxcpu.org>
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

import os
import subprocess


class Systemd(object):
    """Systemd init system"""

    def __init__(self):
        if not self.is_running():
            raise ValueError("Systemd not running")

    @staticmethod
    def is_running():
        return os.path.exists("/run/systemd/system")

    @staticmethod
    def process_to_unit(process):
        cmd = ['systemctl', 'status', "%d" % process.pid]
        systemctl_status = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output = systemctl_status.communicate()[0]
        if systemctl_status.returncode:
            return None
        else:
            parts = output.decode('utf-8').split()
            if parts[0].endswith('.service'):
                return parts[0]
            elif parts[1].endswith('.service'):
                return parts[1]
            elif parts[1].startswith('session-') and parts[1].endswith('.scope'):
                msg = output.decode('utf-8').split('\n')[0][2:]
                raise ValueError("Can't parse service name from %s" % msg)
            else:
                raise ValueError("Can't parse service name from: (%s %s)" % (parts[0], parts[1]))
