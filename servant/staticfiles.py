
# The only HTML file we serve that isn't a template, index.html, should have an
# etag and be checked each time.  Items inside all have a version as part of the
# filename, so reloading this one HTML file updates the site.
#
# All vendor files should have the version manually appended when adding to the
# project or upgrading versions.
#
# To ensure an incremental build that only updates one of the generated files
# works, the build scripts should always regenerate the index HTML too.

# WARNING
# -------
#
# Python's asyncio does not have an asynchronous way to read files because operating systems
# don't really support it.  Apparently *nix systems have the API (select with file descriptors)
# but they always report themselves ready and therefore end up blocking anyway.
#
# Python will soon (or may already) support an asynchronous sendfile, which would could try to
# use.
#
# To work around this, we'll simply cache the files in memory.  Due to reference counting,
# Python is usually very good with memory.  The library is really designed for single page
# applications where resources are cached at the browser for a year.  (Put your version number
# on the end!)

# TODO ITEMS
# ----------
#
# We have not implemented compression yet.  I don't believe there are any modern browsers that
# don't support gzip, so we should only support compression and hold the compressed version in
# memory.
#
# Add a way to register mimetypes.  (Or perhaps use a module that already has them?)

import re, gzip
from os.path import isdir, splitext, abspath, join, exists, isabs
from logging import getLogger
from .errors import HttpError
from asyncio import coroutine
from collections import namedtuple

from .routing import Route, register_route

use_cache = True

logger = getLogger('static')

Ext = namedtuple('Ext', 'mimetype compress')
map_ext_to_mime = {
    '.css'  : Ext('text/css', True),
    '.eot'  : Ext('application/vnd.ms-fontobject', True),
    '.gif'  : Ext('image/gif' , False),
    '.html' : Ext('text/html', True),
    '.ico'  : Ext('image/ico', False),
    '.jpe'  : Ext('image/jpeg', False),
    '.jpeg' : Ext('image/jpeg', False),
    '.jpg'  : Ext('image/jpeg', False),
    '.js'   : Ext('text/javascript', True),
    '.map'  : Ext('application/json', True),
    '.otf'  : Ext('application/x-font-otf', True),
    '.png'  : Ext('image/png', False),
    '.svg'  : Ext('image/svg', True),
    '.svgz' : Ext('image/svgz', True),
    '.ttf'  : Ext('application/x-font-ttf', True),
    '.woff' : Ext('application/font-woff', False),
    '.woff2': Ext('application/font-woff2', False)
}

map_prefix_to_path = {}
# Maps from URL prefix (e.g. "/static") to the fully-qualified path we
# should load files from.  By default all files with extensions in
# map_ext_to_mime are loaded from the path or any subdirectory of the
# path.

map_path_to_cache = {}
# Maps from fully-qualified filename to a cached http.File entry.

class File:
    def __init__(self, relpath, mimetype, content, compressed):
        self.relpath    = relpath
        self.mimetype   = mimetype
        self.content    = content
        self.compressed = compressed # True if gzipped
        self.etag       = None


class StaticFileRoute(Route):
    """
    A route for serving static files from the static file cache.
    """
    def __init__(self, prefix, route_keywords=None):
        Route.__init__(self, route_keywords=route_keywords)

        self.prefix = prefix

        if not prefix[:-1] == '/':
            prefix += '/'

        self.regexp = re.compile('^' + re.escape(prefix) + '(.+)')

    def __repr__(self):
        return 'StaticFileRoute<%s>' % self.prefix

    @coroutine
    def __call__(self, match, ctx):
        relpath = match.group(1)
        return get(self.prefix, relpath)


def register_file_type(ext, mimetype=None, compress=None):
    map_ext_to_mime[ext] = Ext(mimetype=mimetype, compress=compress)


def serve_prefix(prefix, path, **route_keywords):
    """
    Registers a URL prefix (e.g. "/images") with a directory.  Any URLs starting with this
    prefix will serve files from the given path or below.

    route_keywords
      Route keywords.  These are attached to the route for use by middleware.
    """
    assert isabs(path), 'static path {!r} for prefix {} is not absolute'.format(path, prefix)
    assert isdir(path), 'static path {!r} for prefix {} does not exist'.format(path, prefix)
    map_prefix_to_path[prefix] = path
    register_route(StaticFileRoute(prefix, route_keywords=route_keywords))


def path_from_prefix(prefix):
    """
    Return the directory that files for the given URL prefix are being
    served from.
    """
    path = map_prefix_to_path.get(prefix)
    if not path:
        raise Exception('The prefix {!r} is not being served'.format(prefix))
    return path

def get(prefix, relpath):
    """
    Returns an http.File object for the given URL prefix and path from that prefix.
    """

    entry = map_path_to_cache.get(relpath) if use_cache else None

    assert prefix in map_prefix_to_path, "Prefix {!r} is not registered".format(prefix)
    root = map_prefix_to_path[prefix]

    if not entry:
        fqn = abspath(join(root, relpath))
        if not exists(fqn):
            logger.debug('Not found: url=%r fqn=%r', relpath, fqn)
            raise HttpError(404, relpath)

        if fqn[:len(root)] != root:
            # This means someone used ".." to try to move up out of the static directory.  This
            # very well may be a hack attempt.

            logger.error('SECURITY: Dangerous path in file download?  prefix=%s root=%s relpath=%s fqn=%s',
                         prefix, root, relpath, fqn)
            raise HttpError(404, relpath)

        ext = splitext(relpath)[1]
        if ext not in map_ext_to_mime:
            raise Exception('No mimetype for "{}" (from {!r})'.format(ext, relpath))

        content = open(fqn, 'rb').read()
        extinfo = map_ext_to_mime[ext]

        if extinfo.compress:
            # compress using gzip
            content = gzip.compress(content)

        entry = File(relpath, extinfo.mimetype, content, extinfo.compress)

        if use_cache:
            map_path_to_cache[relpath] = entry

    return entry
