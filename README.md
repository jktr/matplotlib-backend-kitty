# matplotlib-backend-kitty

This python module allows using your kitty terminal
as the target for Matplotlib's output (via icat).

To use it, add this module to your `$PYTHONPATH` and 
initialize matplotlib/pandas like this:

```python
import numpy as np
import matplotlib; matplotlib.use('module://matplotlib-backend-kitty')
import matplotlib.pyplot as plt; plt.ion()
import pandas as pd
```

You can then test it (from kitty) with something
like `>>> pd.Series(range(10)).plot()`.

Internally, it's based on the way Matplatlib output works for IPython.
It works by piping the Agg Backend's output to kitty's `icat` kitten
and faking an IPython-like interactive environment.
