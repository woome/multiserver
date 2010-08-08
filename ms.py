
"""
MultiServer

This is a simple wsgi handler for Spawning that does virtual host
handling across a directory of python modules.

This can use a config variable wsgi_path to find the modules. The path
can be specified in a config file: ~/.mswsgi.conf

  [Server]
  wsgi_path = ...

The python module loaded is right now, always: server.spawnwoome
"""

import re
import os
import traceback
from os.path import join as joinpath

def dispatch(path, environ, start_response):
    """Dispatch the wsgi call to the specified directory"""

    import sys
    sys.path += [joinpath(path, "woome")]

    # We have to do this ONLY because I want to monkeypatch settings
    import config
    config.setup_django_env()
    import settings
    try:
         sys.path = [settings.DJANGO_PATH_DIR] + sys.path
    except AttributeError:
         pass
    
    from os.path import abspath, basename, dirname
    reponame = basename(path).replace("_", "-")

    settings.STATIC_URL = 'http://%s.repos.dev.woome.com' % reponame
    settings.IMG_URL = 'http://%s.repos.dev.woome.com' % reponame

    import server.spawnwoome
    wsgi_handler = server.spawnwoome.getapp()
    return wsgi_handler(environ, start_response)

def multiwsgidispatch(conf):
    """Get a wsgi handler to do multiple dispatch.

    The handler uses the Host header to try to find a matching wsgi
    instance in the config['wsgi_path']
    """
    # Capture the config
    config = conf
    def wsgi_dispatcher(environ, start_response):
        """Virtual host WSGI dispatcher"""
        wsgi_path = config.get("wsgi_path")
        host = environ["HTTP_HOST"]
        targetpart = host.split(".")[0]
        # Make a regex that will match against targets
        target_re = re.compile("%s.*" % re.sub("-", "[_-]", targetpart))
        for entry in os.listdir(wsgi_path):
            if target_re.match(entry):
                try:
                    path = joinpath(wsgi_path, entry)
                    return dispatch(path, environ, start_response)
                except Exception,e:
                    start_response('500 Error', [('content-type', 'text/html')])
                    return ["<p>Error: %s</p>" % e]

        # Otherwise it's an error
        start_response('500 Error', [('content-type', 'text/html')])
        return ["<p>No target found for %s</p>" % host]

    return wsgi_dispatcher


# Config stuff
from ConfigParser import ConfigParser
from os.path import expanduser

### Spawning stuff 
### Start this under spawning like:
###    spawn -p 8110 -f ms.spawning_config_factory none

def app_factory(conf):
    return multiwsgidispatch(conf)

def spawning_config_factory(args):
    """A Spawning config factory"""
    conf = ConfigParser()
    try:
        conf.read(expanduser("~/.mswsgi.conf"))
    except:
        pass

    return {
        'args': args,
        'host': args.get('host'),
        'port': args.get('port'),
        'app_factory': "ms.app_factory",
        'app': "", 
        'wsgi_path': conf.get("Server", "wsgi_path"),
        'deadman_timeout': 10,
        'num_processes': 4,
        }

# End
