import numpy as np
import scipy.optimize as opt
from scipy import integrate


def scipy_fit(
    xVal, xErr, yVal, yErr, N_PARS=3, method="Nelder-Mead", max_chi2ndf=25, xrange=None
):
    """Fit function to data points.

    Args:
        xVal (numpy.array): x-positions of data points to fit
        yVal (numpy.array): y-positions of data points to fit
        yErr (numpy.array): uncertainty estimate in y of data points to fit
        N_PARS (int)      : complexity of model function
        method (str)      : optimizer method for fit


    Returns:
        dict: dictionary containing fitted function values/uncertainties at data points and evaluation metrics
    """

    N_PARS = N_PARS

    def model(x, pars):
        """model function"""
        if N_PARS == 3:
            a, b, c = pars
            return a * x ** (b) + c
        elif N_PARS == 2:
            a, b = pars
            return a * x ** (b) + 1
        elif N_PARS == 1:
            a, b = pars
            return a * x + b
        else:
            raise NotImplementedError(
                "No model function implemented for N_PARS={}".format(N_PARS)
            )

    def objective(pars):
        _int_val = np.zeros(xVal.shape)
        # use integral instead of evaluating at bin center
        # this is more accurate, especially in bins with a steep slope
        for _i, (_a, _b) in enumerate(zip(xErr[:, 0], xErr[:, 1])):
            _a = xVal[_i] - _a
            _b = xVal[_i] + _b
            _int_val[_i], _ = integrate.quad(lambda x: model(x, pars), _a, _b)
            _int_val[_i] /= np.abs(_b - _a)  # normalize to bin width
        _res = (_int_val - yVal) / yErr
        return np.sum(_res**2)

    def jac(pars):
        """Analytical gradient of objective function"""
        if N_PARS == 3:
            a, b, c = pars
            return np.array(
                [
                    np.sum(
                        2 * (a * (xVal ** (2 * b)) + (c - yVal) * (xVal**b)) / (yErr**2)
                    ),
                    np.sum(
                        2
                        * ((a**2) * (xVal ** (2 * b)) + a * (c - yVal) * (xVal**b))
                        * np.log(xVal)
                        / (yErr**2)
                    ),
                    np.sum(2 * (a * (xVal**b) + c - yVal) / (yErr**2)),
                ]
            )
        elif N_PARS == 2:
            a, b = pars
            return np.array(
                [
                    np.sum(
                        2 * (a * (xVal ** (2 * b)) + (1 - yVal) * (xVal**b)) / (yErr**2)
                    ),
                    np.sum(
                        2
                        * ((a**2) * (xVal ** (2 * b)) + a * (1 - yVal) * (xVal**b))
                        * np.log(xVal)
                        / (yErr**2)
                    ),
                ]
            )
        elif N_PARS == 1:
            a, b = pars
            return np.array(
                [
                    np.sum(2 * (a * (xVal**2) + (b - yVal) * xVal) / (yErr**2)),
                    np.sum(2 * (a * xVal + b - yVal) / (yErr**2)),
                ]
            )
        else:
            raise NotImplementedError(
                "Gradient for N_PARS={} not implemented".format(N_PARS)
            )

    def hess(pars):
        """Analytical hessian matrix of objective function"""
        if N_PARS == 3:
            a, b, c = pars
            return np.array(
                [
                    [
                        np.sum(2 * (xVal ** (2 * b)) / (yErr**2)),
                        np.sum(
                            2
                            * (2 * a * (xVal ** (2 * b)) + (c - yVal) * (xVal**b))
                            * np.log(xVal)
                            / (yErr**2)
                        ),
                        np.sum(2 * (xVal**b) / (yErr**2)),
                    ],
                    [
                        np.sum(
                            2
                            * (2 * a * (xVal ** (2 * b)) + (c - yVal) * (xVal**b))
                            * np.log(xVal)
                            / (yErr**2)
                        ),
                        np.sum(
                            2
                            * (
                                2 * (a**2) * (xVal ** (2 * b))
                                + a * (c - yVal) * (xVal**b)
                            )
                            * np.log(xVal)
                            * np.log(xVal)
                            / (yErr**2)
                        ),
                        np.sum(2 * a * (xVal**b) * np.log(xVal) / (yErr**2)),
                    ],
                    [
                        np.sum(2 * (xVal**b) / (yErr**2)),
                        np.sum(2 * a * (xVal**b) * np.log(xVal) / (yErr**2)),
                        np.sum(2 / yErr**2),
                    ],
                ]
            )
        elif N_PARS == 2:
            a, b = pars
            return np.array(
                [
                    [
                        np.sum(2 * (xVal ** (2 * b)) / (yErr**2)),
                        np.sum(
                            2
                            * (2 * a * (xVal ** (2 * b)) + (1 - yVal) * (xVal**b))
                            * np.log(xVal)
                            / (yErr**2)
                        ),
                    ],
                    [
                        np.sum(
                            2
                            * (2 * a * (xVal ** (2 * b)) + (1 - yVal) * (xVal**b))
                            * np.log(xVal)
                            / (yErr**2)
                        ),
                        np.sum(
                            2
                            * (
                                2 * (a**2) * (xVal ** (2 * b))
                                + a * (1 - yVal) * (xVal**b)
                            )
                            * np.log(xVal)
                            * np.log(xVal)
                            / (yErr**2)
                        ),
                    ],
                ]
            )
        elif N_PARS == 1:
            a, b = pars
            return np.array(
                [
                    [np.sum(2 * (xVal**2) / (yErr**2)), np.sum(2 * xVal / (yErr**2))],
                    [np.sum(2 * xVal / (yErr**2)), np.sum(2 / (yErr**2))],
                ]
            )
        else:
            raise NotImplementedError(
                "Hessian for N_PARS={} not implemented".format(N_PARS)
            )

    def fit_error(xVal, popt, pcov):
        """compute the uncertainty on the fitted function

        Args:
            xVal (np.ndarray): input space
            popt (np.ndarray): optimized model parameter values
            pcov (np.ndarray): Covariance matrix of the fit result
        """

        def jac(x, pars):
            """Jacobian vector of model function
            evaluated at parameter values pars
            """
            # from scipy.misc import derivative
            # return np.array(
            #     [derivative(,)]
            # )
            if N_PARS == 3:
                a, b, c = pars
                return np.array([x**b, a * np.log(x) * (x**b), np.ones(x.shape)])
            elif N_PARS == 2:
                a, b = pars
                return np.array([x**b, a * np.log(x) * (x**b)])
            elif N_PARS == 1:
                a, b = pars
                return np.array([x, np.ones(x.shape)])
            else:
                return NotImplementedError(
                    "No Jacobian vector implemented for model with N_PARS={}".format(
                        N_PARS
                    )
                )

        # print("jac: ", jac(xVal,popt).shape, jac(xVal,popt))
        # print("cov: ", pcov.shape, pcov)

        return np.sqrt(
            np.einsum(
                "j..., j... -> ...",
                np.einsum("i..., ij -> j...", jac(xVal, popt), pcov),
                jac(xVal, popt),
            )
        )

    # minimize function and take resulting azimuth
    if method not in ("Nelder-Mead", "trust-exact", "BFGS"):
        raise NotImplementedError(
            "Fitting with optimizer {} not implemented!".format(method)
        )

    if method in ("BFGS", "Nelder-Mead"):
        _jac = None
        _hess = None
        options = dict(maxiter=1e6)
    else:
        _jac = jac
        _hess = hess
        options = dict(maxiter=1e4, gtol=1e-3)

    def _fit(N_PARS=3, sign=1):
        if N_PARS == 3:
            result = opt.minimize(
                objective,
                x0=(sign * 10.0, -2.0, 1.0),
                bounds=((-np.inf, np.inf), (-1e2, 0), (0.5, 1.5)),
                tol=1e-6,
                method=method,
                jac=_jac,
                hess=_hess,
                options=options,
            )
        elif N_PARS == 2:
            result = opt.minimize(
                objective,
                x0=(sign * 10.0, -2.0),
                bounds=((-np.inf, np.inf), (-1e2, 0)),
                tol=1e-6,
                method=method,
                jac=_jac,
                hess=_hess,
                options=options,
            )
        elif N_PARS == 1:
            result = opt.minimize(
                objective,
                x0=(sign * 1, 1),
                bounds=((-np.inf, np.inf), (-np.inf, np.inf)),
                tol=1e-6,
                method=method,
                jac=_jac,
                hess=_hess,
                options=options,
            )
        else:
            raise NotImplementedError(
                "No optimization implemented for N_PARS={}".format(N_PARS)
            )
        return result

    def get_chi2ndf(result, xVal):
        return result.fun / (len(xVal) - len(result.x))

    result = _fit(N_PARS)
    chi2ndf = get_chi2ndf(result, xVal)
    best_result = result
    if not result.success or chi2ndf > max_chi2ndf:
        print("\n\tRetry fitting with new start point!\n")
        result = _fit(N_PARS, -1)
        chi2ndf = get_chi2ndf(result, xVal)
        if chi2ndf < get_chi2ndf(best_result, xVal):
            best_result = result

    # repeat fit with less complex model
    while not result.success or chi2ndf > max_chi2ndf:
        print("\n\tRetry fitting with less complex model!\n")
        N_PARS -= 1
        if N_PARS == 0:
            print("\n\tNo good fit found, using best result\n{}".format(best_result))
            result = best_result
            N_PARS = len(best_result.x)
            break
        result = _fit(N_PARS)
        if chi2ndf < get_chi2ndf(best_result, xVal):
            best_result = result
        chi2ndf = get_chi2ndf(result, xVal)
        if not result.success or chi2ndf > max_chi2ndf:
            result = _fit(N_PARS, -1)
            chi2ndf = get_chi2ndf(result, xVal)
            if chi2ndf < get_chi2ndf(best_result, xVal):
                best_result = result

    if method == "BFGS":
        covm = result.hess_inv
    else:
        try:
            covm = np.linalg.inv(hess(result.x))
        except np.linalg.LinAlgError:
            print("Singular matrix {}, try pseudo inverse".format(hess(result.x)))
            covm = np.linalg.pinv(hess(result.x))

    def get_model_str(N_PARS, pars):
        if N_PARS == 3:
            a, b, c = pars
            model = "${a:5.3f}x^{b:5.3f}+{c:5.3f}$".format(a=a, b=b, c=c)
        elif N_PARS == 2:
            a, b = pars
            model = "${a:5.3f}x^{b:5.3f}+1$".format(a=a, b=b)
        elif N_PARS == 1:
            a, b = pars
            model = "${a:5.3f}x+{b:5.3f}$".format(a=a, b=b)
        else:
            raise NotImplementedError(
                "No optimization implemented for N_PARS={}".format(N_PARS)
            )
        return model

    # interpolate the fit to 100 points for better plots
    x_line = np.logspace(np.log10(xVal.min()), np.log10(xVal.max()), 100)
    if xrange:
        x_line = np.logspace(np.log10(xrange[0]), np.log10(xrange[1]), 100)
    y_line = model(x_line, result.x)
    y_line_errs = fit_error(x_line, result.x, covm)

    return dict(
        # result=result,
        xs=x_line,
        pars=result.x,
        cov=covm,
        fitfunc=get_model_str(N_PARS, result.x),
        ys=y_line,
        yerrs=y_line_errs,
        chi2ndf=get_chi2ndf(result, xVal),
        chi2=result.fun,
        ndf=(len(xVal) - N_PARS),
    )


