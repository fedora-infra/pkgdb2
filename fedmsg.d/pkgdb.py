""" This is an example pkgdb configuration for fedmsg.
By convention, it is normally installed as ``/etc/fedmsg.d/pkgdb.py``

For Fedora Infrastructure this file is not needed as we use dynamic
fedmsg endpoints.

It needs to be globally available so remote consumers know how to find the
pkgdb producer (wsgi process).
"""

import socket
hostname = socket.gethostname().split('.')[0]

config = dict(
    endpoints={
        "pkgdb2.%s" % hostname: [
            "tcp://127.0.0.1:3005",
        ],
    },
)
