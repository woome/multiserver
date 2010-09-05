
"""
MultiServer

This is a simple wsgi server that does virtual host handling across a
directory of python modules.

This can use a config variable wsgi_path to find the modules. The path
can be specified in a config file: ~/.mswsgi.conf

  [Server]
  wsgi_path = ...

The python module loaded is defined in the config file:

  [Server]
  module_name = ...

The module is imported by it's name. A function 'dispatch' is
expected.

Reference for the config file:

  module_name  the module name used to do the dispatching.
  wsgi_path    where to find server instances
  port         the port to start the multiserver on

"""

import re
import os
from os.path import join as joinpath

def multiwsgidispatch(wsgi_path, module_name):
    """Get a wsgi handler to do multiple dispatch.

    The handler uses the Host header to try to find a matching wsgi
    instance in the config['wsgi_path']
    """
    m = __import__(module_name, {}, {}, [""])
    def wsgi_dispatcher(environ, start_response):
        """Virtual host WSGI dispatcher"""
        host = environ["HTTP_HOST"]
        targetpart = host.split(".")[0]
        # Make a regex that will match against targets
        target_re = re.compile("%s.*" % re.sub("-", "[_-]", targetpart))
        for entry in os.listdir(wsgi_path):
            if target_re.match(entry):
                try:
                    path = joinpath(wsgi_path, entry)
                    return m.dispatch(path, environ, start_response)
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

import wsgiref.simple_server
RealServerHandler = wsgiref.simple_server.ServerHandler
class MServerHandler(RealServerHandler):
    def __init__(self, stdin, stdout, stderr, environ):
        RealServerHandler.__init__(
            self, 
            stdin, stdout, stderr, environ,
            multithread=False,
            multiprocess=True
            )

def main():
    conf = ConfigParser({"port": "9001"})
    try:
        conf.read(expanduser("~/.mswsgi.conf"))
    except:
        pass

    wsgiref.simple_server.ServerHandler = MServerHandler
    s = wsgiref.simple_server.make_server(
        "localhost", 
        int(conf.get("Server", "port")), 
        multiwsgidispatch(
            conf.get("Server", "wsgi_path"),
            conf.get("Server", "module_name")
            ),
        )
    s.serve_forever()

if __name__ == "__main__":
    main()

# End