# EXPERIMENTAL: doesn't work, python3 required
# def minuit_fit(xVal, yVal, yErr):
#     from iminuit import Minuit

#     def model(x, a, b):
#         return a*np.power(x,b)+1

#     def least_squares(a,b):
#         _res = (model(xVal, a,b) - yVal) / yErr
#         return np.sum(_res**2)

#     try:
#         m = Minuit(least_squares, a=1, b=-1)
#     except:
#         import traceback
#         traceback.print_exc()
#     m.migrad()
#     m.hesse()

#     def fit_error(xVal, popt, pcov):
#         """compute the uncertainty on the fitted function

#         Args:
#             xVal (np.ndarray): input space
#             popt (np.ndarray): optimized model parameter values
#             pcov (np.ndarray): Covariance matrix of the fit result
#         """
#         def jac(x, pars):
#             """Jacobian vector of model function
#             evaluated at parameter values pars
#             """
#             a,b,c = pars
#             return np.array(
#                 [x**b,
#                 a*b*x**(b-1),
#                 np.ones(x.shape)]
#             )

#         print("jac: ", jac(xVal,popt).shape, jac(xVal,popt))
#         print("cov: ", pcov.shape, pcov)

#         return np.sqrt(
#             np.einsum("j..., j... -> ...", np.einsum("i..., ij -> j...", jac(xVal,popt), pcov), jac(xVal,popt))
#         )

