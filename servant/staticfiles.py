
# The only HTML file we serve that isn't a template, index.html, should have an
# etag and be checked each time.  Items inside all have a version as part of the
# filename, so reloading this one HTML file updates the site.
#
# All vendor files should have the version manually appended when adding to the
# project or upgrading versions.
#
# To ensure an incremental build that only updates one of the generated files
# works, the build scripts should always regenerate the index HTML too.

from os.path import isdir, splitext, abspath, join, exists, isabs
from logging import getLogger
from .errors import HttpError

logger = getLogger('static')

map_ext_to_mime = {
    '.css'  : 'text/css',
    '.gif'  : 'image/gif' ,
    '.html' : 'text/html',
    '.js'   : 'text/javascript',
    '.map'  : 'application/json',
    '.png'  : 'image/png',
    '.woff' : 'application/font-woff',
}

map_key_to_path = {}
# Maps from key (e.g. "generated") to the path.

map_path_to_cache = {}
# Maps from (key, relpath) to http.File entry.


class File:
    def __init__(self, relpath, mimetype, content):
        self.relpath    = relpath
        self.mimetype   = mimetype
        self.content    = content
        self.compressed = False # True if gzipped


def register_key(key, path):
    assert isabs(path), 'static file key {} path {!r} is not absolute'.format(key, path)
    assert isdir(path), 'static file key {} path {!r} does not exist'.format(key, path)
    map_key_to_path[key] = path


def get_key(key):
    return map_key_to_path[key]


def get(key, relpath):
    entry = map_path_to_cache.get(relpath)

    assert key in map_key_to_path, key + ' is not registered'
    root = map_key_to_path[key]

    if not entry:
        fqn = abspath(join(root, relpath))
        if not exists(fqn):
            logger.debug('Not found: url=%r fqn=%r', relpath, fqn)
            raise HttpError(404, relpath)

        # TODO: Do more security checking.  Or consider reading the potential files
        # on startup and only matching those directly.

        ext = splitext(relpath)[1]
        if ext not in map_ext_to_mime:
            raise Exception('No mimetype for "{}" (from {!r})'.format(ext, relpath))

        content = open(fqn, 'rb').read()
        entry = File(relpath, map_ext_to_mime[ext], content)

        map_path_to_cache[relpath] = entry

    return entry
