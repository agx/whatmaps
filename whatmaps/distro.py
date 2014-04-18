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

import subprocess

class Distro(object):
    """
    A distribution
    @cvar id: distro id as returned by lsb-release
    """
    id = None
    service_blacklist = set()
    _pkg_services = {}
    _pkg_blacklist = {}
    _pkg_service_blacklist = {}

    @classmethod
    def pkg(klass, name):
        """Return package object named name"""
        raise NotImplementedError

    @classmethod
    def pkg_by_file(klass, path):
        """Return package object that contains path"""
        raise NotImplementedError

    @classmethod
    def restart_service_cmd(klass, service):
        """Command to restart service"""
        raise NotImplementedError

    @classmethod
    def restart_service(klass, service):
        """Restart a service"""
        subprocess.call(klass.restart_service_cmd(service))

    @classmethod
    def pkg_services(klass, pkg):
        """
        List of services that package pkg needs restarted that aren't part
        of pkg itself
        """
        return klass._pkg_services.get(pkg.name, [])

    @classmethod
    def pkg_service_blacklist(klass, pkg):
        """
        List of services in pkg that we don't want to be restarted even when
        a binary from this package maps a shared lib that changed.
        """
        return klass._pkg_service_blacklist.get(pkg.name, [])

    @classmethod
    def has_apt(klass):
        """Does the distribution use apt"""
        return False
