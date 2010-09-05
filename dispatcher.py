"""
A multiserver dispatcher for WooMe.com
"""

from os.path import join as joinpath
import os

def dispatch(path, environ, start_response):
    """Dispatch the wsgi call to the specified directory.

    At the moment this is WooMe specific. Seems like a candidate for
    plugin or something via the config file?
    """

    repopath = joinpath(path, "woome")
    os.chdir(repopath)

    import sys
    sys.path += [repopath]

    import config.importname
    conf = config.importname.get()
    cm = __import__("config.%s" % conf, {}, {}, [""])

    from os.path import basename
    reponame = basename(path).replace("_", "-")

    cm.STATIC_URL = 'http://%s.repos.dev.woome.com' % reponame
    cm.IMG_URL = 'http://%s.repos.dev.woome.com' % reponame
    cm.ENABLE_JS_MINIFY = False

    import settings
    try:
         sys.path = [settings.DJANGO_PATH_DIR] + sys.path
    except AttributeError:
         pass

    import django.core.management
    django.core.management.setup_environ(settings)

    import django.core.handlers.wsgi
    class SpawningDjangoWSGIHandler(django.core.handlers.wsgi.WSGIHandler):
        pass

    wsgi_handler = SpawningDjangoWSGIHandler()
    return wsgi_handler(environ, start_response)

# End
