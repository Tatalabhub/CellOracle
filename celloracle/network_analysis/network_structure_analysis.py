# -*- coding: utf-8 -*-
'''
This is a series of custom functions for the inferring of GRN from single cell RNA-seq data.

Codes were written by Kenji Kamimoto.


'''

###########################
### 0. Import libralies ###
###########################


# 0.1. libraries for fundamental data science and data processing

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from scipy import stats

from tqdm import tqdm_notebook as tqdm
from .network_analysis_utility import linkList_to_networkgraph

#import seaborn as sns

settings = {"save_figure_as": "png"}

###################################
### Analyze degree distribution ###
###################################

def plot_degree_distributions(links, plot_model=False, save=None):
    """
    Plot the distribution of network degree (the number of edge per gene).
    Scatter plots in both linear scale and log scale will be generated.

    Args:
        links (Links object): See network_analisis.Links class for detail.
        plot_model (bool): Whether to plot linear approximation line.
        save (str): Folder path to save plots. If the folde does not exist in the path, the function create the folder.
            If None plots will not be saved. Default is None.

    """
    for i in links.cluster:
        print(i)

        g = linkList_to_networkgraph(links.filtered_links[i])
        degree_df = _get_degree_info_from_NG(g)
        _plotDegreedist(degree_df, plot_model)

        if not save is None:
            os.makedirs(save, exist_ok=True)
            path = os.path.join(save, f"degree_dist_{links.name}_{links.thread_number}_{i}.{settings['save_figure_as']}")
            plt.savefig(path, transparent=True)
        plt.show()


def _plotDegreedist(degree_df, plot_model=False):

    """
    Args:
        degree_df (pandas.DataFrame): data_frame that include degree.
            degree info shold be stored in the column, "degree"

        plot_model (bool): Whether to plot linear approximation line.

        save (str): Folder path to save plots. If the folde does not exist in the path, the function create the folder.
            If None plots will not be saved. Default is None.
    """

    from sklearn.linear_model import LinearRegression as lr
    df = degree_df.copy()

    dist = df.degree.value_counts()/df.degree.value_counts().sum()
    dist.index = dist.index.astype(np.int)
    plt.subplot(1,2,1)
    plt.scatter(dist.index.values, dist.values, c="black")
    plt.title("degree distribution")
    plt.xlabel("k")
    plt.ylabel("P(k)")

    plt.subplot(1,2,2)
    #plt.yscale('log')
    #plt.xscale('log')

    x = np.log(dist.index.values).reshape([-1,1])
    y = np.log(dist.values).reshape([-1,1])
    if plot_model:
        model = lr()
        model.fit(x,y)
        x_ = np.array([-1, 5]).reshape([-1,1])
        y_ = model.predict(x_)
        plt.title(f"degree distribution (log scale)\nslope: {model.coef_[0][0] :.4g}, r2: {model.score(x,y) :.4g}")
        plt.plot(x_.flatten(), y_.flatten(), c="black", alpha=0.5)
    else:

        plt.title(f"degree distribution (log scale)")
    plt.scatter(x.flatten(), y.flatten(), c="black")
    plt.ylim([y.min()-0.2, y.max()+0.2])
    plt.xlim([-0.2, x.max()+0.2])
    plt.xlabel("log P(k)")
    plt.ylabel("log k")

def _get_degree_info_from_NG(network_x_graph):

    df = pd.DataFrame(np.array(network_x_graph.degree))
    df.columns = ["ind", "degree"]
    df = df.set_index("ind")

    return df

def plot_score_discributions(links, values=None, method="boxplot", save=None):
    """
    Plot the distribution of network scores listed below.
    Indivisual data point is network edge (gene) of GRN in each cluster.

    Network scores
        ['clustering_coefficient', 'clustering_coefficient_weighted',
         'degree_centrality_all', 'degree_centrality_in', 'degree_centrality_out',
         'betweenness_centrality', 'closeness_centrality',
         'eigenvector_centrality', 'assortative_coefficient',
         'average_path_length']

    Args:
        links (Links object): See network_analisis.Links class for detail.
        values (list of str): The list of netwrok score type. If it is None, all network score (listed above) will be used.
        method (str): Plotting method. Select one from "boxplot" or "barplot".
        save (str): Folder path to save plots. If the folde does not exist in the path, the function create the folder.
            If None plots will not be saved. Default is None.
    """
    col = ['clustering_coefficient',
   'clustering_coefficient_weighted', 'degree_centrality_all',
   'degree_centrality_in', 'degree_centrality_out',
   'betweenness_centrality', 'closeness_centrality',
   'eigenvector_centrality', 'assortative_coefficient',
   'average_path_length']
    if values is None:
        values = col
    if method == "boxplot":
        for i in values:
            print(i)
            sns.boxplot(data=links.merged_score,
                        x="cluster", y=i, palette=links.palette.palette.values,
                        order=links.palette.index.values, fliersize=0.3)
            plt.xticks(rotation=90)
            if not save is None:
                os.makedirs(save, exist_ok=True)
                path = os.path.join(save, f"boxplot_{i}_in_{links.name}_{links.thread_number}.{settings['save_figure_as']}")
                #plt.ylabel("{}\nentropy")
                plt.savefig(path, transparent=True)
            plt.show()
    elif method == "barplot":
        for i in values:
            print(i)
            sns.barplot(data=links.merged_score,
                        x="cluster", y=i, palette=links.palette.palette.values,
                        order=links.palette.index.values)
            plt.xticks(rotation=90)
            if not save is None:
                os.makedirs(save, exist_ok=True)
                path = os.path.join(save, f"barplot_{i}_in_{links.name}_{links.thread_number}.{settings['save_figure_as']}")
                #plt.ylabel("{}\nentropy")
                plt.savefig(path, transparent=True)
            plt.show()



################################
### Network Entropy analysis ###
################################

def plot_network_entropy_distributions(links, update_network_entropy=False, save=None):
    """
    Plot the distribution of network entropy.
    See the CellOracle paper for the detail.

    Args:
        links (Links object): See network_analisis.Links class for detail.
        values (list of str): The list of netwrok score type. If it is None, all network score (listed above) will be used.
        update_network_entropy (bool): Whether to recalculate network entropy.
        save (str): Folder path to save plots. If the folde does not exist in the path, the function create the folder.
            If None plots will not be saved. Default is None.
    """
    if links.entropy is None:
        links.get_network_entropy()

    if update_network_entropy:
        links.get_network_entropy()

    sns.boxplot(data=links.entropy, x="cluster", y="entropy_norm",
                palette=links.palette.palette.values,
                order=links.palette.index.values, fliersize=0.3)
    plt.xticks(rotation=90)
    plt.ylim([0.81,0.98])

    if not save is None:
        os.makedirs(save, exist_ok=True)
        path = os.path.join(save, f"network_entropy_in_{links.name}_{links.thread_number}.{settings['save_figure_as']}")
        plt.ylabel("normalized\nentropy")
        plt.savefig(path, transparent=True)
    plt.show()
