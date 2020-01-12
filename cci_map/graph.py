
import os
from graphviz import Digraph
from datetime import date


class Node:
    def __init__(self, name):
        self.name = name
        self.versions = set()
        self.profiles = set()


class Edge:
    def __init__(self, origin, target):
        self.origin = origin
        self.target = target
        self.profiles = set()


class Graph:
    nodes = {}
    edges = {}

    def add_node(self, ref, profile=None):
        name, version = ref.split('/')
        node = self.nodes.setdefault(name, Node(name))
        node.versions.add(version)
        if profile:
            node.profiles.add(profile)
        return node

    def add_edge(self, ref_origin, ref_target, profile):
        ori = self.add_node(ref_origin)
        ori.profiles.add(profile)
        dst = self.add_node(ref_target)
        dst.profiles.add(profile)
        edge = self.edges.setdefault((ori, dst), Edge(ori, dst))
        edge.profiles.add(profile)
        return edge

    def export_graphviz(self):
        today = date.today().strftime("%B %d, %Y")
        dot = Digraph(name="Conan Center", strict=True)
        dot.attr(label='<<font point-size="20">Conan Center - {date}</font>>'.format(date=today))
        dot.attr(labelloc='bottom')
        dot.attr(labeljust='left')
        dot.graph_attr['ranksep'] = '2'

        for _, node in self.nodes.items():
            label = '<<table border="0" cellborder="0"><tr><td><b>{name}</b></td></tr>'.format(name=node.name)
            if node.versions:
                label += '<tr><td><font face="monospace" point-size="7">{versions}</font></td></tr>'.format(versions=", ".join(node.versions))
            if node.profiles:
                label += '<tr><td><font face="monospace" point-size="7">{profiles}</font></td></tr>'.format(profiles=", ".join([os.path.basename(pr) for pr in node.profiles]))
            label += '</table>>'      
            dot.node(node.name, shape="rectangle", label=label)
        for edge, data in self.edges.items():
            #label = '<<font point-size="7">{}</font>>'.format("".join([os.path.basename(it)[:1] for it in data.profiles]))  # Just the first letter
            label = None
            dot.edge(edge[0].name, edge[1].name, label=label)

        #dot.edge(ori, dst, style="dashed", color="grey")
        return dot
