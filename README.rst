****************************
Mopidy-Plex
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Plex.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Plex/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/Mopidy-Plex.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Plex/
    :alt: Number of PyPI downloads

.. image:: https://img.shields.io/travis/havardgulldahl/mopidy_plex/master.svg?style=flat
    :target: https://travis-ci.org/havardgulldahl/mopidy_plex
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/havardgulldahl/mopidy_plex/master.svg?style=flat
   :target: https://coveralls.io/r/havardgulldahl/mopidy_plex
   :alt: Test coverage

Mopidy extension for playing audio from a Plex server


Installation
============

Install by running::

    pip install Mopidy-Plex

Or, if available, install the Debian/Ubuntu package from `apt.mopidy.com
<http://apt.mopidy.com/>`_.


And you need the `python-plexapi` module as well::

    pip install plexapi


Extra setup hassle
-------------------

**Please note** that you need the `python-plexapi` package *with music support*, a.k.a *Plex Audio*!
As of 2016-02-02, that functionality is not yet upstream, so you need to install it from
https://github.com/havardgulldahl/python-plexapi for now.



Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Plex to your Mopidy configuration file::

    [plex]
    enabled = true
    server = http://192.168.0.105:32400


Project resources
=================

- `Source code <https://github.com/havardgulldahl/mopidy-plex>`_
- `Issue tracker <https://github.com/havardgulldahl/mopidy-plex/issues>`_


Credits
=======

- Original author: `@havardgulldahl <https://github.com/havardgulldahl>`_
- Current maintainer: `@havardgulldahl <https://github.com/havardgulldahl>`_
- `Contributors <https://github.com/havardgulldahl/mopidy-plex/graphs/contributors>`_


Changelog
=========

v0.1.0 (UNRELEASED)
----------------------------------------


v0.1.0b (2016-02-02)
----------------------------------------

- Initial beta release.
- Listing and searching Plex Server content works.
- Playing audio works.
- Please `file bugs <https://github.com/havardgulldahl/mopidy-plex/issues>`_.

