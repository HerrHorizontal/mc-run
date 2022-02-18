import numpy as np

from matplotlib.ticker import LogFormatterSciNotation


def plot_as_step(ax, *args, **kwargs):
    """display data as horizontal bars with given by `x` +/- `xerr`. `y` error bars are also drawn."""
    assert len(args) == 2
    _x = np.ma.asarray(args[0])
    _y = np.ma.asarray(args[1])
    _zeros = np.zeros_like(_x)

    # kwarg `yerr_as_band` to display
    _show_yerr_as = kwargs.pop('show_yerr_as', None)
    if _show_yerr_as is not None and _show_yerr_as not in ('errorbar', 'band', 'hatch'):
        raise ValueError("Invalid value '{}' for 'show_yerr_as'. Available: {}".format(_show_yerr_as, ('errorbar', 'band', 'hatch')))

    assert 'xerr' in kwargs
    if len(kwargs['xerr']) == 1:
        _xerr_dn = _xerr_up = kwargs.pop('xerr')[0]
    else:
        _xerr_dn, _xerr_up = kwargs.pop('xerr')

    _yerr = kwargs.pop('yerr', None)
    if _yerr is not None:
        if len(_yerr) == 1:
            _yerr_dn = _yerr_up = _yerr[0]
        else:
            _yerr_dn, _yerr_up = _yerr
        _yerr_dn = np.asarray(_yerr_dn)
        _yerr_up = np.asarray(_yerr_up)

    _xerr_dn = np.asarray(_xerr_dn)
    _xerr_up = np.asarray(_xerr_up)

    # replicate each point five times -> bin anchors
    #  1 +       + 5
    #    |       |
    #    +---+---+
    #  2     3     4
    _x = np.ma.vstack([_x, _x, _x, _x, _x]).T.flatten()
    _y = np.ma.vstack([_y, _y, _y, _y, _y]).T.flatten()

    # stop processing y errors if they are zero
    if _yerr is None or np.allclose(_yerr, 0):
        _yerr = None

    # attach y errors (if any) to "bin" center
    if _yerr is not None:
        if _show_yerr_as in ('band', 'hatch'):
            # error band: shade across entire bin width
            _yerr_dn = np.vstack([_zeros, _yerr_dn, _yerr_dn, _yerr_dn, _zeros]).T.flatten()
            _yerr_up = np.vstack([_zeros, _yerr_up, _yerr_up, _yerr_up, _zeros]).T.flatten()
        else:
            # errorbars: only show on central point
            _yerr_dn = np.vstack([_zeros, _zeros, _yerr_dn, _zeros, _zeros]).T.flatten()
            _yerr_up = np.vstack([_zeros, _zeros, _yerr_up, _zeros, _zeros]).T.flatten()
        _yerr = [_yerr_dn, _yerr_up]

    # shift left and right replicas in x by xerr
    _x += np.vstack([-_xerr_dn, -_xerr_dn, _zeros, _xerr_up, _xerr_up]).T.flatten()

    # obtain indices of points with a binning discontinuity
    _bin_edge_discontinuous_at = (np.flatnonzero(_x[0::5][1:] != _x[4::5][:-1]) + 1)*5

    # prevent diagonal connections across bin discontinuities
    if len(_bin_edge_discontinuous_at):
        _x = np.insert(_x, _bin_edge_discontinuous_at, [np.nan])
        _y = np.insert(_y, _bin_edge_discontinuous_at, [np.nan])
        if _yerr is not None:
            _yerr = np.insert(_yerr, _bin_edge_discontinuous_at, [np.nan], axis=1)

    # do actual plotting
    if _show_yerr_as == 'errorbar' or _show_yerr_as is None:
        return ax.errorbar(_x, _y, yerr=_yerr if _show_yerr_as else None, **kwargs)
    elif _show_yerr_as == 'band':
        _band_alpha = kwargs.pop('band_alpha', 0.5)
        _hatch = kwargs.pop('band_hatch', None)
        _boundary = kwargs.pop('band_boundary', False)
        _capsize = kwargs.pop('capsize', None)
        _markeredgecolor = kwargs.pop('markeredgecolor', None)
        _color = kwargs.pop('color', None)
        _alpha = kwargs.pop('alpha', None)
        _linestyle = kwargs.pop('linestyle', None)

        _return_artists = []

        # compute boundary step
        _y_shifted = (_y.copy(), _y.copy())
        for _ys, _ye, _fac in zip(_y_shifted, _yerr, (-1.0, 1.0)):
            _ye = _ye.copy()
            # set shift size at bin anchors 0,4 to y error (only at bin anchors 1,2,3)
            _ye[0::5] = _ye[2::5]
            _ye[4::5] = _ye[2::5]
            _ys += _fac * _ye

        if _boundary:
            _return_artists.extend([
                ax.errorbar(_x, _y_shifted[0], yerr=None, capsize=_capsize, markeredgecolor=_markeredgecolor, color=_color, linestyle=_linestyle, **kwargs),
                ax.errorbar(_x, _y_shifted[1], yerr=None, capsize=_capsize, markeredgecolor=_markeredgecolor, color=_color, linestyle=_linestyle, **kwargs),
            ])

        if _yerr is None:
            _yerr = 0, 0

        _return_artists.extend([
            ax.errorbar(_x, _y, yerr=None, capsize=_capsize, markeredgecolor=_markeredgecolor, alpha=_alpha, color=_color, **kwargs),
            ax.fill_between(_x, _y_shifted[0], _y_shifted[1], **dict(kwargs, hatch=_hatch, alpha=_band_alpha, linewidth=0, color=_color))
            #ax.fill_between(_x, _y-_yerr[0], _y+_yerr[1], **dict(kwargs, alpha=_band_alpha, linewidth=0, hatch=_hatch, facecolor='none', color=None, edgecolor=kwargs.get('color')))
        ])

        return tuple(_return_artists)

    elif _show_yerr_as == 'hatch':
        raise NotImplementedError
        _band_alpha = kwargs.pop('band_alpha', 0.5)
        _hatch = kwargs.pop('hatch', '////')
        _capsize = kwargs.pop('capsize', None)
        _color = kwargs.pop('color', None)
        _alpha = kwargs.pop('alpha', None)
        _markeredgecolor = kwargs.pop('markeredgecolor', None)
        _linestyle = kwargs.pop('linestyle', None)  # invalid for hatch
        if _yerr is None:
            _yerr = 0, 0

        # compute boundary step
        _y_shifted = (_y.copy(), _y.copy())
        for _ys, _ye, _fac in zip(_y_shifted, _yerr, (-1.0, 1.0)):
            _ye = _ye.copy()
            # set shift size at bin anchors 0,4 to y error (only at bin anchors 1,2,3)
            _ye[0::5] = _ye[2::5]
            _ye[4::5] = _ye[2::5]
            _ys += _fac * _ye
        return (
            # central value
            ax.errorbar(_x, _y, yerr=None, capsize=_capsize, markeredgecolor=_markeredgecolor, color=_color, **kwargs),
            # limiting upper/lower edges of hatch
            ax.errorbar(_x, _y_shifted[0], yerr=None, capsize=_capsize, markeredgecolor=_markeredgecolor, color=_color, **kwargs),
            ax.errorbar(_x, _y_shifted[1], yerr=None, capsize=_capsize, markeredgecolor=_markeredgecolor, color=_color, **kwargs),
            # hatch
            ax.fill_between(_x, _y-_yerr[0], _y+_yerr[1], **dict(kwargs, hatch=_hatch, alpha=0.3, facecolor='r', edgecolor='yellow', linewidth=0, color=_color)))
            #ax.fill_between(_x, _y-_yerr[0], _y+_yerr[1], **dict(linestyle='solid', hatch=_hatch, facecolor='none', linewidth=0)))


