# SPDX-License-Identifier: CC0-1.0

from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import (
    _Backend, FigureCanvasBase, FigureManagerBase)
from matplotlib.backends.backend_agg import FigureCanvasAgg

import subprocess

class FigureManagerICat(FigureManagerBase):
    def show(self):
        tmp = f'/tmp/fig-{self.num}.png'
        self.canvas.figure.savefig(tmp, format='png')
        subprocess.run(['kitty', '+kitten', 'icat', '--align=left', tmp])


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
