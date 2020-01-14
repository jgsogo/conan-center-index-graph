
import os
from datetime import date

from graphviz import Digraph


class Node:
    def __init__(self, name, is_draft):
        self.name = name
        self.versions = set()
        self.profiles = set()
        self.is_draft = is_draft


class Edge:
    def __init__(self, origin, target, is_draft):
        self.origin = origin
        self.target = target
        self.profiles = set()
        self.is_draft = is_draft


class Graph:
    nodes = {}
    edges = {}

    color_default = 'black'
    color_draft = 'gray70'

    def add_node(self, ref, profile=None, is_draft=False):
        name, version = ref.split('/')
        node = self.nodes.setdefault(name, Node(name, is_draft=is_draft))
        node.versions.add(version)
        if profile:
            node.profiles.add(profile)
        return node

    def add_edge(self, ref_origin, ref_target, profile, is_draft=False):
        ori = self.add_node(ref_origin)
        ori.profiles.add(profile)
        dst = self.add_node(ref_target)
        dst.profiles.add(profile)
        edge = self.edges.setdefault((ori, dst), Edge(ori, dst, is_draft))
        edge.profiles.add(profile)
        return edge

    def export_graphviz(self):
        today = date.today().strftime("%B %d, %Y")
        dot = Digraph(name="Conan Center", strict=True)
        dot.attr(
            label='<<font point-size="20">Conan Center - {date}</font>>'.format(date=today))
        dot.attr(labelloc='bottom')
        dot.attr(labeljust='left')
        dot.graph_attr['ranksep'] = '2'

        for _, node in self.nodes.items():
            color = self.color_draft if node.is_draft else self.color_default
            label = '<<table color="{color}" border="0" cellborder="0"><tr><td><b><font color="{color}">{name}</font></b></td></tr>'.format(
                name=node.name, color=color)
            if node.versions:
                label += '<tr><td><font color="{color}" face="monospace" point-size="7">{versions}</font></td></tr>'.format(
                    versions=", ".join(node.versions), color=color)
            if not node.is_draft and node.profiles:
                label += '<tr><td><font color="{color}" face="monospace" point-size="7">{profiles}</font></td></tr>'.format(
                    profiles=", ".join([os.path.basename(pr) for pr in node.profiles]), color=color)
            label += '</table>>'
            dot.node(node.name, shape="rectangle", label=label, color=color)
        for edge, data in self.edges.items():
            # label = '<<font point-size="7">{}</font>>'.format("".join([os.path.basename(it)[:1] for it in data.profiles]))  # Just the first letter
            label = None
            color = self.color_draft if data.is_draft else self.color_default
            dot.edge(edge[0].name, edge[1].name, label=label, color=color)

        #dot.edge(ori, dst, style="dashed", color="grey")
        return dot

    def export_cytoscape(self):
        ret = []
        for _, node in self.nodes.items():
            node_type = "draft" if node.is_draft else "regular"
            ret.append({'data': {
                "type": node_type,
                "id": node.name,
                "name": node.name,
                "versions": ", ".join(node.versions),
                "profiles": ", ".join([os.path.basename(pr) for pr in node.profiles])
            }})

        for edge, data in self.edges.items():
            edge_type = "draft" if data.is_draft else "regular"
            ret.append({'data': {
                "source": edge[0].name,
                "target": edge[1].name,
                "etype": edge_type,
            }})

        return ret