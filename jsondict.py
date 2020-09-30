# -*- coding: utf-8 -*-
'''
jsondict
========
Dict with json file saving / restoring support

- datetime, date support
- readable formated json
- safely file write with file move os function
- auto-save support
- compression support

Install
-------
    pip install jsondict

Usage
-----
    >>> from datetime import datetime
    >>> from jsondict import JsonDict
    >>> db = JsonDict('var/test.json')
    >>> db.clear()
    >>> db.update({'b': 2, 'created': datetime(2013, 1, 27, 21, 14), 'a': 1})
    >>> db.save()
    >>> open(db.filename).read()
    '{\\n  "a": 1,\\n  "b": 2,\\n  "created": "2013-01-27T21:14:00Z"\\n}'

Auto-save and compression
-------------------------
    >>> import gzip
    >>> db = JsonDict('var/test.json.gz', compress=True, autosave=True)
    >>> db.clear()
    >>> db['x'] = 'y'
    >>> gzip.open(db.filename).read()
    '{\\n  "x": "y"\\n}'
'''
import os
import gzip
import shutil
import tempfile

import json


__version__ = '1.21'


class JsonDict(dict):
    '''
    Base operations:

        >>> db = JsonDict('var/test.json')
        >>> db.clear()
        >>> db['a'] = 1
        >>> db.save()
        >>> open(db.filename).read()
        '{\\n  "a": 1\\n}'

        >>> db = JsonDict('var/test.json')
        >>> db['a']
        1

    Autosave:

        >>> db = JsonDict('var/test.json', autosave=True)
        >>> db.clear()
        >>> open(db.filename).read()
        '{}'
        >>> db.update({'a': 1, 'b': 2})
        >>> open(db.filename).read()
        '{\\n  "a": 1,\\n  "b": 2\\n}'
        >>> db['c'] = 3
        >>> open(db.filename).read()
        '{\\n  "a": 1,\\n  "b": 2,\\n  "c": 3\\n}'
        >>> del db['a']
        >>> open(db.filename).read()
        '{\\n  "b": 2,\\n  "c": 3\\n}'

    Compress:

        >>> db = JsonDict('var/test.json.gz', autosave=True)
        >>> db.compress
        True
        >>> db.clear()
        >>> db['a'] = 1
        >>> gzip.open(db.filename).read()
        '{\\n  "a": 1\\n}'

    Unsafely write:

        >>> db = JsonDict('var/test.json', safely_write=False)
        >>> db.clear()
        >>> db['a'] = 1
        >>> db.save()
        >>> open(db.filename).read()
        '{\\n  "a": 1\\n}'

    Unicode keys:

        >>> db = JsonDict('var/test.json')
        >>> db[u'ыыы'] = 1
        >>> db.save()
        >>> db = JsonDict('var/test.json')
        >>> db[u'ыыы']
        1

    '''
    def __init__(self, filename, autosave=False, compress=None,
            safely_write=True, *args, **kwargs):
        super(JsonDict, self).__init__(*args, **kwargs)
        self.filename = filename
        self.autosave = autosave
        self.compress = (compress if compress is not None
                else filename.endswith('.gz'))
        self.safely_write = safely_write
        self.open = gzip.open if self.compress else open
        if os.path.isfile(self.filename):
            self.load()

    def __setitem__(self, name, val):
        super(JsonDict, self).__setitem__(name, val)
        if self.autosave:
            self.save()

    def __delitem__(self, name):
        super(JsonDict, self).__delitem__(name)
        if self.autosave:
            self.save()

    def clear(self):
        super(JsonDict, self).clear()
        if self.autosave:
            self.save()

    def update(self, *args, **kwargs):
        super(JsonDict, self).update(*args, **kwargs)
        if self.autosave:
            self.save()

    def load(self):
        dump = self.open(self.filename).read()
        data = json.loads(dump)
        self.clear()
        self.update(data)

    def save(self):
        makedirs(self.filename)
        dump = self.to_json()
        if self.safely_write:
            safely_write(self.filename, dump, self.compress)
        else:
            self.open(self.filename, 'w').write(dump)

    def to_json(self):
        dump = json.dumps(dict(self))
        return dump

    def __str__(self):
        return self.to_json()


def makedirs(filename):
    dirname = os.path.dirname(filename)
    if dirname:
        try:
            os.makedirs(dirname)
        except OSError:
            pass

def safely_write(filename, data, compress):
    dirname = os.path.dirname(filename)
    suffix = '.' + os.path.basename(filename)
    fd, tmp_fn = tempfile.mkstemp(dir=dirname, suffix=suffix)
    f = os.fdopen(fd, 'w')
    if compress:
        gf = gzip.GzipFile(fileobj=f)
        gf.write(data)
        gf.close()
    else:
        f.write(data)
    f.close()
    try:
        shutil.move(tmp_fn, filename)
    except IOError:
        os.unlink(tmp_fn)
        raise

if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
