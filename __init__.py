# SPDX-License-Identifier: CC0-1.0

import os
import sys

from io import BytesIO
from subprocess import run

from matplotlib import interactive, is_interactive
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import (_Backend, FigureManagerBase)
from matplotlib.backends.backend_agg import FigureCanvasAgg


# XXX heuristic for interactive repl
if sys.flags.interactive:
    interactive(True)


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
        tput = __class__._run('tput')
        icat = __class__._run('kitty', '+kitten', 'icat')

        # gather terminal dimensions
        rows = int(tput('lines'))
        px = icat('--print-window-size')
        px = list(map(int, px.split('x')))

        # account for post-display prompt scrolling
        # 3 line shift for [\n, <matplotlib.axes…, >>>] after the figure
        px[1] -= int(3*(px[1]/rows))

        # resize figure to terminal size & aspect ratio
        dpi = self.canvas.figure.dpi
        self.canvas.figure.set_size_inches((px[0] / dpi, px[1] / dpi))

        with BytesIO() as buf:
            self.canvas.figure.savefig(buf, format='png', facecolor='#888888')
            icat('--align', 'left', output=False, input=buf.getbuffer())


@_Backend.export
class _BackendICatAgg(_Backend):

    FigureCanvas = FigureCanvasAgg
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
