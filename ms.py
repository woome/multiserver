

import re
import os
import traceback
from os.path import join as joinpath

PATH="/home/app/hgrepos/repos"

def dispatch(path, environ, start_response):
    """Dispatch the wsgi call to the specified directory"""
    #import pdb
    #pdb.set_trace()

    import sys
    sys.path += [joinpath(path, "woome")]
    wsgihandler_maker = __import__('server.spawnwoome')
    app = wsgihandler_maker.spawnwoome.getapp()
    return app(environ, start_response)

def multiwsgidispatch(environ, start_response):
    host = environ["HTTP_HOST"]
    targetpart = host.split(".")[0]
    # Make a regex that will match against targets
    target_re = re.compile("%s.*" % re.sub("-", "[_-]", targetpart))
    for e in os.listdir(PATH):
        if target_re.match(e):
            try:
                return dispatch(joinpath(PATH, e), environ, start_response)
            except Exception,e:
                print e
                traceback.print_exc()
                start_response('500 Error', [('content-type', 'text/html')])
                return ["<p>Error: %s</p>" % e]
                

    # Otherwise it's an error
    start_response('500 Error', [('content-type', 'text/html')])
    return ["<p>No target found for %s</p>" % host]

### Spawning stuff 
### Start this under spawning like:
###    spawn -p 8110 -f ms.spawning_config_factory none
### this interface needs significant work

def app_factory(conf):
    return multiwsgidispatch

def spawning_config_factory(args):
    """A Spawning config factory"""
    return {
        'args': args,
        'host': args.get('host'),
        'port': args.get('port'),
        'app_factory': "ms.app_factory",
        'app': "", 
        'deadman_timeout': 10,
        'num_processes': 4,
        }

# End
