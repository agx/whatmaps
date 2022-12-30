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

import logging
import os
import re
import subprocess


try:
    import lsb_release
except ImportError:
    lsb_release = None


class Distro(object):
    """
    A distribution

    @cvar id: distro id as returned by lsb-release

    @cvar service_blacklist: services that should never be restarted
    @cvar service_blacklist_re: regex list of services that should
       never be restartet
    @cvar _pkg_services: A C{dict} that maps packages to services. In
      case we find binaries that match a key in this hash restart
      the services listed in values.
    @cvar _pkg_service_blacklist: if we find binaries in the package
      listed as key don't restart services listed in values
    """
    id = None
    service_blacklist = set()
    service_blacklist_re = set()

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
    def is_service_installed(klass, service):
        """Check wether a service exists on the system"""
        return True

    @classmethod
    def pkg_services(klass, pkg):
        """
        List of services that package pkg needs restarted that aren't part
        of pkg itself
        """
        return [s for s in klass._pkg_services.get(pkg.name, [])
                if klass.is_service_installed(s)]

    @classmethod
    def pkg_service_blacklist(klass, pkg):
        """
        List of services in pkg that we don't want to be restarted even when
        a binary from this package maps a shared lib that changed.
        """
        return klass._pkg_service_blacklist.get(pkg.name, [])

    def filter_services(self, services):
        """
        Filter out servies that match service_blacklist_re
        """
        ret = []
        matchers = [re.compile(b) for b in self.service_blacklist_re]
        for s in services:
            if not any([m.match(s) for m in matchers]):
                ret.append(s)
        return set(ret)

    @classmethod
    def has_apt(klass):
        """Does the distribution use apt"""
        return False

    @staticmethod
    def detect():
        return detect()


import whatmaps.debiandistro  # noqa: E402
import whatmaps.redhatdistro  # noqa: E402


def detect():
    """
    Detect the distribution we run on. Returns C{None} if the
    distribution is unknown.
    """
    id = None

    if lsb_release:
        id = lsb_release.get_distro_information()['ID']
    else:
        try:
            lsb_cmd = subprocess.Popen(['lsb_release', '--id', '-s'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL)
            output = lsb_cmd.communicate()[0]
            if not lsb_cmd.returncode:
                id = output.decode().split('\n')[0].strip()
        except OSError:
            # id is None in this case
            pass

    if id == whatmaps.debiandistro.DebianDistro.id:
        return whatmaps.debiandistro.DebianDistro
    elif id == whatmaps.redhatdistro.FedoraDistro.id:
        return whatmaps.redhatdistro.FedoraDistro
    else:
        if os.path.exists('/usr/bin/dpkg'):
            logging.warning("Unknown distro but dpkg found, assuming Debian")
            return whatmaps.debiandistro.DebianDistro
        elif os.path.exists('/bin/rpm'):
            logging.warning("Unknown distro but rpm found, assuming Fedora")
            return whatmaps.debiandistro.FedoraDistro
        else:
            return None
