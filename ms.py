#!/usr/bin/python

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
  port         the port to start the multiserver on (default: 9001)

"""

import re
import os
from os.path import join as joinpath

def multiwsgidispatch(wsgi_path, module_name, target_pattern):
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
                    return m.dispatch(path, target_pattern, environ, start_response)
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

from SocketServer import ForkingMixIn
class WSGIServerForking(ForkingMixIn, wsgiref.simple_server.WSGIServer):
    """A forking WSGI server"""
    pass

def server(conf):
    """Run the server"""
    wsgiref.simple_server.ServerHandler = MServerHandler
    s = wsgiref.simple_server.make_server(
        "localhost", 
        int(conf.get("Server", "port")), 
        multiwsgidispatch(
            conf.get("Server", "wsgi_path"),
            conf.get("Server", "module_name"),
            conf.get("Server", "target_pattern"),
            ),
        server_class=WSGIServerForking
        )
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)



# Some lifecycle methods for standard unix server stuff
import daemon
import sys
import signal

DEFAULT_PIDFILE="/tmp/multiserver.pid"
def lifecycle_cleanup():
    """Terminate the process nicely."""
    sys.exit(0)

def lifecycle_start(conf):
    with daemon.DaemonContext() as dctx:
        # Write the pid
        with open(conf.get("Server", "pidfile", DEFAULT_PIDFILE), "w") as pidfile:
            pidfile.write("%s\n" % os.getpid())

        # Set the signal map
        dctx.signal_map = {
            signal.SIGTERM: lifecycle_cleanup,
            }
        server(conf)

def lifecycle_stop(conf):
    with open(conf.get("Server", "pidfile", DEFAULT_PIDFILE)) as pidfile:
        pid = pidfile.read()
        try:
            os.kill(int(pid), signal.SIGTERM)
        except Exception, e:
            print >>sys.stderr, "couldn't stop %s" % pid

def lifecycle_status(conf):
    with open(conf.get("Server", "pidfile", DEFAULT_PIDFILE)) as pidfile:
        pid = pidfile.read()
        print pid


def main():
    from optparse import OptionParser
    usage = "%prog [options] [start|stop|status|help]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        '-c', 
        '--config', 
        dest='config',
        default="~/.mswsgi.conf",
        help="configuration file"
        )
    parser.add_option(
        '-D', 
        '--no-daemon', 
        dest='nodaemon',
        action="store_true",
        help="disable daemonification if specified in config"
        )
    options, args = parser.parse_args()

    if "help" in args:
        parser.print_help()
        sys.exit(0)

    conf = ConfigParser({"port": "9001"})
    try:
        conf.read(expanduser("~/.mswsgi.conf"))
    except:
        pass

    if "start" in args:
        try:
            if not(options.nodaemon):
                lifecycle_start(conf)
            else:
                raise AttributeError("no daemon")
        except AttributeError:
            # Just run then
            server(conf)

    elif "stop" in args:
        lifecycle_stop(conf)

    elif "status" in args:
        lifecycle_status(conf)

    elif "run" in args:
        server(conf)



if __name__ == "__main__":
    main()

# End
