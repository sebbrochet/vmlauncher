#!/usr/bin/env python

import os
import sys

sys.path.insert(0, os.path.abspath('lib'))
from vmlauncher import __version__, __author__
from distutils.core import setup

setup(name='vmlauncher',
      version=__version__,
      description='vCenter VM start/stop commander',
      long_description='This command-line tool lets you start/stop a set of VMs in a VMWare vCenter host in a pre-defined order.',
      author=__author__,
      author_email='contact@sebbrochet.com',
      url='https://code.google.com/p/vmlauncher/',
      platforms=['linux'],
      license='MIT License',
      install_requires=['paramiko'],
      package_dir={ 'vmlauncher': 'lib/vmlauncher' },
      packages=[
         'vmlauncher',
      ],
      scripts=[
         'bin/vmlauncher',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: System :: Systems Administration',
          ],
      )
