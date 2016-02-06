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
#   GNU General Public Licnese for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

try:
    import apt_pkg
except ImportError:
    apt_pkg = None

try:
    import lsb_release
except ImportError:
    lsb_release = None

import logging
import os
import subprocess
import sys
import string

from . distro import Distro
from . debianpkg import DebianPkg
from . pkg import PkgError
from . systemd import Systemd

class DebianDistro(Distro):
    "Debian (dpkg) based distribution"
    id = 'Debian'

    _pkg_services = { 'apache2-mpm-worker':  [ 'apache2' ],
                      'apache2-mpm-prefork': [ 'apache2' ],
                      'apache2.2-bin':       [ 'apache2' ],
                      'apache2-bin':         [ 'apache2' ],
                      'dovecot-imapd':       [ 'dovecot' ],
                      'dovecot-pop3d':       [ 'dovecot' ],
                      'exim4-daemon-light':  [ 'exim4' ],
                      'exim4-daemon-heavy':  [ 'exim4' ],
                      'libvirt-daemon':      [ 'libvirtd' ],
                      'openjdk-6-jre-headless': ['jenkins', 'tomcat7'],
                      'openjdk-7-jre-headless': ['jenkins', 'tomcat7'],
                      'qemu-system-x86_64':  [ 'libvirt-guests' ],
                    }

    # Per package blacklist
    _pkg_service_blacklist = { 'libvirt-bin': [ 'libvirt-guests' ] }

    # Per distro blacklist
    service_blacklist = set(['kvm', 'qemu-kvm', 'qemu-system-x86'])

    @classmethod
    def pkg(klass, name):
        return DebianPkg(name)

    @classmethod
    def pkg_by_file(klass, path):
        find_file = subprocess.Popen(['dpkg-query', '-S', path],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        output = find_file.communicate()[0]
        if find_file.returncode:
            return None
        pkg = output.split(':')[0]
        return DebianPkg(pkg)

    @classmethod
    def restart_service_cmd(klass, service):
        """The command that should be used to start a service"""
        if Systemd.is_running() and service.endswith('.service'):
            name = service[:-len('.service')]
        else:
            name = service
        return ['invoke-rc.d', name, 'restart']

    @classmethod
    def is_service_installed(klass, name):
        """Whether the system has this service"""
        return os.path.exists('/etc/init.d/%s' % name)

    @classmethod
    def has_apt(klass):
        return True

    @staticmethod
    def read_apt_pipeline():
        whatmaps_enabled = False

        version = sys.stdin.readline().rstrip()
        if version != "VERSION 2":
            err = "Wrong or missing VERSION from apt pipeline"
            logging.error("%s\n"
                          "(is Dpkg::Tools::Options::/usr/bin/whatmaps::Version set to 2?)"
                          % err)
            raise PkgError(err)

        while 1:
            aptconfig = sys.stdin.readline()
            if not aptconfig or aptconfig == '\n':
                break
            if aptconfig.startswith('Whatmaps::Enable-Restart=') and \
               aptconfig.strip().split('=', 1)[1].lower() in ["true", "1"]:
                    logging.debug("Service restarts enabled")
                    whatmaps_enabled = True

        if not whatmaps_enabled:
            return None

        pkgs = {}
        for line in sys.stdin.readlines():
            if not line:
                break
            (pkgname, oldversion, compare, newversion, filename) = line.split()

            if filename == '**CONFIGURE**':
                if oldversion != '-': # Updates only
                    pkgs[pkgname] = DebianPkg(pkgname)
                    pkgs[pkgname].version = newversion
        return pkgs


    @classmethod
    def _security_update_origins(klass):
        "Determine security update origins from apt configuration"

        if lsb_release is None:
            raise PkgError("lsb_release not found, can't determine security updates")

        codename = lsb_release.get_distro_information()['CODENAME']
        def _subst(line):
            mapping = {'distro_codename' : codename,
                       'distro_id' : klass.id, }
            return string.Template(line).substitute(mapping)

        origins = []
        for s in apt_pkg.config.value_list('Whatmaps::Security-Update-Origins'):
            (distro_id, distro_codename) = s.split()
            origins.append((_subst(distro_id),
                            _subst(distro_codename)))
        logging.debug("Security Update Origins: %s", origins)
        return origins


    @classmethod
    def filter_security_updates(klass, pkgs):
        """Filter on security updates"""

        if apt_pkg is None:
            raise PkgError("apt_pkg not installed, can't determine security updates")

        apt_pkg.init()
        acquire = apt_pkg.Acquire()
        cache = apt_pkg.Cache()

        security_update_origins = klass._security_update_origins()
        security_updates = {}

        for pkg in list(pkgs.values()):
            cache_pkg = cache[pkg.name]
            for cache_version in cache_pkg.version_list:
                if pkg.version == cache_version.ver_str:
                    for pfile, _ in cache_version.file_list:
                        for origin in security_update_origins:
                            if pfile.origin == origin[0] and \
                               pfile.archive == origin[1]:
                                security_updates[pkg] = pkg
                                break
        return security_updates
