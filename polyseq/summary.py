import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from polyseq.viz import kde_plot, STYLE_CONTEXTS


def summarize(data, umi_threshold=1, plot=True):

    counts_by_cell = data.sum(axis=1)
    genes_expressed = (data >= umi_threshold).sum(axis=1)
    counts_by_gene = data.sum(axis=0)
    cells_expressed = (data > umi_threshold).sum(axis=0)

    # central_tendency = np.log(data + 1).mean(axis=0)
    # spread = np.log(data + 1).std(axis=0)
    # central_tendency = data.mean(axis=0)
    # spread = data.std(axis=0)
    #
    # good_inds = (central_tendency > 0) & (spread > 0)
    # central_tendency, spread = central_tendency[good_inds], spread[good_inds]
    # dispersion = spread/central_tendency

    data = data.__array__().flatten()
    distributions = {
        'umis': data,
        'umis above {}'.format(umi_threshold - 1): data[data >= umi_threshold],
        'umis per cell cell': counts_by_cell,
        'genes expressed': genes_expressed,
        'umis per gene': counts_by_gene,
        'cells expressing': cells_expressed,
    }

    stats = {
        'min': np.min,
        'max': np.max,
        'mean': np.mean,
        'median': np.median
    }

    result = pd.DataFrame()
    for dist_name, dist in distributions.items():
        df = pd.DataFrame()
        for stat_name, stat in stats.items():
            df[stat_name] = [int(np.round(stat(dist)))]
        df.index = [dist_name]
        result = pd.concat([result, df])

    if plot:

        with plt.style.context(STYLE_CONTEXTS):

            plt.figure(figsize=(20, 13))

            bw_factor = 20.0

            ax = plt.subplot(2, 2, 1)
            kde_plot(counts_by_cell, bw_factor=bw_factor)
            ax.set_xlabel('# of umis')
            ax.set_ylabel('density')
            ax.set_title('umis per cell')

            ax = plt.subplot(2, 2, 2)
            kde_plot(genes_expressed, bw_factor=bw_factor)
            ax.set_xlabel('# of genes expressed')
            ax.set_ylabel('density')
            ax.set_title('genes expressed per cell')

            ax = plt.subplot(2, 2, 3)
            kde_plot(counts_by_gene, bw_factor=bw_factor)
            ax.set_xlabel('# of umis')
            ax.set_ylabel('density')
            ax.set_title('umis per gene')

            ax = plt.subplot(2, 2, 4)
            kde_plot(cells_expressed, bw_factor=bw_factor)
            ax.set_xlabel('# of cells')
            ax.set_ylabel('density')
            ax.set_title('cells showing expression per gene')

            plt.figure(figsize=(20, 7))

            ax = plt.subplot(1, 2, 1)
            plt.scatter(counts_by_cell, genes_expressed, s=15)
            ax.set_xlabel('# of umis')
            ax.set_ylabel('# of genes expressed')
            ax.set_title('corr coef: {:.3f}'.format(np.corrcoef(np.vstack([counts_by_cell, genes_expressed]))[0, 1]))

            # ax = plt.subplot(1, 2, 2)
            # #ax.set_xscale('log')
            # #ax.set_yscale('log')
            # ax.scatter(central_tendency, dispersion, s=15)
            # ax.set_xlabel('umi median')
            # ax.set_ylabel('umi dispersion')

    return result
