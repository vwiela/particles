# -*- coding: utf-8 -*-

"""
Probability distributions as Python objects.

Overview
========

This module lets users define probability distributions as Python objects.

The probability distributions defined in this module may be used:

  * to define state-space models (see module `state_space_models`);
  * to define a prior distribution, in order to perform parameter estimation
    (see modules `smc_samplers` and `mcmc`).

Univariate distributions
========================

The module defines the following classes of univariate continuous distributions:

=======================================  =====================
  class (with signature)                       comments
=======================================  =====================
Beta(a=1., b=1.)
Dirac(loc=0.)                            Dirac mass at point *loc*
FlatNormal(loc=0.)                       Normal with inf variance (missing data)
Gamma(a=1., b=1.)                        scale = 1/b
InvGamma(a=1., b=1.)                     Distribution of 1/X for X~Gamma(a,b)
Laplace(loc=0., scale=1.)
Logistic(loc=0., scale=1.)
LogNormal(mu=0., sigma=1.)               Dist of Y=e^X, X ~ N(μ, σ^2)
Normal(loc=0., scale=1.)                 N(loc,scale^2) distribution
Student(loc=0., scale=1., df=3)
TruncNormal(mu=0, sigma=1., a=0., b=1.)  N(mu, sigma^2) truncated to interval [a,b]
Uniform(a=0., b=1.)                      uniform over interval [a,b]
=======================================  =====================

and the following classes of univariate discrete distributions:

=======================================  =====================
  class (with signature)                       comments
=======================================  =====================
Binomial(n=1, p=0.5)
Categorical(p=None)                      returns i with prob p[i]
DiscreteUniform(lo=0, hi=2)              uniform over a, ..., b-1
Geometric(p=0.5)
Poisson(rate=1.)                         Poisson with expectation ``rate``
=======================================  =====================

Note that all the parameters of these distributions have default values, e.g.::

    some_norm = Normal(loc=2.4)  # N(2.4, 1)
    some_gam = Gamma()  # Gamma(1, 1)

Mixture distributions (new in version 0.4)
==========================================

A (univariate) mixture distribution may be specified as follows::

    mix = Mixture([0.5, 0.5], Normal(loc=-1), Normal(loc=1.))

The first argument is the vector of probabilities, the next arguments are the k
component distributions. 

See also `MixMissing` for defining a mixture distributions, between one
component that generates the label "missing", and another component::

    mixmiss = MixMissing(pmiss=0.1, base_dist=Normal(loc=2.))

This particular distribution is useful to specify a state-space model where the
observation may be missing with a certain probability.

Transformed distributions
=========================

To further enrich the list of available univariate distributions, the module
lets you define **transformed distributions**, that is, the distribution of
Y=f(X), for a certain function f, and a certain base distribution for X.

+--------------------------------+--------------------------+
| class name (and signature)     | description              |
+================================+==========================+
+--------------------------------+--------------------------+
| LinearD(base_dist, a=1., b=0.) | Y = a * X + b            |
+--------------------------------+--------------------------+
| LogD(base_dist)                | Y = log(X)               |
+--------------------------------+--------------------------+
| LogitD(base_dist, a=0., b=1.)  | Y = logit( (X-a)/(b-a) ) |
+--------------------------------+--------------------------+

A quick example::

    from particles import distributions as dists
    d = dists.LogD(dists.Gamma(a=2., b=2.))  # law of Y=log(X), X~Gamma(2, 2)

.. note:: These transforms are often used to obtain random variables
   defined over the full real line. This is convenient in particular
   when implementing random walk Metropolis steps.

Multivariate distributions
==========================

The module implements one multivariate distribution class, for Gaussian
distributions; see `MvNormal`.

Furthermore, the module provides two ways to construct multivariate
distributions from a collection of univariate distributions:

* `IndepProd`: product of independent distributions; mainly used to
  define state-space models.

* `StructDist`: distributions for named variables; mainly used to specify
  prior distributions; see modules `smc_samplers` and `mcmc` (and the
  corresponding tutorials).

Under the hood
==============

Probability distributions are represented as objects of classes that inherit
from base class `ProbDist`, and  implement the following methods:

* ``logpdf(self, x)``: computes the log-pdf (probability density function) at
  point ``x``;
* ``rvs(self, size=None)``: simulates ``size`` random variates; (if set to
  None, number of samples is either one if all parameters are scalar, or
  the same number as the common size of the parameters, see below);
* ``ppf(self, u)``: computes the quantile function (or Rosenblatt transform
  for a multivariate distribution) at point ``u``.

A quick example::

    some_dist = dists.Normal(loc=2., scale=3.)
    x = some_dist.rvs(size=30)  # a (30,) ndarray containing IID N(2, 3^2) variates
    z = some_dist.logpdf(x)  # a (30,) ndarray containing the log-pdf at x

By default, the inputs and outputs of these methods are either scalars or Numpy
arrays (with appropriate type and shape). In particular, passing a Numpy
array to a distribution parameter makes it possible to define "array
distributions". For instance::

    some_dist = dists.Normal(loc=np.arange(1., 11.))
    x = some_dist.rvs(size=10)

generates 10 Gaussian-distributed variates, with respective means 1., ..., 10.
This is how we manage to define "Markov kernels" in state-space models; e.g.
when defining the distribution of X_t given X_{t-1} in a state-space model::

    class StochVol(ssm.StateSpaceModel):
        def PX(self, t, xp, x):
            return stats.norm(loc=xp)
        ### ... see module state_space_models for more details

Then, in practice, in e.g. the bootstrap filter, when we generate particles
X_t^n, we call method ``PX`` and pass as an argument a numpy array of shape
(N,) containing the N ancestors.

.. note::
    ProbDist objects are roughly similar to the frozen distributions of package
    `scipy.stats`. However, they are not equivalent. Using such a
    frozen distribution when e.g. defining a state-space model will return an
    error.

Posterior distributions
=======================

A few classes also implement a ``posterior`` method, which returns the posterior
distribution that corresponds to a prior set to ``self``, a model which is
conjugate for the considered class, and some data. Here is a quick example::

    from particles import distributions as dists
    prior = dists.InvGamma(a=.3, b=.3)
    data = random.randn(20)  # 20 points generated from N(0,1)
    post = prior.posterior(data)
    # prior is conjugate wrt model X_1, ..., X_n ~ N(0, theta)
    print("posterior is Gamma(%f, %f)" % (post.a, post.b))

Here is a list of distributions implementing posteriors:

============    =================== ==================
Distribution    Corresponding model comments
============    =================== ==================
InvGamma        N(0, theta)
Gamma           N(0, 1/theta)
Normal          N(theta, sigma^2)   sigma fixed (passed as extra argument)
TruncNormal     same
MvNormal        N(theta, Sigma)     Sigma fixed (passed as extra argument)
============    =================== ==================


Implementing your own distributions
===================================

If you would like to create your own univariate probability distribution, the
easiest way to do so is to sub-class `ProbDist`, for a continuous distribution,
or `DiscreteDist`, for a discrete distribution. This will properly set class
attributes ``dim`` (the dimension, set to one, for a univariate distribution),
and ``dtype``, so that they play nicely with `StructDist` and so on. You will
also have to properly define methods ``rvs``, ``logpdf`` and ``ppf``. You may
omit ``ppf`` if you do not plan to use SQMC (Sequential quasi Monte Carlo).


"""

from __future__ import division, print_function

from collections import OrderedDict
from re import S  # see prior
import numpy as np
import numpy.random as random
import scipy.stats as stats
from scipy.linalg import cholesky, solve_triangular, inv

HALFLOG2PI = 0.5 * np.log(2. * np.pi)


class ProbDist(object):
    """Base class for probability distributions.

    To define a probability distribution class, subclass ProbDist, and define
    methods:

    * ``logpdf(self, x)``: the log-density at point x
    * ``rvs(self, size=None)``: generates *size* variates from distribution
    * ``ppf(self, u)``: the inverse CDF function at point u

    and attributes:

        * ``dim``: dimension of variates (default is 1)
        * ``dtype``: the dtype of inputs/outputs arrays (default is 'float64')

    """
    dim = 1  # distributions are univariate by default
    dtype = 'float64'  # distributions are continuous by default

    def shape(self, size):
        if size is None:
            return None
        else:
            return (size,) if self.dim == 1 else (size, self.dim)

    def logpdf(self, x):
        raise NotImplementedError

    def pdf(self, x):
        return np.exp(self.logpdf(x))

    def rvs(self, size=None):
        raise NotImplementedError

    def ppf(self, u):
        raise NotImplementedError

##############################
# location-scale distributions
##############################


class LocScaleDist(ProbDist):
    """Base class for location-scale distributions.
    """
    def __init__(self, loc=0., scale=1.):
        self.loc = loc
        self.scale = scale


class Normal(LocScaleDist):
    """N(loc, scale^2) distribution.
    """
    def rvs(self, size=None):
        return random.normal(loc=self.loc, scale=self.scale,
                             size=self.shape(size))

    def logpdf(self, x):
        return stats.norm.logpdf(x, loc=self.loc, scale=self.scale)

    def ppf(self, u):
        return stats.norm.ppf(u, loc=self.loc, scale=self.scale)

    def posterior(self, x, sigma=1.):
        """Model is X_1,...,X_n ~ N(theta, sigma^2), theta~self, sigma fixed.
        """
        pr0 = 1. / self.scale**2  # prior precision
        prd = x.size / sigma**2  # data precision
        varp = 1. / (pr0 + prd)  # posterior variance
        mu = varp * (pr0 * self.loc + prd * x.mean())
        return Normal(loc=mu, scale=np.sqrt(varp))


class Logistic(LocScaleDist):
    """Logistic(loc, scale) distribution.
    """
    def rvs(self, size=None):
        return random.logistic(loc=self.loc, scale=self.scale,
                               size=self.shape(size))

    def logpdf(self, x):
        return stats.logistic.logpdf(x, loc=self.loc, scale=self.scale)

    def ppf(self, u):
        return stats.logistic.ppf(u, loc=self.loc, scale=self.scale)


class Laplace(LocScaleDist):
    """Laplace(loc,scale) distribution.
    """

    def rvs(self, size=None):
        return random.laplace(loc=self.loc, scale=self.scale,
                              size=self.shape(size))

    def logpdf(self, x):
        return stats.laplace.logpdf(x, loc=self.loc, scale=self.scale)

    def ppf(self, u):
        return stats.laplace.ppf(u, loc=self.loc, scale=self.scale)


################################
# Other continuous distributions
################################

class Beta(ProbDist):
    """Beta(a,b) distribution.
    """
    def __init__(self, a=1., b=1.):
        self.a = a
        self.b = b

    def rvs(self, size=None):
        return random.beta(self.a, self.b, size=size)

    def logpdf(self, x):
        return stats.beta.logpdf(x, self.a, self.b)

    def ppf(self, x):
        return stats.beta.ppf(x, self.a, self.b)


class Gamma(ProbDist):
    """Gamma(a,b) distribution, scale=1/b.
    """
    def __init__(self, a=1., b=1.):
        self.a = a
        self.b = b
        self.scale = 1. / b

    def rvs(self, size=None):
        return random.gamma(self.a, scale=self.scale, size=size)

    def logpdf(self, x):
        return stats.gamma.logpdf(x, self.a, scale=self.scale)

    def ppf(self, u):
        return stats.gamma.ppf(u, self.a, scale=self.scale)

    def posterior(self, x):
        """Model is X_1,...,X_n ~ N(0, 1/theta), theta ~ Gamma(a, b)"""
        return Gamma(a=self.a + 0.5 * x.size,
                     b=self.b + 0.5 * np.sum(x**2))


class InvGamma(ProbDist):
    """Inverse Gamma(a,b) distribution.
    """
    def __init__(self, a=1., b=1.):
        self.a = a
        self.b = b

    def rvs(self, size=None):
        return stats.invgamma.rvs(self.a, scale=self.b, size=size)

    def logpdf(self, x):
        return stats.invgamma.logpdf(x, self.a, scale=self.b)

    def ppf(self, u):
        return stats.invgamma.ppf(u, self.a, scale=self.b)

    def posterior(self, x):
        " Model is X_1,...,X_n ~ N(0, theta), theta ~ InvGamma(a, b) "
        return InvGamma(a=self.a + 0.5 * x.size,
                        b=self.b + 0.5 * np.sum(x**2))


class LogNormal(ProbDist):
    """Distribution of Y=e^X, with X ~ N(mu, sigma^2).

    Note that mu and sigma are the location and scale parameters of X, not Y.
    """
    def __init__(self, mu=0., sigma=1.):
        self.mu = mu
        self.sigma = sigma

    def rvs(self, size=None):
        return random.lognormal(mean=self.mu, sigma=self.sigma, size=size)

    def logpdf(self, x):
        return stats.lognorm.logpdf(x, self.sigma, scale=np.exp(self.mu))

    def ppf(self, u):
        return stats.lognorm.ppf(u, self.sigma, scale=np.exp(self.mu))

class Uniform(ProbDist):
    """Uniform([a,b]) distribution.
    """
    def __init__(self, a=0, b=1.):
        self.a = a
        self.b = b
        self.scale = b - a

    def rvs(self, size=None):
        return random.uniform(low=self.a, high=self.b, size=size)

    def logpdf(self, x):
        return stats.uniform.logpdf(x, loc=self.a, scale=self.scale)

    def ppf(self, u):
        return stats.uniform.ppf(u, loc=self.a, scale=self.scale)


class Student(ProbDist):
    """Student distribution.
    """
    def __init__(self, df=3., loc=0., scale=1.):
        self.df = df
        self.loc = loc
        self.scale = scale

    def rvs(self, size=None):
        return stats.t.rvs(self.df, loc=self.loc, scale=self.scale, size=size)

    def logpdf(self, x):
        return stats.t.logpdf(x, self.df, loc=self.loc, scale=self.scale)

    def ppf(self, u):
        return stats.t.ppf(u, self.df, loc=self.loc, scale=self.scale)


class FlatNormal(ProbDist):
    """Normal with infinite variance.

    May be used to specify the distribution of a missing value.
    Sampling from FlatNormal generate an array of NaNs.
    """
    def __init__(self, loc=0.):
        self.loc = loc

    def logpdf(self, x):
        # ensures proper shape/type
        return 0. * (x + self.loc)

    def rvs(self, size=None):
        sz = 1 if size is None else size
        return self.loc + np.full(sz, np.nan)


class Dirac(ProbDist):
    """Dirac mass.
    """
    def __init__(self, loc=0.):
        self.loc = loc

    def rvs(self, size=None):
        if isinstance(self.loc, np.ndarray):
            return self.loc.copy()
            # seems safer to make a copy here
        else:  # a scalar
            N = 1 if size is None else size
            return np.full(N, self.loc)

    def logpdf(self, x):
        return np.where(x==self.loc, 0., -np.inf)

    def ppf(self, u):
        return self.rvs(size=u.shape[0])


class TruncNormal(ProbDist):
    """Normal(mu, sigma^2) truncated to [a, b] interval.
    """
    def __init__(self, mu=0., sigma=1., a=0., b=1.):
        self.mu = mu
        self.sigma = sigma
        self.a = a
        self.b = b
        self.au = (a - mu) / sigma
        self.bu = (b - mu) / sigma

    def rvs(self, size=None):
        return stats.truncnorm.rvs(self.au, self.bu, loc=self.mu,
                                   scale=self.sigma, size=size)

    def logpdf(self, x):
        return stats.truncnorm.logpdf(x, self.au, self.bu, loc=self.mu,
                                      scale=self.sigma)

    def ppf(self, u):
        return stats.truncnorm.ppf(u, self.au, self.bu, loc=self.mu,
                                   scale=self.sigma)

    def posterior(self, x, s=1.):
        """Model is X_1,...,X_n ~ N(theta, s^2), theta~self, s fixed"""
        pr0 = 1. / self.sigma**2  # prior precision
        prd = x.size / s**2  # data precision
        varp = 1. / (pr0 + prd)  # posterior variance
        mu = varp * (pr0 * self.mu + prd * x.mean())
        return TruncNormal(mu=mu, sigma=np.sqrt(varp), a=self.a, b=self.b)

########################
# Discrete distributions
########################


class DiscreteDist(ProbDist):
    """Base class for discrete probability distributions.
    """
    dtype = 'int64'


class Poisson(DiscreteDist):
    """Poisson(rate) distribution.
    """
    def __init__(self, rate=1.):
        self.rate = rate

    def rvs(self, size=None):
        return random.poisson(self.rate, size=size)

    def logpdf(self, x):
        return stats.poisson.logpmf(x, self.rate)

    def ppf(self, u):
        return stats.poisson.ppf(u, self.rate)


class Binomial(DiscreteDist):
    """Binomial(n,p) distribution.
    """
    def __init__(self, n=1, p=0.5):
        self.n = n
        self.p = p

    def rvs(self, size=None):
        return random.binomial(self.n, self.p, size=size)

    def logpdf(self, x):
        return stats.binom.logpmf(x, self.n, self.p)

    def ppf(self, u):
        return stats.binom.ppf(u, self.n, self.p)


class Geometric(DiscreteDist):
    """Geometric(p) distribution.
    """
    def __init__(self, p=0.5):
        self.p = p

    def rvs(self, size=None):
        return random.geometric(self.p, size=size)

    def logpdf(self, x):
        return stats.geom.logpmf(x, self.p)

    def ppf(self, u):
        return stats.geom.ppf(u, self.p)

class NegativeBinomial(DiscreteDist):
    """Negative Binomial distribution.

    Parameters
    ----------
    n:  int, or array of ints
        number of failures until the experiment is run
    p:  float, or array of floats
        probability of success

    Note:
        Returns the distribution of the number of successes: support is
        0, 1, ...

    """
    def rvs(self, size=None):
        return random.negative_binomial(self.n, self.p, size=size)

    def logpdf(self, x):
        return stats.nbinom.logpmf(x, self.p, self.n)

    def ppf(self, u):
        return stats.nbinom.ppf(u, self.p, self.n)


class Categorical(DiscreteDist):
    """Categorical distribution.

    Parameter
    ---------
    p:  (k,) or (N,k) float array
        vector(s) of k probabilities that sum to one
    """
    def __init__(self, p=None):
        self.p = p

    def logpdf(self, x):
        return np.log(self.p[x])

    def rvs(self, size=None):
        if self.p.ndim == 1:
            N = 1 if size is None else size
            u =random.rand(N)
            return np.searchsorted(np.cumsum(self.p), u)
        else:
            N = self.p.shape[0] if size is None else size
            u = random.rand(N)
            cp = np.cumsum(self.p, axis=1)
            return np.array([np.searchsorted(cp[i], u[i])
                             for i in range(N)])

class DiscreteUniform(DiscreteDist):
    """Discrete uniform distribution.

    Parameters
    ----------
    lo, hi: int
        support is lo, lo + 1, ..., hi - 1

    """

    def __init__(self, lo=0, hi=2):
        self.lo, self.hi = lo, hi
        self.log_norm_cst = np.log(hi - lo)

    def logpdf(self, x):
        return np.where((x >= self.lo) & (x<self.hi), -self.log_norm_cst, -np.inf)

    def rvs(self, size=None):
        return random.randint(self.lo, high=self.hi, size=size)

#########################
# distribution transforms
#########################

class TransformedDist(ProbDist):
    """Base class for transformed distributions.

    A transformed distribution is the distribution of Y=f(X) for a certain
    function f, and a certain (univariate) base distribution for X.
    To define a particular class of transformations, sub-class this class, and
    define methods:

        * f(self, x): function f
        * finv(self, x): inverse of function f
        * logJac(self, x): log of Jacobian of the inverse of f

    """

    def __init__(self, base_dist):
        self.base_dist = base_dist

    def error_msg(self, method):
        return 'method %s not defined in class %s' % (method, self.__class__)

    def f(self, x):
        raise NotImplementedError(self.error_msg('f'))

    def finv(self, x):
        """ Inverse of f."""
        raise NotImplementedError(self.error_msg('finv'))

    def logJac(self, x):
        """ Log of Jacobian.

        Obtained by differentiating finv, and then taking the log."""
        raise NotImplementedError(self.error_msg('logJac'))

    def rvs(self, size=None):
        return self.f(self.base_dist.rvs(size=size))

    def logpdf(self, x):
        return self.base_dist.logpdf(self.finv(x)) + self.logJac(x)

    def ppf(self, u):
        return self.f(self.base_dist.ppf(u))


class LinearD(TransformedDist):
    """Distribution of Y = a*X + b.

    See TransformedDist.

    Parameters
    ----------
    base_dist: ProbDist
        The distribution of X

    a, b: float (a should be != 0)
    """
    def __init__(self, base_dist, a=1., b=0.):
        self.a, self.b = a, b
        self.base_dist = base_dist

    def f(self, x):
        return self.a * x + self.b

    def finv(self, x):
        return (x - self.b) / self.a

    def logJac(self, x):
        return -np.log(self.a)


class LogD(TransformedDist):
    """Distribution of Y = log(X).

    See TransformedDist.

    Parameters
    ----------
    base_dist: ProbDist
        The distribution of X

    """
    def f(self, x):
        return np.log(x)

    def finv(self, x):
        return np.exp(x)

    def logJac(self, x):
        return x


class LogitD(TransformedDist):
    """Distributions of Y=logit((X-a)/(b-a)).

    See base class `TransformedDist`.

    Parameters
    ----------
    base_dist: ProbDist
        The distribution of X
    a, b: float
        interval [a, b] is the support of base_dist

    """

    def __init__(self, base_dist, a=0., b=1.):
        self.a, self.b = a, b
        self.base_dist = base_dist

    def f(self, x):
        p = (x - self.a) / (self.b - self.a)
        return np.log(p / (1. - p))  # use built-in?

    def finv(self, x):
        return self.a + (self.b - self.a) / (1. + np.exp(-x))

    def logJac(self, x):
        return np.log(self.b - self.a) + x - 2. * np.log(1. + np.exp(x))

###########################
# Mixtures
###########################

class Mixture(ProbDist):
    """Mixture distributions.

    Parameters
    ----------
    pk:  array-like of shape (k,) or (N, k)
        component probabilities (must sum to one)
    *components: ProbDist objects
        the k component distributions

    Example:
        mix = Mixture([0.6, 0.4], Normal(loc=3.), Normal(loc=-3.))

    """
    def __init__(self, pk, *components):
        self.pk = np.atleast_1d(pk)
        self.k = self.p.shape[-1]
        if len(components) != self.k:
            raise ValueError('Size of pk and nr of components should match')
        self.components = components

    def logpdf(self, x):
        lpks = [np.log(self.pk[..., i]) + cd.logpdf(x)
               for i, cd in enumerate(self.components)]
        return sp.special.logsumexp(np.column_stack(tuple(lpks)),
                                    axis=-1)

    def rvs(self, size=None):
        k = Categorical(p=self.pk).rvs(size=size)
        xk = [cd.rvs(size=size) for cd in self.components]
        # sub-optimal, we sample N x k values
        return np.choose(k, xk)

class MixMissing(ProbDist):
    """Mixture between a given distribution and 'missing'.

    Example:
        mix = MixMissing(pmiss=0.10, base_dist=Normal(loc=1.))

    Main use is for state-space models where Y_t may be missing with a certain
    probability.
    """
    def __init__(self, pmiss=0.10, base_dist=None):
        self.pmiss = pmiss
        self.base_dist = base_dist

    def logpdf(self, x):
        l = self.base_dist.logpdf(x)
        ina = np.atleast_1d(np.isnan(x))
        if ina.shape[0] == 1:
            ina = np.full_like(l, ina, dtype=np.bool)
        l[ina] = np.log(self.pmiss)
        l[np.logical_not(ina)] += np.log(1. - self.pmiss)
        return l

    def rvs(self, size=None):
        x = self.base_dist.rvs(size=size)
        N = x.shape[0]
        is_missing = random.rand(N) < self.pmiss
        x[is_missing, ...] = np.nan
        return x

############################
# Multivariate distributions
############################

class MvNormal(ProbDist):

    def __init__(self, loc=0., scale=1., cov=None):
        self.cov = np.array([np.eye(len(loc[0]))]*loc.shape[0]) if cov is None else cov
        self.loc = loc
        self.scale = scale
        err_msg = 'mvnorm: argument cov must contain dxd ndarrays, \
                with d>1, defining a symmetric positive matrix'
        try:
            self.L = cholesky(self.cov[0], lower=True)  # L*L.T = cov
        except:
            raise ValueError(err_msg)
        assert self.cov[0].shape == (self.dim, self.dim), err_msg
        L_list = []
        for i in range(self.cov.shape[0]):
            L_list.append(cholesky(self.cov[i], lower=True))
        self.L_list = L_list
        self.halflogdetcor = np.zeros(len(L_list))
        for i in range(len(L_list)):
            self.halflogdetcor[i] = np.sum(np.log(np.diag(self.L_list[i])))

    @property
    def number(self):
        return self.cov.shape[0]

    @property
    def dim(self):
        return self.cov.shape[-1]

    def linear_transform(self, z):
        # z is a list of normal random variables, Nxd
        transformed = np.empty_like(z)
        for i in range(z.shape[0]):
            transformed[i] = self.loc[i] + self.scale * np.dot(z[i], self.L_list[i].T)
        return transformed

    def logpdf(self, x): # x is Nxd
        if x.shape[0] > self.number:
            raise AssertionError('given number realisations is greater than number of rv`s')
        z = []
        for i in range(x.shape[0]):
            z.append(solve_triangular(L, ((x[i] - loc[i]) / scale), lower=True))
        z = np.array(z)
        # z is Nxd as well
        if np.asarray(self.scale).ndim == 0:
            logdet = np.array([self.dim * np.log(self.scale)]*x.shape[0])
        else:
            logdet = np.array([np.sum(np.log(self.scale), axis=-1)]*x.shape[0])
        logdet += self.halflogdetcor
        return - 0.5 * np.sum(z * z, axis=1) - logdet - self.dim * (0.5*np.log(2*np.pi))

    def rvs(self, size=None):
        if size is None:
            size = self.number
        elif size > self.number:
            raise AssertionError('asked number of rv`s is greater than number of given input rv`s')
        else:
            N = size
        z = stats.norm.rvs(size=(N, self.dim))
        return self.linear_transform(z)

    def ppf(self, u): # Works but why u needs to be Nxd and what is it used for when it treats just the partial case
        """
        Note: if dim(u) < self.dim, the remaining columns are filled with 0
        Useful in case the distribution is partly degenerate.
        """
        N, du = u.shape
        if du < self.dim:
            z = np.zeros((N, self.dim))
            z[:, :du] = stats.norm.ppf(u)
        else:
            z = stats.norm.ppf(u)
        return self.linear_transform(z)

    def posterior(self, x, Sigma=None):
        """Posterior for model: X1, ..., Xn ~ N(theta, Sigma), theta ~ self.

        Parameters
        ----------
        x: (n, d) ndarray
            data
        Sigma: (n, d, d) ndarray
            covariance matrices in the model (default: identity matrix)

        Notes
        -----
        Scale must be set to 1.
        """
        if self.scale != 1.:
            raise ValueError('posterior of MvNormal: scale must be one.')
        n = x.shape[0]
        Sigma = np.array([np.eye(self.dim)]*x.shape[0]) if Sigma is None else Sigma
        Siginv = np.array([inv(Sig) for Sig in list(Sigma)])
        covinv = np.array([inv(cov) for cov in list(self.cov)])
        Qpost = np.empty_like(Sigma)
        for i in range(n):
            Qpost[i] = covinv[i] + n * Siginv[i]
        Sigpost = np.array([inv(Qp) for Qp in list(Qpost)])
        m = np.full(self.dim, self.loc) if np.isscalar(self.loc) else self.loc
        mupost = np.empty_like(x)
        for i in range(n):
            mupost[i] = Sigpost[i] @ (m[i] @ covinv[i] + Siginv[i] @ np.sum(x, axis=0))
        # m @ covinv works wether the shape of m is (N, d) or (d)
        return MvNormal(loc=mupost, cov=Sigpost)

class MvNormal_new(ProbDist):

    def __init__(self, loc=0., scale=1., cov=None, trunc_rv=False):
        self.cov = np.array([np.eye(len(loc[0]))]*loc.shape[0]) if cov is None else cov
        self.loc = loc
        self.scale = scale
        self.trunc_rv = trunc_rv
        err_msg = 'mvnorm: argument cov must contain dxd ndarrays, \
                with d>1, defining a symmetric positive matrix'
        # try:
        #     self.L = cholesky(self.cov[0], lower=True)  # L*L.T = cov
        # except:
        #     raise ValueError(err_msg)
        assert self.cov[0].shape == (self.dim, self.dim), err_msg
        # L_list = []
        # for i in range(self.cov.shape[0]):
        #     L_list.append(cholesky(self.cov[i], lower=True))
        # self.L_list = L_list
        # self.halflogdetcor = np.zeros(len(L_list))
        # for i in range(len(L_list)):
        #     self.halflogdetcor[i] = np.sum(np.log(np.diag(self.L_list[i])))

    @property
    def number(self):
        return self.loc.shape[0]

    @property
    def dim(self):
        return self.cov.shape[-1]

    def linear_transform(self, z):
        # z is a list of normal random variables, Nxd
        transformed = np.empty_like(z)
        for i in range(z.shape[0]):
            transformed[i] = self.loc[i] + self.scale * np.dot(z[i], self.L_list[i].T)
        return transformed

    def logpdf(self, x): # x is Nxd
        if self.number == 1:
            l = np.empty(x.shape[0])
            for n in range(x.shape[0]):
                l[n] = stats.multivariate_normal.logpdf(x[n], mean =self.loc[0], cov=self.cov[0], allow_singular=True)
            return l
        
        if x.shape[0] > self.number:
            raise AssertionError('given number realisations is greater than number of rv`s')
        
        if np.ndim(x)==1 and x.shape[0]==self.dim: # for the case where data is given as  y(t)=[y1,y2]
            l = np.empty(self.number)
            for n in range(self.number):
                l[n] = stats.multivariate_normal.logpdf(x, mean=self.loc[n,:], cov=self.cov[n, :, :], allow_singular=True)
            return l


        l = np.empty(x.shape[0])
        for n in range(x.shape[0]):
            l[n] = stats.multivariate_normal.logpdf(x[n], mean =self.loc[n,:], cov=self.cov[n,:,:], allow_singular=True)
        return l

    def rvs(self, size=None):
        if size is None:
            size = self.number
        
        if self.number == 1:
            if self.trunc_rv:
                x = np.empty((size, self.dim))
                for n in range(size):
                    x[n, :] = np.maximum(0, random.multivariate_normal(self.loc[0], self.cov[0]))
                return x

            x = np.empty((size, self.dim))
            for n in range(size):
                x[n, :] = random.multivariate_normal(self.loc[0], self.cov[0])
            return x 
        
        elif size > self.number:
            raise AssertionError('asked number of rv`s is greater than number of given input rv`s')
        
        else:
                    
            if self.trunc_rv:
                x = np.empty((size, self.dim))
                for n in range(size):
                    x[n, :] = np.maximum(0, random.multivariate_normal(self.loc[n, :], self.cov[n, :, :]))

            else:
                x = np.empty((size, self.dim))
                for n in range(size):
                    x[n, :] = random.multivariate_normal(self.loc[n, :], self.cov[n, :, :])

            return x

    # ppf is just needed for SQMC
    # def ppf(self, u): # Works but why u needs to be Nxd and what is it used for when it treats just the partial case
    #     """
    #     Note: if dim(u) < self.dim, the remaining columns are filled with 0
    #     Useful in case the distribution is partly degenerate.
    #     """
    #     N, du = u.shape
    #     if du < self.dim:
    #         z = np.zeros((N, self.dim))
    #         z[:, :du] = stats.norm.ppf(u)
    #     else:
    #         z = stats.norm.ppf(u)
    #     return self.linear_transform(z)

    def posterior(self, x, Sigma=None):
        """Posterior for model: X1, ..., Xn ~ N(theta, Sigma), theta ~ self.

        Parameters
        ----------
        x: (n, d) ndarray
            data
        Sigma: (n, d, d) ndarray
            covariance matrices in the model (default: identity matrix)

        Notes
        -----
        Scale must be set to 1.
        """
        if self.scale != 1.:
            raise ValueError('posterior of MvNormal: scale must be one.')
        n = x.shape[0]
        Sigma = np.array([np.eye(self.dim)]*x.shape[0]) if Sigma is None else Sigma
        Siginv = np.array([inv(Sig) for Sig in list(Sigma)])
        covinv = np.array([inv(cov) for cov in list(self.cov)])
        Qpost = np.empty_like(Sigma)
        for i in range(n):
            Qpost[i] = covinv[i] + n * Siginv[i]
        Sigpost = np.array([inv(Qp) for Qp in list(Qpost)])
        m = np.full(self.dim, self.loc) if np.isscalar(self.loc) else self.loc
        mupost = np.empty_like(x)
        for i in range(n):
            mupost[i] = Sigpost[i] @ (m[i] @ covinv[i] + Siginv[i] @ np.sum(x, axis=0))
        # m @ covinv works wether the shape of m is (N, d) or (d)
        return MvNormal_new(loc=mupost, cov=Sigpost)


class MvNormal_old(ProbDist):
    """Multivariate Normal distribution.
    Parameters
    ----------
    loc: ndarray
        location parameter (default: 0.)
    scale: ndarray
        scale parameter (default: 1.)
    cov: (d, d) ndarray
        covariance matrix (default: identity, with dim determined by loc)
    Notes
    -----
    The dimension d is determined either by argument ``cov`` (if it is a dxd 
    array), or by argument loc (if ``cov`` is not specified). In the latter 
    case, the covariance matrix is set to the identity matrix. 
    If ``scale`` is set to ``1.`` (default value), we use the standard 
    parametrisation of a Gaussian, with mean ``loc`` and covariance 
    matrix ``cov``. Otherwise::
        x = dists.MvNormal(loc=m, scale=s, cov=Sigma).rvs(size=30)
    is equivalent to::
        x = m + s * dists.MvNormal(cov=Sigma).rvs(size=30)
    The idea is that they are cases when we may want to pass varying
    means and scales (but a fixed correlation matrix). Note that
    ``cov`` does not need to be a correlation matrix; e.g.::
        MvNormal(loc=m, scale=s, cov=C)
    corresponds to N(m, diag(s)*C*diag(s)).
    In addition, note that m and s may be (N, d) vectors;
    i.e for each n=1...N we have a different mean, and a different scale.
    To specify a Multivariate Normal distribution with a different covariance
    matrix for each particle, see `VaryingCovNormal`.
    """

    def __init__(self, loc=0., scale=1., cov=None):
        self.loc = loc
        self.scale = scale
        self.cov = np.eye(loc.shape[-1]) if cov is None else cov
        err_msg = 'MvNormal: argument cov must be a (d, d) pos. definite matrix'
        try:
            self.L = cholesky(self.cov)  # lower triangle
        except:
            raise ValueError(err_msg)
        assert self.cov.shape == (self.dim, self.dim), err_msg

    @property
    def dim(self):
        return self.cov.shape[-1]

    def linear_transform(self, z):
        return self.loc + self.scale * np.dot(z, self.L.T)

    def logpdf(self, x):
        halflogdetcor = np.sum(np.log(np.diag(self.L)))
        xc = (x - self.loc) / self.scale
        z = solve_triangular(self.L, np.transpose(xc), lower=True)
        # z is dxN, not Nxd
        if np.asarray(self.scale).ndim == 0:
            logdet = self.dim * np.log(self.scale)
        else:
            logdet = np.sum(np.log(self.scale), axis=-1)
        logdet += halflogdetcor
        return - 0.5 * np.sum(z * z, axis=0) - logdet - self.dim * HALFLOG2PI

    def rvs(self, size=None):
        if size is None:
            sh = np.broadcast(self.loc, self.scale).shape
            # sh=() when both loc and scale are scalars
            N = 1 if len(sh) == 0 else sh[0]
        else:
            N = size
        z = stats.norm.rvs(size=(N, self.dim))
        return self.linear_transform(z)

    def ppf(self, u):
        """
        Note: if dim(u) < self.dim, the remaining columns are filled with 0.
        Useful in case the distribution is partly degenerate.
        """
        N, du = u.shape
        if du < self.dim:
            z = np.zeros((N, self.dim))
            z[:, :du] = stats.norm.ppf(u)
        else:
            z = stats.norm.ppf(u)
        return self.linear_transform(z)

    def posterior(self, x, Sigma=None):
        """Posterior for model: X1, ..., Xn ~ N(theta, Sigma), theta ~ self.
        Parameters
        ----------
        x: (n, d) ndarray
            data
        Sigma: (d, d) ndarray
            covariance matrix in the model (default: identity matrix)
        Notes
        -----
        Scale must be set to 1.
        """
        if self.scale != 1.:
            raise ValueError('posterior of MvNormal: scale must be one.')
        n = x.shape[0]
        Sigma = np.eye(self.dim) if Sigma is None else Sigma
        Siginv = sla.inv(Sigma)
        covinv = sla.inv(self.cov)
        Qpost = covinv + n * Siginv
        Sigpost = sla.inv(Qpost)
        m = np.full(self.dim, self.loc) if np.isscalar(self.loc) else self.loc
        mupost = Sigpost @ (m @ covinv + Siginv @ np.sum(x, axis=0))
        # m @ covinv works wether the shape of m is (N, d) or (d)
        return MvNormal(loc=mupost, cov=Sigpost)

##################################
# product of independent dists


class IndepProd(ProbDist):
    """Product of independent univariate distributions.

    The inputs/outputs of IndeProd are numpy ndarrays of shape (N,d), or (d),
    where d is the number of univariate distributions that are
    passed as arguments.

    Parameters
    ----------
    dists: list of `ProbDist` objects
        The probability distributions of each component

    Example
    -------
    To define a bivariate distribution::

        biv_dist = IndepProd(Normal(scale=2.), Gamma(2., 3.))
        samples = biv_dist.rvs(size=9)  # returns a (9, 2) ndarray

    Note
    ----
    This is used mainly to define multivariate state-space models,
    see module `state_space_models`. To specify a prior distribution, you
    should use instead `StructDist`.

    """
    def __init__(self, *dists):
        self.dists = dists
        self.dim = len(dists)
        if all(d.dtype == 'int64' for d in dists):
            self.dtype = 'int64'
        else:
            self.dtype = 'float64'

    def logpdf(self, x):
        return sum([d.logpdf(x[..., i]) for i, d in enumerate(self.dists)])
        # ellipsis: in case x is of shape (d) instead of (N, d)

    def rvs(self, size=None):
        return np.stack([d.rvs(size=size) for d in self.dists], axis=1)

    def ppf(self, u):
        return np.stack([d.ppf(u[..., i]) for i, d in enumerate(self.dists)],
                        axis=1)

def IID(law, k):
    """Joint distribution of k iid (independent and identically distributed) variables.

    Parameters
    ----------
    law:  ProbDist object
        the univariate distribution of each component
    k: int (>= 2)
        number of components
    """
    return IndepProd(*[law for _ in range(k)])

###################################
# structured array distributions
# (mostly to define prior distributions)
###################################

class Cond(ProbDist):
    """Conditional distributions.

    A conditional distribution acts as a function, which takes as input the
    current value of the samples, and returns a probability distribution.

    This is used to specify conditional distributions in `StructDist`; see the
    documentation of that class for more details.
    """
    def __init__(self, law, dim=1, dtype='float64'):
        self.law = law
        self.dim = dim
        self.dtype = dtype

    def __call__(self, x):
        return self.law(x)

class StructDist(ProbDist):
    """A distribution such that inputs/outputs are structured arrays.

    A structured array is basically a numpy array with named fields.
    We use structured arrays to represent particles that are
    vectors of (named) parameters; see modules :mod:`smc_samplers`
    and :mod:`mcmc`. And we use StructDist to define prior distributions
    with respect to such parameters.

    To specify a distribution such that parameters are independent,
    we pass a dictionary::

        prior = StructDist({'mu':Normal(), 'sigma':Gamma(a=1., b=1.)})
        # means mu~N(0,1), sigma~Gamma(1, 1) independently
        x = prior.rvs(size=30)  # returns a stuctured array of length 30
        print(x['sigma'])  # prints the 30 values for sigma

    We may also define a distribution using a chain rule decomposition.
    For this, we pass an ordered dict, since the order of components
    become relevant::

        chain_rule = OrderedDict()
        chain_rule['mu'] = Normal()
        chain_rule['tau'] = Cond(lambda x: Normal(loc=x['mu'])
        prior = StructDist(chain_rule)
        # means mu~N(0,1), tau|mu ~ N(mu,1)

    In the third line, ``Cond`` is a ``ProbDist`` class that represents
    a conditional distribution; it is initialized with a function that
    returns for each ``x`` a distribution that may depend on fields in ``x``.

    Parameters
    ----------
    laws: dict or ordered dict (as explained above)
        keys are parameter names, values are `ProbDist` objects

    """

    def __init__(self, laws):
        if isinstance(laws, OrderedDict):
            self.laws = laws
        elif isinstance(laws, dict):
            self.laws = OrderedDict([(key, laws[key])
                                     for key in sorted(laws.keys())])
        else:
            raise ValueError('recdist class requires a dict or'
                             ' an ordered dict to be instantiated')
        self.dtype = []
        for key, law in self.laws.items():
            if law.dim == 1:
                typ = (key, law.dtype)  # avoid FutureWarning about (1,) fields
            else:
                typ = (key, law.dtype, law.dim)
            self.dtype.append(typ)

    def logpdf(self, theta):
        l = 0.
        for par, law in self.laws.items():
            cond_law = law(theta) if callable(law) else law
            l += cond_law.logpdf(theta[par])
        return l

    def rvs(self, size=1):  # Default for size is 1, not None
        out = np.empty(size, dtype=self.dtype)
        for par, law in self.laws.items():
            cond_law = law(out) if callable(law) else law
            out[par] = cond_law.rvs(size=size)
        return out

    def ppf(self, theta):
        out = np.empty(size, dtype=self.dtype)
        for par, law in self.laws.items():
            cond_law = law(out) if callable(law) else law
            out[par] = cond_law.ppf(theta[par])
        return out
