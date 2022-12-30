#!/usr/bin/python3 -u
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
import glob
import os
import logging
import sys
from optparse import OptionParser

from . process import Process
from . distro import Distro
from . pkg import PkgError
from . systemd import Systemd


def check_maps(procs, shared_objects):
    restart_procs = {}
    for proc in procs:
        for so in shared_objects:
            if proc.maps(so):
                if proc.exe in restart_procs:
                    restart_procs[proc.exe] += [proc]
                else:
                    restart_procs[proc.exe] = [proc]
                break
    return restart_procs


def get_all_pids():
    processes = []
    paths = glob.glob('/proc/[0-9]*')

    for path in paths:
        p = Process(int(path.rsplit('/')[-1]))
        processes.append(p)

    return processes


def write_cmd_file(services, cmd_file, distro):
    "Write out commands needed to restart the services to a file"
    out = open(cmd_file, 'w')
    print('#! /bin/sh', file=out)
    for service in services:
        logging.info("Need to restart '%s'", service)
        print(" ".join(distro.restart_service_cmd(service)), file=out)
    out.close()
    os.chmod(cmd_file, 0o755)


def find_pkgs(procs, distro):
    """
    Find packages that contain the binaries of the given processes
    """
    pkgs = {}
    for proc in procs:
        pkg = distro.pkg_by_file(proc)
        if not pkg:
            logging.warning("No package found for '%s' - restart manually" % proc)
        else:
            if pkg.name in pkgs:
                pkgs[pkg.name].procs.append(proc)
            else:
                pkg.procs = [proc]
                pkgs[pkg.name] = pkg

    if pkgs:
        logging.info("Packages that ship the affected binaries:")
    for pkg in list(pkgs.values()):
        logging.info("  Pkg: %s, binaries: %s" % (pkg.name, pkg.procs))

    return pkgs


def find_services(pkgs, distro):
    """
    Determine the services in pkgs honoring distro specific mappings
    and blacklists
    """
    all_services = set()

    for pkg in list(pkgs.values()):
        services = set(pkg.services + distro.pkg_services(pkg))
        services -= set(distro.pkg_service_blacklist(pkg))
        if not services:
            logging.warning("No service script found in '%s' for '%s' "
                            "- restart manually" % (pkg.name, pkg.procs))
        else:
            all_services.update(services)
    all_services -= distro.service_blacklist
    return all_services


def find_systemd_units(procmap, distro):
    """Find systemd units that contain the given processes"""
    units = set()

    for dummy, procs in list(procmap.items()):
        for proc in procs:
            try:
                unit = Systemd.process_to_unit(proc)
            except ValueError as e:
                logging.warning("No systemd unit found for '%s': %s "
                                "- restart manually" % (proc.exe, e))
                continue
            if not unit:
                logging.warning("No systemd unit found for '%s' "
                                "- restart manually" % proc.exe)
            else:
                units.add(unit)
    units -= set([service + '.service' for service in distro.service_blacklist])
    return units


def filter_services(distro, services):
    filtered = distro.filter_services(services)
    diff = services - filtered
    if len(diff):
        logging.warning("Filtered out blacklisted service%s %s - restart manually",
                        's' if len(diff) > 1 else '',
                        ', '.join(diff))
    return filtered


def main(argv):
    shared_objects = []
    services = None
    ret = 0

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

    distro = Distro.detect()()
    if not distro:
        logging.error("Unsupported Distribution")
        return 1
    else:
        logging.debug("Detected distribution: '%s'", distro.id)

    if args:
        pkgs = [distro.pkg(arg) for arg in args]
    elif options.apt and distro.has_apt():
        try:
            pkgs = distro.read_apt_pipeline()
        except PkgError:
            logging.error("Can't read apt pipeline")
            return 1
        if not pkgs:
            return 0
        pkgs, notfound = distro.filter_security_updates(pkgs)
        if notfound:
            logging.warning("Pkgs %s not found in apt cache" % ", ".join(notfound))
        logging.debug("Security Upgrades: %s" % pkgs)
    else:
        parser.print_help()
        return 1

    # Find shared objects of updated packages
    for pkg in pkgs:
        try:
            shared_objects += pkg.shared_objects
        except PkgError as e:
            logging.error("%s - skipping package %s" % (e, pkg.name))
            ret = 1
    logging.debug("Found shared objects:")
    for so in shared_objects:
        logging.debug("  %s", so)

    # Find processes that map them
    try:
        restart_procs = check_maps(get_all_pids(), shared_objects)
    except IOError as e:
        if e.errno == errno.EACCES:
            logging.error("Can't open process maps in '/proc/<pid>/maps', are you root?")
            return 1
        else:
            raise
    logging.debug("Processes that map them:")
    for exe, pids in list(restart_procs.items()):
        logging.debug("  Exe: %s Pids: %s", exe, pids),

    if Systemd.is_running():
        logging.debug("Detected Systemd")
        services = find_systemd_units(restart_procs, distro)
    else:
        # Find the packages that contain the binaries the processes are
        # executing
        pkgs = find_pkgs(restart_procs, distro)

        # Find the services in these packages honoring distro specific
        # mappings and blacklists
        try:
            services = find_services(pkgs, distro)
        except NotImplementedError:
            if level > logging.INFO:
                logging.error("Getting Service listing not implemented "
                              "for distribution %s - rerun with --verbose to see a list"
                              "of binaries that map a shared objects from %s",
                              distro.id, args)
                return 1
            else:
                return 0

    services = filter_services(distro, services)

    if options.restart:
        if options.print_cmds and services:
            write_cmd_file(services, options.print_cmds, distro)
        else:
            for service in services:
                logging.info("Restarting '%s'" % service)
                distro.restart_service(service)
    elif services:
        print("Services that possibly need to be restarted:")
        for s in services:
            print(s)

    return ret


def run():
    return main(sys.argv)

# vim:et:ts=4:sw=4:et:sts=4:ai:set list listchars=tab\:»·,trail\:·:
