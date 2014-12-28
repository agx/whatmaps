#!/usr/bin/python
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

from setuptools import setup

data_files = []

try:
    import lsb_release
    if (lsb_release.get_distro_information()['ID'] in [ 'Debian' ] or
        os.path.exists('/etc/debian_version')):
       data_files = [('../etc/apt/apt.conf.d/',
                      ['apt/50whatmaps_apt']),
                     ('../etc/apt/apt.conf.d/',
                      ['apt/20services']),
                    ]
except ImportError:
    pass

setup(name = "whatmaps",
      author = 'Guido Günther',
      author_email = 'agx@sigxcpu.org',
      data_files = data_files,
      packages = ['whatmaps'],
      entry_points = {
          'console_scripts': [ 'whatmaps = whatmaps.command:run' ],
      },
)

# vim:et:ts=4:sw=4:et:sts=4:ai:set list listchars=tab\:»·,trail\:·:
