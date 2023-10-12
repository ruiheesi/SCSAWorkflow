import squidpy as sq
import matplotlib.pyplot as plt
import pandas as pd
import anndata
import pickle
import io
from spac.utils import check_annotation


def spatial_interaction(
        adata,
        annotation,
        analysis_method,
        stratify_by=None,
        ax=None,
        return_matrix=False,
        **kwargs):
    """
    Perform spatial analysis on the selected annotation in the dataset.
    Current analysis methods are provided in squidpy:
        Neighborhood Enrichment,
        Cluster Interaction Matrix
    Parameters:
    -----------
        adata : anndata.AnnData
            The AnnData object.

        annotation : str
            The column name of the annotation to analysis in the dataset.

        analysis_method : str
            The analysis method to use, currently available:
            "Neighborhood Enrichment" and "Cluster Interaction Matrix".

        stratify_by : str or list of strs
            The annotation[s] to stratify the dataset when generating
            interaction plots. If single annotation is passed, the dataset
            will be stratified by the unique labels in the annotation column.
            If n (n>=2) annotations are passed, the function will be stratified
            based on existing combination of labels in the passed annotations.

        ax: matplotlib.axes.Axes, default None
            The matplotlib Axes to display the image.

        return_matrix: boolean, default False
            If true, the fucntion will return a list of two dictionaries,
            the first contains axes and the second containing computed matrix.
            Note that for Neighborhood Encrichment, the matrix will be a tuple
            with the z-score and the enrichment count.
            For Cluster Interaction Matrix, it will returns the
            interaction matrix.
            If False, the function will return only the axes dictaionary.

        **kwargs
            Keyword arguments for matplotlib.pyplot.text()
    Returns:
    -------
        ax_dictionary : dictionary of matplotlib.axes.Axes
            A dictionary of the matplotlib Axes containing the analysis plots.
            If not stratify, the key for analysis will be "Full",
            otherwise the plot will be stored with key <stratify combination>.
            The returned ax is the passed ax or new ax created.
    """

    # List all available methods
    available_methods = [
        "Neighborhood Enrichment",
        "Cluster Interaction Matrix"
    ]
    available_methods_str = ",".join(available_methods)

    # pacakge each methods into a function to allow
    # centralized control and improve flexibility
    def Neighborhood_Enrichment_Analysis(
                adata,
                new_annotation_name,
                ax,
                return_matrix=False
            ):

        # Calculate Neighborhood_Enrichment
        if return_matrix:
            matrix = sq.gr.nhood_enrichment(
                        adata,
                        copy=True,
                        cluster_key=new_annotation_name
                )

            sq.gr.nhood_enrichment(
                        adata,
                        cluster_key=new_annotation_name
                )
        else:
            sq.gr.nhood_enrichment(
                        adata,
                        cluster_key=new_annotation_name
                )

        # Plot Neighborhood_Enrichment
        sq.pl.nhood_enrichment(
                    adata,
                    cluster_key=new_annotation_name,
                    ax=ax,
                    **kwargs
            )

        if return_matrix:
            return [ax, matrix]
        else:
            return ax

    def Cluster_Interaction_Matrix_Analysis(
                adata,
                new_annotation_name,
                ax,
                return_matrix=False
            ):

        # Calculate Cluster_Interaction_Matrix

        if return_matrix:
            matrix = sq.gr.interaction_matrix(
                    adata,
                    cluster_key=new_annotation_name,
                    copy=True
            )

            sq.gr.interaction_matrix(
                    adata,
                    cluster_key=new_annotation_name
            )

        else:
            sq.gr.interaction_matrix(
                    adata,
                    cluster_key=new_annotation_name
            )

        # Plot Cluster_Interaction_Matrix
        sq.pl.interaction_matrix(
                    adata,
                    cluster_key=new_annotation_name,
                    ax=ax,
                    **kwargs
            )

        if return_matrix:
            return [ax, matrix]
        else:
            return ax

    # Perfrom the actual analysis, first call sq.gr.spatial_neighbors
    # to calculate neighboring graph, then do different analysis.
    def perform_analysis(
            adata,
            analysis_method,
            new_annotation_name,
            ax,
            return_matrix=False
    ):

        sq.gr.spatial_neighbors(adata)

        if analysis_method == "Neighborhood Enrichment":
            ax = Neighborhood_Enrichment_Analysis(
                    adata,
                    new_annotation_name,
                    ax,
                    return_matrix)

        elif analysis_method == "Cluster Interaction Matrix":
            ax = Cluster_Interaction_Matrix_Analysis(
                    adata,
                    new_annotation_name,
                    ax,
                    return_matrix)

        return ax

    # Error Check Section
    # -----------------------------------------------
    if not isinstance(adata, anndata.AnnData):
        error_text = "Input data is not an AnnData object. " + \
            f"Got {str(type(adata))}"
        raise ValueError(error_text)

    # Check if annotation is in the dataset
    check_annotation(
        adata,
        [annotation]
    )

    # Check if stratify_by is list or list of str
    if stratify_by:
        if not isinstance(stratify_by, str):
            if isinstance(stratify_by, list):
                for item in stratify_by:
                    check_annotation(
                        adata,
                        item
                    )
            else:
                error_text = "The stratify_by variable should be " + \
                    "single string or a list of string, currently is" + \
                    f"{type(stratify_by)}"
                raise ValueError(error_text)
        else:
            check_annotation(
                adata,
                stratify_by
            )

    if not isinstance(analysis_method, str):
        error_text = "The analysis methods must be a string."
        raise ValueError(error_text)
    else:
        if analysis_method not in available_methods:
            error_text = f"Method {analysis_method}" + \
                " is not supported currently. " + \
                f"Available methods are: {available_methods_str}"
            raise ValueError(error_text)

    if ax is not None:
        if not isinstance(ax, plt.Axes):
            error_text = "Invalid 'ax' argument. " + \
                "Expected an instance of matplotlib.axes.Axes. " + \
                f"Got {str(type(ax))}"
            raise ValueError(error_text)
    else:
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)

    # Operational Section
    # -----------------------------------------------

    # Create a categorical column data for plotting
    new_annotation_name = annotation + "_plot"

    adata.obs[new_annotation_name] = pd.Categorical(
        adata.obs[annotation])

    if stratify_by:
        if isinstance(stratify_by, list):
            adata.obs[
                'concatenated_obs'
            ] = adata.obs[stratify_by].astype(str).agg('_'.join, axis=1)
        else:
            adata.obs[
                'concatenated_obs'
            ] = adata.obs[stratify_by]

    # Compute a connectivity matrix from spatial coordinates
    if stratify_by:
        ax_dictionary = {}
        matrix_dictionary = {}
        unique_values = adata.obs['concatenated_obs'].unique()
        buffer = io.BytesIO()
        pickle.dump(ax, buffer)
        for subset_key in unique_values:
            # Subset the original AnnData object based on the unique value
            subset_adata = adata[
                adata.obs[
                    'concatenated_obs'
                ] == subset_key
            ].copy()

            buffer.seek(0)

            ax_copy = pickle.load(buffer)

            ax_copy = perform_analysis(
                            subset_adata,
                            analysis_method,
                            new_annotation_name,
                            ax_copy,
                            return_matrix
                        )

            if return_matrix:
                ax_dictionary[subset_key] = ax_copy[0]
                matrix_dictionary[subset_key] = ax_copy[1]
            else:
                ax_dictionary[subset_key] = ax_copy

            del subset_adata

        if return_matrix:
            results = [
                {"Ax": ax_dictionary},
                {"Matrix": matrix_dictionary}
            ]
        else:
            results = ax_dictionary

    else:
        ax = perform_analysis(
                adata,
                analysis_method,
                new_annotation_name,
                ax,
                return_matrix
            )

        if return_matrix:
            results = [
                {"Ax": ax[0]},
                {"Matrix": ax[1]}
            ]
        else:
            results = {"Full": ax}

    return results
