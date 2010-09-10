"""
A multiserver dispatcher for WooMe.com
"""

from os.path import join as joinpath
import os

def dispatch(path, target_pattern, environ, start_response):
    """Dispatch the wsgi call to the WooMe instance in the specified directory.

    This only handles ticket repos of course.
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

    cm.STATIC_URL = target_pattern % reponame
    cm.IMG_URL = target_pattern % reponame
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