#     return dict(
#         result=m,
#         pars=m.values,
#         cov=m.covariance,
#         ys=model(xVal, *m.values),
#         yerrs=fit_error(xVal, m.values, m.covariance),
#         chi2ndf=m.fmin.reduced_chi2,
#         chi2=m.fval, ndf=m.ndof
#     )


import kafe2


def exp_model(x, a=10.0, b=-2.0, c=1.0):
    ret = a * np.power(x, b, dtype=np.float128) + c
    return np.asarray(ret, dtype=np.float64)


def kafe2_fit(xVals, yVals, xErrs, yErrs, xrange=None):
    data = kafe2.XYContainer(xVals, yVals, dtype=np.float64)
    # Don't add x_errs, this is not the same as for a HistFit.
    # data.add_error("x", xErrs, correlation=0, relative=False)
    data.add_error("y", yErrs, correlation=0, relative=False)

    fit = kafe2.XYFit(
        data,
        model_function=exp_model,
    )
    fit_res = fit.do_fit()

    # interpolate the fit to 100 points for better plots
    x_line = np.logspace(np.log10(xVals.min()), np.log10(xVals.max()), 100)
    if xrange:
        x_line = np.logspace(np.log10(xrange[0]), np.log10(xrange[1]), 100)

    y_line = fit.eval_model_function(x_line)
    y_line_errs = fit.error_band(x_line)
    print(fit_res)

    return dict(
        xs=x_line,
        pars=np.array(list(fit_res["parameter_values"].values())),
        cov=fit_res["parameter_cov_mat"],
        fitfunc=fit.model_function.formatter.get_formatted(
            with_par_values=True, with_expression=True
        ),
        ys=y_line,
        yerrs=y_line_errs,
        chi2ndf=fit_res["gof/ndf"],
        chi2=fit_res["goodness_of_fit"],
        ndf=fit_res["ndf"],
    )


# from scipy.misc import derivative


# def kafe2_hist_fit(bin_edges, bin_values, bin_errors, xrange=None):
#     fit_func = exp_model
#     data = kafe2.HistContainer(bin_edges=bin_edges, dtype=float)
#     data.set_bins(bin_values)
#     data.add_error(bin_errors, correlation=0, relative=False)
#     # Don't add x_errs, this is not the same as for a HistFit.
#     # data.add_error("x", xErrs, correlation=0, relative=False)

#     fit = kafe2.HistFit(
#         data,
#         model_function=fit_func,
#         density=False,
#         cost_function="chi2",
#     )
#     fit.limit_parameter(
#         "b",
#         lower=-1e2,
#         upper=0.0,
#     )
#     fit.limit_parameter(
#         "c",
#         lower=-10,
#         upper=10,
#     )
#     fit_res = fit.do_fit()
#     print(fit_res)

#     # interpolate the fit to 100 points for better plots
#     x_line = np.logspace(np.log10(bin_edges.min()), np.log10(bin_edges.max()), 100)
#     if xrange:
#         x_line = np.logspace(np.log10(xrange[0]), np.log10(xrange[1]), 100)

#     y_line = fit.eval_model_function_density(x_line)
#     print(fit.parameter_cov_mat)
#     if np.isnan(fit.parameter_cov_mat).any():
#         raise ValueError("Covariance matrix contains nan values")

#     def eval_model_function_derivative_by_parameters(fit, x):
#         _pars = np.asarray(fit.parameter_values).copy()
#         _par_dxs = 1e-2 * np.asarray(fit.parameter_errors).copy()
#         _ret = np.zeros((len(_pars), len(x)))
#         for _par_idx, (_par_val, _par_dx) in enumerate(zip(_pars, _par_dxs)):

#             def _chipped_func(par):
#                 _chipped_pars = _pars.copy()
#                 _chipped_pars[_par_idx] = par
#                 return fit_func(x, *_chipped_pars)

#             _der_val = np.array(derivative(_chipped_func, _par_val, dx=_par_dx))
#             _ret[_par_idx] = _der_val
#         return _ret

#     def error_band(fit, x):
#         _f_deriv_by_params = eval_model_function_derivative_by_parameters(fit, x)
#         _f_deriv_by_params = _f_deriv_by_params.T
#         # here: df/dp[par_idx]|x=x[x_idx] = _f_deriv_by_params[x_idx][par_idx]
#         _band_y = np.zeros_like(x)

#         # Cut out fixed parameters which have nan as derivative:
#         _cov_mat = np.asarray(fit.parameter_cov_mat).copy()
#         _cov_mat = np.diag(_cov_mat)
#         for _x_idx, _x_val in enumerate(x):
#             _p_res = _f_deriv_by_params[_x_idx]
#             _band_y[_x_idx] = _p_res.dot(_cov_mat).dot(_p_res)

#         return np.sqrt(_band_y)

#     y_line_errs = error_band(fit, x_line)

#     return dict(
#         xs=x_line,
#         pars=np.array(list(fit_res["parameter_values"].values())),
#         cov=fit_res["parameter_cov_mat"],
#         fitfunc=fit.model_function.formatter.get_formatted(
#             with_par_values=True, with_expression=True
#         ),
#         ys=y_line,
#         yerrs=y_line_errs,
#         chi2ndf=fit_res["gof/ndf"],
#         chi2=fit_res["goodness_of_fit"],
#         ndf=fit_res["ndf"],
#     )
