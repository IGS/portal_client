import os

from setuptools import setup

# Utility function to read files. Used for the long_description.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='portal-client',
      description='Download client tool for IGS Portal servers.',
      long_description=read('DESC'),
      version='1.0',
      py_modules=['portal_client'],
      author='Victor Felix',
      author_email='victor73@github.com',
      license='MIT',
      install_requires=[
                       'boto >= 2.49.0',
                       'google-auth-oauthlib >= 0.2.0',
                       'google-cloud-storage >= 1.13.2'
                       ],
      packages=[''],
      package_dir={'': 'lib'},
      scripts=[
          'portal_client'
      ],
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
      ]
     )
