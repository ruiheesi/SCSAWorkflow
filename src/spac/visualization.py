import seaborn
import scanpy as sc
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


def histogram(adata, column, group_by=None, together=False, **kwargs):
    """
    Plot the histogram of cells based specific column.

    Parameters
    ----------
    adata : anndata.AnnData
         The AnnData object.

    column : str
        Name of member of adata.obs to plot the histogram.

    group_by : str, default None
        Choose either to group the histogram by another column.

    together : bool, default False
        If True, and if group_by !=None  create one plot for all groups.
        Otherwise, divide every histogram by the number of elements.

    **kwargs
        Parameters passed to matplotlib hist function.

    Returns
    -------
    ax : matplotlib.axes.Axes
        The axes of the histogram plot.

    fig : matplotlib.figure.Figure
        The created figure for the plot.

    """
    n_bins = len(adata.obs[column].unique()) - 1
    print("nbins=", n_bins)

    arrays = []
    labels = []

    if group_by is not None:
        groups = adata.obs[group_by].unique().tolist()
        observations = pd.concat(
            [adata.obs[column], adata.obs[group_by]],
            axis=1)

        for group in groups:
            group_cells = (observations[observations[group_by] ==
                           group][column].to_numpy())

            arrays.append(group_cells)
            labels.append(group)

        if together:
            fig, ax = plt.subplots()
            ax.hist(arrays, n_bins, label=labels, **kwargs)
            ax.legend(
                prop={'size': 10},
                bbox_to_anchor=(1.05, 1),
                loc='upper left',
                borderaxespad=0.)
            ax.set_title(column)
            return ax, fig

        else:
            n_groups = len(groups)
            fig, ax = plt.subplots(n_groups)
            fig.tight_layout(pad=1)
            fig.set_figwidth(5)
            fig.set_figheight(5*n_groups)

            for group, ax_id in zip(groups, range(n_groups)):
                ax[ax_id].hist(arrays[ax_id], n_bins, **kwargs)
                ax[ax_id].set_title(group)
            return ax, fig

    else:
        fig, ax = plt.subplots()
        array = adata.obs[column].to_numpy()
        plt.hist(array, n_bins, label=column, **kwargs)
        ax.set_title(column)
        return ax, fig


def heatmap(adata, column, layer=None, **kwargs):
    """
    Plot the heatmap of the mean feature of cells that belong to a `column`.

    Parameters
    ----------
    adata : anndata.AnnData
         The AnnData object.

    column : str
        Name of member of adata.obs to plot the histogram.

    layer : str, default None
        The name of the `adata` layer to use to calculate the mean feature.

    **kwargs:
        Parameters passed to seaborn heatmap function.

    Returns
    -------
    pandas.DataFrame
        A dataframe tha has the labels as indexes the mean feature for every
        marker.

    matplotlib.figure.Figure
        The figure of the heatmap.

    matplotlib.axes._subplots.AxesSubplot
        The AsxesSubplot of the heatmap.

    """
    features = adata.to_df(layer=layer)
    labels = adata.obs[column]
    grouped = pd.concat([features, labels], axis=1).groupby(column)
    mean_feature = grouped.mean()

    n_rows = len(mean_feature)
    n_cols = len(mean_feature.columns)
    fig, ax = plt.subplots(figsize=(n_cols * 1.5, n_rows * 1.5))
    seaborn.heatmap(
        mean_feature,
        annot=True,
        cmap="Blues",
        square=True,
        ax=ax,
        fmt=".1f",
        cbar_kws=dict(use_gridspec=False, location="top"),
        linewidth=.5,
        annot_kws={"fontsize": 10},
        **kwargs)

    ax.tick_params(axis='both', labelsize=25)
    ax.set_ylabel(column, size=25)

    return mean_feature, fig, ax


