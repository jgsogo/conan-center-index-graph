Conan Center graph
==================

This is a community project to generate and maintain a graph of the libraries available in
[Conan Center](https://conan.io/center/) and the relations between them. The graph is published
in [this webpage](http://jgsogo.es/conan-center-index-graph/index.html).

![Conan Center index. Libraries available](https://jgsogo.es/conan-center-index-graph/graph.png)

How it works
------------

The graph is generated in several steps in a machine with [Conan client](https://conan.io)
installed:
 * All the recipes in [conan-center-index](https://github.com/conan-io/conan-center-index) are
   exported to the cache.
 * Optionally, several combinations of the options in each recipe are computed: to avoid the
   combinatorial explosion, we try to be smart (:crossfingers:) and assign only one value to
   options like `with_`, `enable_` in order to maximize the requirements and edges in the
   graph.
 * Profiles from [`conf`](conf) folder are considered.
 * A [graphlock](https://docs.conan.io/en/latest/reference/commands/misc/graph.html) for all
   these combinations is computed for every recipe.
 * All those graphlocks are combined into a single graph and exported to different formats.

The algorighm can include recipes in [`recipe_drafts`](recipe_drafts) that will increase the
connectivity of the graph and help to detect next efforts that maximize the community
throughoutput making more recipes into Conan Center.

