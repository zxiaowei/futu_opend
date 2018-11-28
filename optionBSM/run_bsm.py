from math import log,sqrt,exp
from scipy import stats

def bsm_call_value(S0,K,T,r,sigma):
    S0 = float(S0)
    d1 = (log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = (log(S0 / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    value = (S0 * stats.norm.cdf(d1,0.0,1.0) - K * exp(-r * T) * stats.norm.cdf(d2,0.0,1.0))
    print(value,"ccc")
    return value

def bsm_put_value(S0,K,T,r,sigma):
    S0 = float(S0)
    d1 = (log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    d2 = (log(S0 / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    value = (S0 * (stats.norm.cdf(d1,0.0,1.0)-1) - K * exp(-r * T) * (stats.norm.cdf(d2,0.0,1.0)-1))
    print(value,"ppp")
    return value


def bsm_vega(S0,K,T,r,sigma):
    S0 = float(S0)
    d1 = (log(S0 / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
    vega = S0 * stats.norm.cdf(d1,0.0,1.0) * sqrt(T)
    return vega

def bsm_call_imp_vol(S0,K,T,r,C0,sigma_est,it = 100):
    for i in range(it):
        sigma_est -= ((bsm_call_value(S0,K,T,r,sigma_est) - C0) / bsm_vega(S0,K,T,r,sigma_est))
    print(sigma_est,"sss")
    return sigma_est

S0 = 219.8
K = 205
T = 0.0834
r = 0.0228
sigma = 0.3857
a=bsm_call_value(S0,K,T,r,sigma)
b=bsm_put_value(S0,K,T,r,sigma)