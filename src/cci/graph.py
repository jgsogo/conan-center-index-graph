
import os
from datetime import date

from graphviz import Digraph
from collections import defaultdict


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

    def add_node(self, ref, profile, is_draft):
        node = self._add_node(ref)
        node.is_draft = is_draft
        node.profiles.add(profile)
        node.versions.add(ref.version)
        return node

    def _add_node(self, ref):
        return self.nodes.setdefault(ref.name, Node(ref.name, is_draft=None))

    def add_edge(self, ref_origin, ref_target, profile, is_draft):
        ori = self._add_node(ref_origin)
        dst = self._add_node(ref_target)
        edge = self.edges.setdefault((ori, dst), Edge(ori, dst, is_draft))
        edge.profiles.add(profile)
        return edge

    def compute_max_connected_component(self, include_drafts):
        # TODO: Improve this algorithm
        components = []
        _cmps_record = defaultdict(set)
        for (ori, dst), edge in self.edges.items():
            if not include_drafts and (ori.is_draft or dst.is_draft or edge.is_draft):
                continue
            for i, it in enumerate(components):
                if ori.name in it or dst.name in it:
                    it.add(ori.name)
                    it.add(dst.name)
                    _cmps_record[ori.name].add(i)
                    _cmps_record[dst.name].add(i)
                    break
            else:
                _cmps_record[ori.name].add(len(components))
                _cmps_record[dst.name].add(len(components))
                components.append({ori.name, dst.name})
        
        # Join the components
        ret = [set() for _ in range(len(components))]
        for _, v in _cmps_record.items():
            p = min(v)
            for it in v:
                ret[p].update(components[it])
                ret[p].update(ret[it])
                if it != p:
                    ret[it].clear()
                    components[it].clear()

        ret = [it for it in ret if len(it)]
        return ret

    def export_graphviz(self, include_drafts):
        today = date.today().strftime("%B %d, %Y")
        dot = Digraph(name="Conan Center", strict=True)
        dot.attr(label='<<font point-size="20">Conan Center - {date}</font>>'.format(date=today))
        dot.attr(labelloc='bottom')
        dot.attr(labeljust='left')
        dot.graph_attr['ranksep'] = '2'

        for _, node in self.nodes.items():
            if not include_drafts and node.is_draft:
                continue
            color = self.color_draft if node.is_draft else self.color_default
            label = '<<table color="{color}" border="0" cellborder="0"><tr><td><b><font color="{color}">{name}</font></b></td></tr>'.format(name=node.name, color=color)
            if node.versions:
                label += '<tr><td><font color="{color}" face="monospace" point-size="7">{versions}</font></td></tr>'.format(versions=", ".join(node.versions), color=color)
            if not node.is_draft and node.profiles:
                label += '<tr><td><font color="{color}" face="monospace" point-size="7">{profiles}</font></td></tr>'.format(profiles=", ".join([os.path.basename(pr) for pr in node.profiles]), color=color)
            label += '</table>>'
            dot.node(node.name, shape="rectangle", label=label, color=color)
        for edge, data in self.edges.items():
            if not include_drafts and data.is_draft:
                continue
            #label = '<<font point-size="7">{}</font>>'.format("".join([os.path.basename(it)[:1] for it in data.profiles]))  # Just the first letter
            label = None
            color = self.color_draft if data.is_draft else self.color_default
            dot.edge(edge[0].name, edge[1].name, label=label, color=color)

        #dot.edge(ori, dst, style="dashed", color="grey")
        return dot
