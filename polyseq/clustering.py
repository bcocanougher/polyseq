import numpy as np

def getLogW(data, Algorithm, k, algKwargs):
    '''
    Compute log(sum of squared distances from cluster)
    '''
    alg = Algorithm(n_clusters=k, **algKwargs)
    distsToCenters = alg.fit_transform(data)
    labels = alg.labels_
    return np.log(np.sum(np.choose(labels, distsToCenters.T)**2))

def generateSample(bounds, mean, pca, n):
    '''
    Generate a sample from the null distribution
    '''
    proj = [np.random.uniform(low=l, high=h, size=n) for (l, h) in bounds]
    proj = np.array(proj).T
    orig = pca.inverse_transform(proj)
    return mean + orig

def gapStatistic(data, Algorithm, nSamples, algKwargs={}):
    '''
    Determine the number of clusters via the gap statistic method

    Tibsharani, Walther, & Hastie; J.R. Statist. Soc. B, 2001

    Parameters:
    -----------

    Returns:
    --------
    '''
    n, k = data.shape

    # compute parameters of null distribution
    from sklearn.decomposition import PCA
    mean = data.mean(axis=0)
    centered = data - mean
    pca = PCA(n_components=k).fit(centered)
    proj = pca.transform(data)

    bounds = [(v.min(), v.max()) for v in proj.T]
    k=1
    gapLast = 0
    while True:
        # cluster true data
        logW = getLogW(data, Algorithm, k, algKwargs)
        # create and cluster data from null distribution
        samples = []
        #TODO: parallelize this loop for multithreaded execution
        for _ in range(nSamples):
            sample = generateSample(bounds, mean, pca, n)
            samples.append(getLogW(sample, Algorithm, k, algKwargs))
        logWStar = np.mean(sample)
        gap = logWStar - logW
        deltaGap = gap - gapLast
        print k, deltaGap
        gapLast = gap
        k += 1
        if k == 2:
            continue
        if deltaGap < 0:
            k -= 2
            break
        if k > 10:
            print("exiting early")
            break
