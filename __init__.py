# SPDX-License-Identifier: CC0-1.0

from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import (
    _Backend, FigureCanvasBase, FigureManagerBase)
from matplotlib.backends.backend_agg import FigureCanvasAgg

from io import BytesIO
from subprocess import run

class FigureManagerICat(FigureManagerBase):
    def show(self):

        def run_with_output(cmd):
            def f(args, **kwargs):
                r = run(cmd + args, **kwargs, capture_output=True, text=True)
                return r.stdout.rstrip()
            return f

        tput = run_with_output(['tput'])
        icat = ['kitty', '+kitten', 'icat']

        # gather terminal dimensions
        cols = int(tput(['cols']))
        rows = int(tput(['lines']))
        px = run_with_output(icat)(['--print-window-size'])
        px = list(map(int, px.split('x')))

        # account for post-display prompt scrolling
        px[1] -= int(1*(px[1]/rows))
        rows = int(tput(['lines'])) - 1

        # resize figure to terminal size
        dpi = self.canvas.figure.dpi
        self.canvas.figure.set_size_inches(tuple(map(lambda x: (x / dpi), px)))

        with BytesIO() as buf:
            self.canvas.figure.savefig(buf, format='png',
                                       facecolor='#ffffff7f', transparent=True)

            run(icat + ['--clear', '--place', f'{cols}x{rows}@0x0'],
                input=buf.getbuffer())


@_Backend.export
class _BackendICatAgg(_Backend):
    FigureCanvas = FigureCanvasAgg
    FigureManager = FigureManagerICat

    def _icat_draw():
        manager = Gcf.get_active()
        if manager:
            manager.show()
        Gcf.destroy_all()

    def draw_if_interactive(*args, **kwargs):
        __class__._icat_draw()

    def show(*args, **kwargs):
        __class__._icat_draw()
