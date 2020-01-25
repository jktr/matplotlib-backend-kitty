# matplotlib-backend-kitty

This python module allows using your kitty terminal
as the target for Matplotlib's output (via icat).

To use it, add this module to your `$PYTHONPATH` and 
initialize matplotlib like this:

```python
import matplotlib
matplotlib.use('module://matplotlib-backend-kitty')
import matplotlib.pyplot as plt
```

You can then test it (from kitty) with something like
`>>> import pandas; pandas.Series(range(10)).plot()`.

Internally, it's based on the way Matplatlib output works
for IPython: it's a hybrid of image and GUI backends, piping
the Agg Backend's output to kitty's `icat` kitten. This
means that both `DataFrame.plot()` and `plt.show()` calls
will work as expected, but the image drawn to your terminal
isn't interactive and animations aren't supported.
