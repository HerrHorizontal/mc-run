
import scipy.optimize as opt
import numpy as np

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

    

def fit(xVal, yVal, yErr):
    """Fit function to ratio points."""

    N_PARS = 3
    def model(x, pars):
        return pars[0]*x**(pars[1]) + pars[2]

    def objective(pars):
        _res = (model(xVal, pars) - yVal) / yErr
        return np.sum(_res**2)

    # minimize function and take resulting azimuth
    result = opt.minimize(objective, x0=(0,-1,1), bounds=((-np.inf,np.inf),(-np.inf,0),(-10,10)), tol=1e-9)

    def fit_error(xVal,popt=result.x, pcov=result.hess_inv):
        """compute the uncertainty on the fitted function

        Args:
            xVal (np.ndarray): input space
            cov (np.ndarray): COvariance matrix of the fit result
        """
        def jac(x):
            """Jacobian vector of model function"""
            # from scipy.misc import derivative
            # return np.array(
            #     [derivative(,)]
            # )
            return np.array(
                [x**popt[1],
                 popt[0]*popt[1]*x**(popt[1]-1),
                 np.ones(x.shape)]
            )
        
        print("jac: ", jac(xVal).shape, jac(xVal))
        print("cov: ", pcov.shape, pcov.todense())
        # import pdb; pdb.set_trace()

        return np.sqrt(
            np.einsum("j..., j... -> ...", np.einsum("i..., ij -> j...", jac(xVal), pcov.todense()), jac(xVal))
        )

    return dict(
        result=result,
        pars=result.x,
        cov=result.hess_inv,
        ys=model(xVal, result.x),
        yerrs=fit_error(xVal),
        chi2ndf=result.fun/(len(xVal)-N_PARS),
        chi2=result.fun, ndf=(len(xVal)-N_PARS)
    )
    # result = opt.curve_fit(
    #     objective,
    #     xdata=xVal, ydata=yVal, sigma=yErr,
    #     bounds=((-np.inf,np.inf),(-np.inf,0),(-10,10)),
    #     full_output=True
    # )
    # return dict(
    #     result=result,
    #     pars=result.popt,
    #     cov=result.pcov,
    #     ys=model(xVal, result.popt)
    # )

