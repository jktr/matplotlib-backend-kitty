# SPDX-License-Identifier: CC0-1.0

import subprocess

import matplotlib.backends.backend_agg as agg

from matplotlib import is_interactive
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import (
    _Backend, FigureCanvasBase, FigureManagerBase)

class FigureManagerICat(FigureManagerBase):
    def show(self):
        if not getattr(self, '_workaround', False):
            self._workaround = True
            return True

        tmp = '/tmp/fig.png'
        self.canvas.figure.savefig(tmp, format='png')
        subprocess.run(['kitty', '+kitten', 'icat', '--align=left', tmp])
        
@_Backend.export
class _BackendICatAgg(_Backend):
    FigureCanvas = agg.FigureCanvasAgg
    FigureManager = FigureManagerICat

    trigger_manager_draw = lambda manager: _BackendICatAgg.show()

    @staticmethod
    def show(*args, block=None, **kwargs):
        interactive = is_interactive()
        workaround = False
        for manager in Gcf.get_all_fig_managers():
            workaround = workaround or manager.show()
            if hasattr(manager, '_cidgcf'):
                manager.canvas.mpl_disconnect(manager._cidgcf)
            if not interactive and manager in Gcf._activeQue:
                Gcf._activeQue.remove(manager)
        if not workaround and interactive:
            Gcf.destroy_all()