def hierarchical_heatmap(
        adata,
        column,
        layer=None,
        dendrogram=True,
        standard_scale=None,
        **kwargs):
    """
    Plot a hierarchical clustering heatmap of the mean
    feature of cells that belong to a `column' using
    scanpy.tl.dendrogram and sc.pl.matrixplot.

    Parameters
    ----------
    adata : anndata.AnnData
        The AnnData object.
    column : str
        Name of the column in adata.obs to group by and
        calculate mean feature.
    layer : str, optional, default: None
        The name of the `adata` layer to use to calculate the mean feature.
    dendrogram : bool, optional, default: True
        If True, a dendrogram based on the hierarchical clustering between
        the `column` categories is computed and plotted.
    **kwargs:
        Additional parameters passed to sc.pl.matrixplot function.

    Returns
    ----------
    feature, matrixplot

    """

    """
    # An example to call this function:
    mean_feature, matrixplot = hierarchical_heatmap(all_data,
    "phenograph", layer=None, standard_scale='var')

    # Display the figure
    #matrixplot.show()
    """

    # Calculate mean feature
    features = adata.to_df(layer=layer)
    labels = adata.obs[column]
    grouped = pd.concat([features, labels], axis=1).groupby(column)
    mean_feature = grouped.mean()

    # Reset the index of mean_feature
    mean_feature = mean_feature.reset_index()

    # Convert mean_feature to AnnData
    mean_feature_adata = sc.AnnData(
        X=mean_feature.iloc[:, 1:].values,
        obs=pd.DataFrame(
            index=mean_feature.index,
            data={column: mean_feature.iloc[:, 0].astype('category').values}
        ),
        var=pd.DataFrame(index=mean_feature.columns[1:]))

    # Compute dendrogram if needed
    if dendrogram:
        sc.tl.dendrogram(
            mean_feature_adata,
            groupby=column,
            var_names=mean_feature_adata.var_names,
            n_pcs=None)

    # Create the matrix plot
    matrixplot = sc.pl.matrixplot(
        mean_feature_adata,
        var_names=mean_feature_adata.var_names,
        groupby=column,
        use_raw=False,
        dendrogram=dendrogram,
        standard_scale=standard_scale,
        cmap="viridis",
        return_fig=True,
        **kwargs)

    return mean_feature, matrixplot


def threshold_heatmap(adata, marker_cutoffs, phenotype):
    """
    Creates a heatmap for each marker, categorizing features into
    low, medium, and high based on provided cutoffs.

    Parameters
    ----------
    adata : anndata.AnnData
        AnnData object containing the marker features in .X attribute.

    marker_cutoffs : dict
        Dictionary with marker names as keys and tuples with two
        features cutoffs
        as values.

    phenotype : str
        Column name in .obs DataFrame that contains the phenotype
        used for grouping.

    Returns
    -------
    Dictionary of :class:`~matplotlib.axes.Axes`
        A dictionary contains the axes of figures generated in the
        scanpy heatmap function.
        Consistent Key: 'heatmap_ax'
        Potential Keys includes: 'groupby_ax', 'dendrogram_ax',
        and 'gene_groups_ax'.

    """

    """
    # Current function returns a Matplotlib figure object.
    # Use the code below to display the heatmap when the function is called:

    heatmap_figure = threshold_heatmap(adata, marker_cutoffs, phenotype)
    plt.show()

    """
    # Save marker_cutoffs in the AnnData object
    adata.uns['marker_cutoffs'] = marker_cutoffs

    feature_df = pd.DataFrame(
        index=adata.obs_names,
        columns=marker_cutoffs.keys())

    for marker, cutoffs in marker_cutoffs.items():
        low_cutoff, high_cutoff = cutoffs
        marker_values = adata[:, marker].X.flatten()
        feature_df.loc[marker_values <= low_cutoff, marker] = 0
        feature_df.loc[
            (marker_values > low_cutoff) & (marker_values <= high_cutoff),
            marker] = 1
        feature_df.loc[marker_values > high_cutoff, marker] = 2

    feature_df = feature_df.astype(int)

    # Add the feature_df to adata as an AnnData layer
    adata.layers["feature"] = feature_df.to_numpy()

    # Convert the phenotype column to categorical
    adata.obs[phenotype] = adata.obs[phenotype].astype('category')

    # Create a custom color map for the heatmap
    color_map = {
        0: (0/255, 0/255, 139/255),
        1: 'green',
        2: 'yellow',
    }
    colors = [color_map[i] for i in range(3)]
    cmap = ListedColormap(colors)

    # Plot the heatmap using scanpy.pl.heatmap
    heatmap_plot = sc.pl.heatmap(
        adata,
        var_names=feature_df.columns,
        groupby=phenotype,
        use_raw=False,
        layer='feature',
        cmap=cmap,
        swap_axes=True,
        show=False)

    return heatmap_plot
