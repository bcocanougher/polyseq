import numpy as np
import pandas as pd

from polyseq.utils import cluster_arg_sort

class ExpressionMatrix(pd.DataFrame):

    # def __init__(self, array):
    #
    #     if type(array) is  np.ndarray:
    #         self.data = pd.DataFrame(array)
    #     elif type(array) is pd.DataFrame:
    #         self.data = array
    #     else:
    #         raise ValueError("unknown data type for an Expression matrix")
    #
    # def __repr__(self):
    #     return self.data.__repr__()
    #
    # def _repr_html_(self):
    #     return self.data._repr_html_()
    #
    # def head(self, n=5):
    #     return ExpressionMatrix(self.data.head(n))
    #
    # @property
    # def shape(self):
    #     return self.data.shape

    def drop_cells(self, reads=None, num_genes=None, genes=None, read_threshold=1):

        if isinstance(genes, (int, str)):
            genes = [genes]

        relevant = self if genes is None else self[genes]

        subset = self
        if reads is not None:
            subset = subset[relevant.sum(axis=1) >= reads]
        if num_genes is not None:
            subset = subset[(relevant >= read_threshold).sum(axis=1) >= num_genes]

        return ExpressionMatrix(subset)

    def drop_genes(self, reads=None, num_cells=None, read_threshold=1):

        subset = self
        if reads is not None:
            subset = subset.loc[:, subset.sum(axis=0) >= reads]
        if num_cells is not None:
            subset = subset.loc[:, (subset >= read_threshold).sum(axis=0) >= num_cells]

        return ExpressionMatrix(subset)

    def sort(self, sort_cells=True, sort_genes=True, genes=None):
        if genes is None:
            genes = slice(None, None, None)
        elif isinstance(genes, (int, str)):
            genes = [genes]

        if sort_cells:
            sorted = self.loc[self[genes].sum(axis=1).sort_values(ascending=False).index]
        else:
            sorted = self

        if sort_genes:
            sorted = sorted[sorted.sum(axis=0).sort_values(ascending=False).index]

        return ExpressionMatrix(sorted)

    def cluster_sort(self, sort_cells=True, sort_genes=True):

        if sort_cells:
            inds = cluster_arg_sort(self)
            result = self.iloc[inds]
        else:
            result = self

        if sort_genes:
            inds = cluster_arg_sort(result.T)
            result = result.iloc[:, inds]

        return ExpressionMatrix(result)

    def log_normalize(self):
        return ExpressionMatrix(np.log(self + 1))
