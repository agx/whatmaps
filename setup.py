#!/usr/bin/python
# vim: set fileencoding=utf-8 :

from distutils.core import setup

data_files = []

try:
    import lsb_release
    if lsb_release.get_distro_information()['ID'] in [ 'Debian' ]:
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
      scripts = [ 'whatmaps' ],
)

# vim:et:ts=4:sw=4:et:sts=4:ai:set list listchars=tab\:»·,trail\:·:
