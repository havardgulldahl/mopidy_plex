from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext

__version__ = '0.1.0'

# TODO: If you need to log, use loggers named after the current Python module
logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Plex'
    ext_name = 'plex'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['server'] = config.String()
        #schema['username'] = config.String()
        #schema['password'] = config.Secret()
        return schema

    def setup(self, registry):
        # You will typically only implement one of the following things
        # in a single extension.

        from .backend import PlexBackend
        registry.add('backend', PlexBackend)

    def validate_environment(self):
        # Any manual checks of the environment to fail early.  Dependencies
        # described by setup.py are checked by Mopidy, so you should not check
        # their presence here.

        # TODO: ping server?
        pass

    def validate_config(self, config):  # no_coverage
        if not config.getboolean('plex', 'enabled'):
            return
        if not config.get('plex', 'server'):
            raise ExtensionError(
                'In order to use the Plex Music extension you must provide a '
                'server address. For more information refer to '
                'https://github.com/havardgulldahl/mopidy-plex/')