class LogFormatterSciNotationForceSublabels(LogFormatterSciNotation):
    """Variant of LogFormatterSciNotation that always displays labels at
    certain non-decade positions. Needed because parent class may hide these
    labels based on axis spacing."""

    def __init__(self, *args, **kwargs):
        self._sci_min_exp = kwargs.pop('sci_min_exp', None)  # sci notation above, regular below
        self._sublabels_max_exp = kwargs.pop('sublabels_max_exp', None)  # no sublabels above exp
        super(LogFormatterSciNotationForceSublabels, self).__init__(*args, **kwargs)

    def set_locs(self, *args, **kwargs):
        '''override sublabels'''
        _ret = super(LogFormatterSciNotationForceSublabels, self).set_locs(*args, **kwargs)

        _locs = kwargs.pop("locs", None)

        # override locations
        _locs = kwargs.pop("locs", None)
        if _locs is not None:
            self._sublabels = _locs
        else:
            self._sublabels = {1.0, 2.0, 5.0, 10.0}

        return _ret

    def _non_decade_format(self, sign_string, base, fx, usetex):
        'Return string for non-decade locations'
        b = float(base)
        exponent = math.floor(fx)
        coeff = b ** fx / b ** exponent
        if is_close_to_int(coeff):
            coeff = np.round(coeff)
        if usetex:
            return (r'$%s%g\times%s^{%d}$') % \
                                        (sign_string, coeff, base, exponent)
        else:
            return ('$%s$' % _mathdefault(r'%s%g\times%s^{%d}' %
                                        (sign_string, coeff, base, exponent)))

    def __call__(self, x, pos=None):
        """
        Return the format for tick value *x*.
        The position *pos* is ignored.
        """
        usetex = mpl.rcParams['text.usetex']
        assert not usetex, "LogFormatterSciNotationForceSublabels does not (yet) support `text.usetex`"
        sci_min_exp = self._sci_min_exp #rcParams['axes.formatter.min_exponent']

        if x == 0:
            return '$0$'

        sign_string = '-' if x < 0 else ''
        x = abs(x)
        b = self._base

        # only label the decades
        fx = math.log(x) / math.log(b)
        is_x_decade = is_close_to_int(fx)
        exponent = np.round(fx) if is_x_decade else np.floor(fx)
        coeff = np.round(x / b ** exponent)
        if is_x_decade:
            fx = np.round(fx)

        if self.labelOnlyBase and not is_x_decade:
            return ''
        if self._sublabels is not None and coeff not in self._sublabels:
            return ''

        # use string formatting of the base if it is not an integer
        if b % 1 == 0.0:
            base = '%d' % b
        else:
            base = '%s' % b

        # TEMP: suppress minor ticks above threshold
        if not is_x_decade and self._sublabels_max_exp is not None and np.abs(fx) > self._sublabels_max_exp + 1:
            return ''

        if np.abs(fx) < sci_min_exp:
            return '${0}$'.format(_mathdefault(
                '{0}{1:g}'.format(sign_string, x)))
        elif not is_x_decade:
            return self._non_decade_format(sign_string, base, fx, usetex)
        else:
            return '$%s$' % _mathdefault('%s%s^{%d}' % (sign_string, base, fx))


