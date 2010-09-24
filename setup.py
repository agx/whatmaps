#!/usr/bin/python
# vim: set fileencoding=utf-8 :

from distutils.core import setup

data_files = [('../etc/apt/apt.conf.d/',
              ['apt/50whatmaps_apt']),
             ('../etc/apt/apt.conf.d/',
              ['apt/20services']),
            ]

setup(name = "whatmaps",
      author = 'Guido Günther',
      author_email = 'agx@sigxcpu.org',
      data_files = data_files,
      scripts = [ 'whatmaps' ],
)

# vim:et:ts=4:sw=4:et:sts=4:ai:set list listchars=tab\:»·,trail\:·:
