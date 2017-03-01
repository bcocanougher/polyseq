import numpy as np
import multiprocessing as mp
import pandas as pd

def getLogW(data, Algorithm, k, algKwargs):
    '''
    Compute log(sum of squared distances from cluster)
    '''
    alg = Algorithm(n_clusters=k, **algKwargs)
    distsToCenters = alg.fit_transform(data)
    labels = alg.labels_
    logW = np.log(np.sum(np.choose(labels, distsToCenters.T)**2))
    return logW, labels

def generateSample(bounds, mean, pca, n):
    '''
    Generate a sample from the null distribution
    '''
    proj = [np.random.uniform(low=l, high=h, size=n) for (l, h) in bounds]
    proj = np.array(proj).T
    orig = pca.inverse_transform(proj)
    return mean + orig

def getSampleStat(args):
    '''
    Get the logW statistic for a sample from the null distribution

    Needed because multiprocessing.Pool.map only works with functions that
    take a single argument.
    '''
    seed, bounds, mean, pca, n, Algorithm, k, algKwargs = args
    np.random.seed(seed)
    sample = generateSample(bounds, mean, pca, n)
    stat, _ = getLogW(sample, Algorithm, k, algKwargs)
    return stat

def gapStatistic(data, Algorithm, nSamples, nProcesses=1, cutoff=None,
                 algKwargs={}):
    '''
    Determine the number of clusters via the gap statistic method

    Tibsharani, Walther, & Hastie; J.R. Statist. Soc. B, 2001

    Parameters:
    -----------
    data: 2D array-like
        Data maxtrix of shape (samples, features)

    Algorithm: scikit-learn style clustering algorithm class
        e.g. sklearn.cluster.KMeans

    nSamples: int
        Number of samples from null distribution to use when computing
        reference statistics

    nProcesses: int, default=1
        Number of processes to use for parallel processing of samples from null
        distribution. Note: each process will require memory equal to the size
        of the original dataset to store the random sample.

    cutoff: int, default=None
        Maximum number of clusters to try before exiting with an error code (k
        = -1)

    cutoff: int, default=None
        Maximum number of clusters to try before exiting with an error code (k
        = -1). If None, then the number of clusters can be artibrarily large,
        if supported by the data.

    algKwargs: dictionary, default={}
       Optional keyword arguments to pass to the clustering algorithm
       constructor.

    Returns:
    --------
    k: int
        The optimal number of clusters
    labels:
        Cluster labels when fitting with k clusters
    '''
    n, k = data.shape

    # compute parameters of null distribution
    from sklearn.decomposition import PCA
    mean = data.mean(axis=0).__array__()
    centered = data - mean
    pca = PCA(n_components=k).fit(centered)
    proj = pca.transform(centered)

    bounds = [(v.min(), v.max()) for v in proj.T]
    k=1
    gapLast = 0
    labels = []
    p = mp.Pool(processes=nProcesses)
    while True:
        # cluster true data
        labelsLast = labels
        logW, labels = getLogW(data, Algorithm, k, algKwargs)
        # create and cluster data from null distribution
        args = (bounds, mean, pca, n, Algorithm, k, algKwargs)
        seedStart = np.random.randint(low=0, high=2*8-1)
        args = [(s + seedStart,) + args for s in range(nSamples)]
        stats = p.map(getSampleStat, args)
        # compute statistics
        logWStar = np.mean(stats)
        error = np.sqrt(1-1.0/nSamples) * np.std(stats)
        gap = logWStar - logW
        deltaGap = gap - gapLast
        gapLast = gap
        k += 1
        if k == 2:
            continue
        if deltaGap < error:
            return k - 2, labelsLast
        if cutoff is not None and k > cutoff:
            print("exiting early")
            return -1, labels

def hCluster(data, DimAlg, ClustAlg, nSamples=1000, nProcesses=1, cutoff=None,
             algKwargs={}):
    '''
    Top-down hierarchical clustering.

    Parameters:
    -----------
    data: 2D array-like
        Data maxtrix of shape (samples, features)

    Algorithm: scikit-learn style clustering algorithm class
        e.g. sklearn.cluster.KMeans

    nSamples: int, default=1000
        Number of samples from null distribution to use when using the gap
        statistic to determine depth of clustering.

    nProcesses: int, default=1
        Number of processes to use for parallel processing of samples from null
        distribution. Note: each process will require memory equal to the size
        of the original dataset to store the random sample.

    cutoff: int, default=None
        Maximum number of clusters to try before exiting with an error code (k
        = -1). If None, then the number of clusters can be artibrarily large,
        if supported by the data.

    algKwargs: dictionary, default={}
       Optional keyword arguments to pass to the clustering algorithm
       constructor.

    Returns:
    --------
    '''

    args = (ClustAlg, nSamples, nProcesses, cutoff, algKwargs)
    reduced = pd.DataFrame(DimAlg(data.__array__()))
    reduced.index = data.index
    k, labels = gapStatistic(data, *args)

    if k == 1:
        return {'k': 1}

    else:
        clusters = [data.index[labels == i].__array__() for i in range(k)]
        subclusters = [hCluster(data.loc[inds], DimAlg, *args) for inds in clusters]
        return {'k': k, 'clusters': clusters, 'subclusters': subclusters}

def _factor(data, k, alpha, beta, frac, seed):
    from pyper import R
    r = R()

    r.m = data
    r.seed, r.k, r.alpha, r.beta, r.frac, r.seed = seed, k, alpha, beta, frac, seed

    r.run([
        'library(NNLM)',
        'set.seed(seed)',
        'inds <- sample(length(m), frac*length(m))',
        'targets <- m[inds]',
        'm[inds] <- NA',
        'res <- nnmf(m, k, alpha=c(0, 0, alpha), beta=c(0, 0, beta))',
        'predictions <- with(res, W %*% H)[inds]',
        'sse <- sum((predictions - targets)^2)'
    ])
