import json

def packages_list(graph, output_filepath):
    # Dump list of requirements (to be used by TapaholesList)
    nodelist = []
    edges = {}
    for edge, _ in graph.edges.items():
        edges.setdefault(edge[0].name, []).append(edge[1].name)
    nodes_seen = []
    for name, data in graph.nodes.items():
        if name not in edges.keys():
            for v in data.versions:
                nodelist.append(f'{name}/{v}')
            nodes_seen.append(name)

    while edges:
        for edge, reqs in edges.items():
            if all([it in nodes_seen for it in reqs]):
                for v in graph.nodes[edge].versions:
                    nodelist.append(f'{edge}/{v}')
                nodes_seen.append(edge)
                edges.pop(edge)
                break

    with open(output_filepath, 'w') as outfile:
        json.dump(nodelist, outfile)


def packages_deps(graph, output_filepath):
    # List of packages with dependencies (JSON format)
    nodelist = {}

    edges = {}
    for edge, _ in graph.edges.items():
        edges.setdefault(edge[0].name, []).append(edge[1].name)
    
    # First the nodes without dependencies
    for name, data in graph.nodes.items():
        if name not in edges.keys():
            for v in data.versions:
                nodelist[f'{name}/{v}'] = []

    # Now add nodes with dependencies
    for edge, reqs in edges.items():
        reqs_refs = []
        for n in reqs:
            reqs_refs.extend([f'{n}/{v}' for v in graph.nodes[n].versions])

        for v in graph.nodes[edge].versions:
            nodelist[f'{edge}/{v}'] = reqs_refs

    with open(output_filepath, 'w') as outfile:
        json.dump(nodelist, outfile)
