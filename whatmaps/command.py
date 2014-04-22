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

import glob
import os
import logging
import re
import string
import subprocess
import sys
import errno
from optparse import OptionParser
try:
    import lsb_release
except ImportError:
    lsb_release = None

from . process import Process
from . debiandistro import DebianDistro
from . redhatdistro  import FedoraDistro
from . pkg import Pkg, PkgError
from . debianpkg import DebianPkg
from . rpmpkg import RpmPkg


def check_maps(procs, shared_objects):
    restart_procs = {}
    for proc in procs:
        for so in shared_objects:
            if proc.maps(so):
                if restart_procs.has_key(proc.exe):
                    restart_procs[proc.exe] += [ proc ]
                else:
                    restart_procs[proc.exe] = [ proc ]
                continue
    return restart_procs


def get_all_pids():
    processes = []
    paths = glob.glob('/proc/[0-9]*')

    for path in paths:
        p = Process(int(path.rsplit('/')[-1]))
        processes.append(p)

    return processes


def detect_distro():
    id = None

    if lsb_release:
        id = lsb_release.get_distro_information()['ID']
    else:
        try:
            lsb_cmd = subprocess.Popen(['lsb_release', '--id', '-s'],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            output = lsb_cmd.communicate()[0]
            if not lsb_cmd.returncode:
               id = output.strip()
        except OSError:
            # id is None in this case
            pass

    if id == DebianDistro.id:
        return DebianDistro
    elif id == FedoraDistro.id:
        return FedoraDistro
    else:
        if os.path.exists('/usr/bin/dpkg'):
            logging.warning("Unknown distro but dpkg found, assuming Debian")
            return DebianDistro
        elif os.path.exists('/bin/rpm'):
            logging.warning("Unknown distro but rpm found, assuming Fedora")
            return FedoraDistro
        else:
            return None


def write_cmd_file(services, cmd_file, distro):
    "Write out commands needed to restart the services to a file"
    out = open(cmd_file, 'w')
    print >>out, '#! /bin/sh'
    for service in services:
        logging.debug("Need to restart %s", service)
        print >>out, " ".join(distro.restart_service_cmd(service))
    out.close()
    os.chmod(cmd_file, 0755)


def main(argv):
    shared_objects = []

    parser = OptionParser(usage='%prog [options] pkg1 [pkg2 pkg3 pkg4]')
    parser.add_option("--debug", action="store_true", dest="debug",
                      default=False, help="enable debug output")
    parser.add_option("--verbose", action="store_true", dest="verbose",
                      default=False, help="enable verbose output")
    parser.add_option("--restart", action="store_true", dest="restart",
                      default=False, help="Restart services")
    parser.add_option("--print-cmds", dest="print_cmds",
                      help="Output restart commands to file instead of restarting")
    parser.add_option("--apt", action="store_true", dest="apt", default=False,
                      help="Use in apt pipeline")

    (options, args) = parser.parse_args(argv[1:])

    if options.debug:
        level = logging.DEBUG
    elif options.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(level=level,
                        format='%(levelname)s: %(message)s')

    distro = detect_distro()
    if not distro:
        logging.error("Unsupported Distribution")
        return 1
    else:
        logging.debug("Detected distribution: '%s'", distro.id)

    if args:
        pkgs = [ distro.pkg(arg) for arg in args ]
    elif options.apt and distro.has_apt():
        try:
            pkgs = distro.read_apt_pipeline()
        except PkgError:
            logging.error("Can't read apt pipeline")
            return 1
        if not pkgs:
            return 0
        pkgs = distro.filter_security_updates(pkgs)
        logging.debug("Security Upgrades: %s" % pkgs)
    else:
        parser.print_help()
        return 1

    # Find shared objects of updated packages
    for pkg in pkgs:
        try:
            shared_objects += pkg.shared_objects
        except PkgError:
            logging.error("Cannot parse contents of %s" % pkg.name)
            return 1
    logging.debug("Found shared objects:")
    map(lambda x: logging.debug("  %s", x), shared_objects)

    # Find processes that map them
    restart_procs = check_maps(get_all_pids(), shared_objects)
    logging.debug("Processes that map them:")
    map(lambda (x, y):  logging.debug("  Exe: %s Pids: %s", x, y),
                                      restart_procs.items())

    # Find packages that contain the binaries of these processes
    pkgs = {}
    for proc in restart_procs:
        pkg = distro.pkg_by_file(proc)
        if not pkg:
            logging.warning("No package found for '%s' - restart manually" % proc)
        else:
            if pkgs.has_key(pkg.name):
                pkgs[pkg.name].procs.append(proc)
            else:
                pkg.procs = [ proc ]
                pkgs[pkg.name] = pkg

    logging.info("Packages that ship the affected binaries:")
    map(lambda x: logging.info("  Pkg: %s, binaries: %s" % (x.name, x.procs)),
        pkgs.values())

    all_services = set()
    try:
        for pkg in pkgs.values():
            services = set(pkg.services + distro.pkg_services(pkg))
            services -= set(distro.pkg_service_blacklist(pkg))
            if not services:
                logging.warning("No service script found in '%s' for '%s' "
                                "- restart manually" % (pkg.name, pkg.procs))
            else:
                all_services.update(services)
        all_services -= distro.service_blacklist
    except NotImplementedError:
        if level > logging.INFO:
            logging.error("Getting Service listing not implemented "
            "for distribution %s - rerun with --verbose to see a list"
            "of binaries and packages to map a shared objects from %s",
            distro.id, args)
            return 1
        else:
            return 0

    if options.restart:
        if options.print_cmds and all_services:
            write_cmd_file(all_services, options.print_cmds, distro)
        else:
            for service in all_services:
                logging.info("Restarting %s" % service)
                distro.restart_service(service)
    elif all_services:
        print "Services that possibly need to be restarted:"
        for s in all_services:
            print s

    return 0

def run():
    return(main(sys.argv))

if __name__ == '__main__':
    sys.exit(main(sys.argv))

# vim:et:ts=4:sw=4:et:sts=4:ai:set list listchars=tab\:»·,trail\:·:
