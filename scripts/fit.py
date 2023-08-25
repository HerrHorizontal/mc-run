
import scipy.optimize as opt
import numpy as np


def scipy_fit(xVal, yVal, yErr, N_PARS=2):
    """Fit function to ratio points."""

    N_PARS = N_PARS
    def model(x, pars):
        """model function"""
        if N_PARS == 3:
            a,b,c = pars
            return a*x**(b) + c
        elif N_PARS == 2:
            a,b, = pars
            return a*x**(b) + 1
        else:
            raise NotImplementedError("No model function implemented for N_PARS={}".format(N_PARS))

    def objective(pars):
        _res = (model(xVal, pars) - yVal) / yErr
        return np.sum(_res**2)
    
    def jac(pars):
        """gradient of objective function"""
        if N_PARS == 3:
            a,b,c = pars
            return np.array(
                [np.sum(xVal**(2*b)/yErr**2),
                    np.sum(a**2*b**2*xVal**(2*b-2)/yErr**2),
                    np.sum(1/yErr**2)]
            )
        elif N_PARS == 2:
            a,b = pars
            return np.array(
                [np.sum(xVal**(2*b)/yErr**2),
                    np.sum(a**2*b**2*xVal**(2*b-2)/yErr**2)]
            )
        else:
            raise NotImplementedError("Gradient for N_PARS={} not implemented".format(N_PARS))

    def hess(pars):
        if N_PARS == 3:
            a,b,c = pars
            return np.array(
                [[0, np.sum(2*np.log(xVal)*xVal**(2*b)/yErr**2), 0],
                [np.sum(2*np.log(xVal)*xVal**(2*b)/yErr**2), np.sum(2*a**2*b*xVal**(2*b-2)*(b*np.log(xVal)+1)/yErr**2), 0],
                [0, 0, 0]]
            )
        elif N_PARS == 2:
            a,b = pars
            return np.array(
                [[0, np.sum(2*np.log(xVal)*xVal**(2*b)/yErr**2)],
                [np.sum(2*np.log(xVal)*xVal**(2*b)/yErr**2), np.sum(2*a**2*b*xVal**(2*b-2)*(b*np.log(xVal)+1)/yErr**2)]]
            )
        else:
            raise NotImplementedError("Hessian for N_PARS={} not implemented".format(N_PARS))


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
                a,b,c = pars
                return np.array(
                    [x**b,
                    a*b*x**(b-1),
                    np.ones(x.shape)]
                )
            elif N_PARS == 2:
                a,b = pars
                return np.array(
                    [x**b,
                    a*b*x**(b-1)]
                )
            else:
                return NotImplementedError("No Jacobian vector implemented for model with N_PARS={}".format(N_PARS))

        print("jac: ", jac(xVal,popt).shape, jac(xVal,popt))
        print("cov: ", pcov.shape, pcov)

        return np.sqrt(
            np.einsum("j..., j... -> ...", np.einsum("i..., ij -> j...", jac(xVal,popt), pcov), jac(xVal,popt))
        )

    # minimize function and take resulting azimuth
    # bounds = ((-np.inf,np.inf),(-np.inf,0),(-10,10))
    if N_PARS==3:
        result = opt.minimize(objective, x0=(0,-1,1), bounds=None, tol=1e-10, method='BFGS')
    elif N_PARS==2:
        result = opt.minimize(objective, x0=(0,-1), bounds=None, tol=1e-10, method='BFGS')
    else:
        raise NotImplementedError("No optimization implemented for N_PARS={}".format(N_PARS))

    print(result)
    print(hess(result.x))

    return dict(
        result=result,
        pars=result.x,
        cov=result.hess_inv, #np.linalg.inv(hess(result.x)),
        ys=model(xVal, result.x),
        yerrs=fit_error(xVal, result.x, result.hess_inv),
        chi2ndf=result.fun/(len(xVal)-N_PARS),
        chi2=result.fun, ndf=(len(xVal)-N_PARS)
    )


def kafe_fit(xVal, yVal, yErr):
    import kafe2
    data = kafe2.XYContainer(xVal, yVal)
    data.add_error(axis="y",err_val=yErr)

    def model(x, a=0, b=-1, c=1):
        return a*x**(b) + c
    
    fit = kafe2.Fit(data, model, minimizer="scipy")
    # fit.limit_parameter("a", lower=None, upper=None)
    fit.limit_parameter("b", lower=None, upper=0)
    fit.limit_parameter("c", lower=-10, upper=10)

    result = fit.do_fit()

    print(result)
    return dict(
        result=result,
        pars=[result["parameter_values"]["a"],result["parameter_values"]["b"],result["parameter_values"]["c"]],
        ys=fit.y_model,
        yerrs=fit.error_band(),
        chi2ndf=result["gof/ndf"],
        chi2=result["goodness_of_fit"], ndf=result["ndf"]
    )


# EXPERIMENTAL: doesn't work
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


