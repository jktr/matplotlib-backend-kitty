# SPDX-License-Identifier: CC0-1.0

import array
import fcntl
import os
import re
import sys

from io import BytesIO
import termios
import tty
from base64 import standard_b64encode
from contextlib import suppress
from subprocess import run

from matplotlib import interactive, is_interactive
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import (_Backend, FigureManagerBase)
from matplotlib.backends.backend_agg import FigureCanvasAgg


# XXX heuristic for interactive repl
if hasattr(sys, 'ps1') or sys.flags.interactive:
    interactive(True)

def term_size_px():
    width_px = height_px = 0

    # try to get terminal size from ioctl
    with suppress(OSError):
        buf = array.array('H', [0, 0, 0, 0])
        fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, buf)
        _, _, width_px, height_px = buf

    if width_px != 0 and height_px != 0:
        return height_px, width_px

    # fallback to ANSI escape code if ioctl fails
    buf = ''
    stdin = sys.stdin.fileno()
    tattr = termios.tcgetattr(stdin)

    try:
        tty.setcbreak(stdin, termios.TCSANOW)
        sys.stdout.write('\x1b[14t')
        sys.stdout.flush()

        while True:
            buf += sys.stdin.read(1)
            if buf[-1] == 't':
                break

    finally:
        termios.tcsetattr(stdin, termios.TCSANOW, tattr)

    # reading the actual values, but what if a keystroke appears while reading
    # from stdin? As dirty work around, getpos() returns if this fails: None
    try:
        matches = re.match(r'^\x1b\[4;(\d*);(\d*)t', buf)
        groups = matches.groups()
    except AttributeError:
        return None

    return (int(groups[0]), int(groups[1]))


def serialize_gr_command(**cmd):
    payload = cmd.pop('payload', None)
    cmd = ','.join(f'{k}={v}' for k, v in cmd.items())
    ans = []
    w = ans.append
    w(b'\033_G'), w(cmd.encode('ascii'))
    if payload:
        w(b';')
        w(payload)
    w(b'\033\\')
    return b''.join(ans)


def write_chunked(**cmd):
    data = standard_b64encode(cmd.pop('data'))
    while data:
        chunk, data = data[:4096], data[4096:]
        m = 1 if data else 0
        sys.stdout.buffer.write(serialize_gr_command(payload=chunk, m=m, **cmd))
        sys.stdout.flush()
        cmd.clear()

class FigureManagerICat(FigureManagerBase):

    @classmethod
    def _run(cls, *cmd):
        def f(*args, output=True, **kwargs):
            if output:
                kwargs['capture_output'] = True
                kwargs['text'] = True
            r = run(cmd + args, **kwargs)
            if output:
                return r.stdout.rstrip()
        return f

    def show(self):
        if os.environ.get('MPLBACKEND_KITTY_SIZING', 'automatic') != 'manual':

            # gather terminal dimensions
            term_height_px, term_width_px = term_size_px()

            # resize figure to terminal size & aspect ratio
            ipd = 1 / self.canvas.figure.dpi
            term_width_inch, term_height_inch = term_width_px * ipd, term_height_px * ipd
            self.canvas.figure.set_size_inches(term_width_inch, term_height_inch)

        with BytesIO() as buf:
            self.canvas.figure.savefig(buf, format='png')
            write_chunked(a='T', f=100, data=buf.getvalue())


class FigureCanvasICat(FigureCanvasAgg):
    manager_class = FigureManagerICat


@_Backend.export
class _BackendICatAgg(_Backend):

    FigureCanvas = FigureCanvasICat
    FigureManager = FigureManagerICat

    # Noop function instead of None signals that
    # this is an "interactive" backend
    mainloop = lambda: None

    # XXX: `draw_if_interactive` isn't really intended for
    # on-shot rendering. We run the risk of being called
    # on a figure that isn't completely rendered yet, so
    # we skip draw calls for figures that we detect as
    # not being fully initialized yet. Our heuristic for
    # that is the presence of axes on the figure.
    @classmethod
    def draw_if_interactive(cls):
        manager = Gcf.get_active()
        if is_interactive() and manager.canvas.figure.get_axes():
            cls.show()

    @classmethod
    def show(cls, *args, **kwargs):
        _Backend.show(*args, **kwargs)
        Gcf.destroy_all()
