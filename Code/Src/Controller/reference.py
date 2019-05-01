# -*- coding: utf-8 -*-
"""
Created on Wed May 1 13:25:25 2019

@author: ls
"""
import numpy as np


g = {  # manually tuned
     '000': [('100', ((.0, .0), -1)), ('010', ((0, 0), 1)),
             ('000', ((0, 0), 0))],

     '100': [('000', ((0, 0), 0)),
             ('100f', ((0, .71), 1)), ('100f', ((.2, .2), -90)),
             ('100f', ((.1, .53), -30)), ('102', ((.15, .4), -60))],
     '100f': [('100df', None)],
     '100df': [('010', ((0, .71), 1)), ('104', ((.2, .2), -90)),
               ('101', ((.1, .53), -30))],
     '104': [('104f', None)],
     '104f': [('104df', None)],
     '104df': [('105', None)],
     '105': [('105f', None)],
     '105f': [('105df', None)],
     '105df': [('106', ((0, .2), -130)), ('107', ((0, .4), -70))],
     '106': [('106f', None)],
     '106f': [('106df', None)],
     '106df': [('105', None)],
     '107': [('107f', None)],
     '107f': [('107df', None)],
     '107df': [('100', None)],
     '101': [('101d', None)],
     '101d': [('101df', None)],
     '101df': [('100', None)],
     '102': [('102f', None)],
     '102f': [('102df', None)],
     '102df': [('103', None)],
     '103': [('103f', None)],
     '103f': [('103df', None)],
     '103df': [('102', ((0, .4), -30)), ('100', ((0, .6), -15))],

     '010': [('000', ((0, 0), 0)),
             ('010f', ((0, .71), -1)), ('010f', ((-.2, .2), 90)),
             ('010f', ((-.1, .53), 30)), ('012', ((-.15, .4), 60))],
     '010f': [('010df', None)],
     '010df': [('100', ((0, .71), -1)), ('014', ((-.2, .2), 90)),
               ('011', ((-.1, .53), 30))],
     '014': [('014f', None)],
     '014f': [('014df', None)],
     '014df': [('015', None)],
     '015': [('015f', None)],
     '015f': [('015df', None)],
     '015df': [('016', ((0, .2), 130)), ('017', ((0, .4), 70))],
     '016': [('016f', None)],
     '016f': [('016df', None)],
     '016df': [('015', None)],
     '017': [('017f', None)],
     '017f': [('017df', None)],
     '017df': [('010', None)],
     '011': [('011d', None)],
     '011d': [('011df', None)],
     '011df': [('010', None)],
     '012': [('012f', None)],
     '012f': [('012df', None)],
     '012df': [('013', None)],
     '013': [('013f', None)],
     '013f': [('013df', None)],
     '013df': [('012', ((0, .4), 30)), ('010', ((0, 0.6), 15))]
    }

ref = {
     '000': [[0, 0, 0, 0, 0], [0, 0, 0, 0], .1],

     '100': [[0, 90, 90, 0, 90], [0, 1, 1, 0], .8],
     '100f': [[0, 90, 90, 0, 90], [1, 1, 1, 1], .1],
     '100df': [[0, 90, 90, 0, 90], [1, 0, 0, 1], .1],

     '104': [[50, 30, 90, 30, 150], [1, 0, 0, 1], .8],
     '104f': [[50, 30, 90, 30, 150], [1, 1, 1, 1], .1],
     '104df': [[50, 30, 90, 30, 150], [0, 1, 1, 0], .1],
     
     '105': [[124, 164, 152, 62, 221], [0, 1, 1, 0], .8],
     '105f': [[124, 164, 152, 62, 221], [1, 1, 1, 1], .1],
     '105df': [[124, 164, 152, 62, 221], [1, 0, 0, 1], .1],

     '106': [[0, 0, 24, 0, 0], [1, 0, 0, 1], .8],
     '106f': [[0, 0, 24, 0, 0], [1, 1, 1, 1], .1],
     '106df': [[0, 0, 24, 0, 0], [0, 1, 1, 0], .1],

     '107': [[30, 90, 80, 10, 10], [1, 0, 0, 1], .8],
     '107f': [[30, 90, 80, 10, 10], [1, 1, 1, 1], .1],
     '107df': [[30, 90, 80, 10, 10], [0, 1, 1, 0], .1],

     '101': [[40, 1, -10, 60, 10], [1, 0, 0, 1], .8],
     '101f': [[40, 1, -10, 60, 10], [1, 1, 1, 1], .1],
     '101df': [[40, 1, -10, 60, 10], [0, 1, 1, 0], .1],

     '102': [[48, 104, 114, 27, 124], [0, 1, 1, 0], .8],
     '102f': [[48, 104, 114, 27, 124], [1, 1, 1, 1], .1],
     '102df': [[48, 104, 114, 27, 124], [1, 0, 0, 1], .1],

     '103': [[1, 72, 70, 1, 55], [1, 0, 0, 1], .8],
     '103f': [[1, 72, 70, 1, 55], [1, 1, 1, 1], .1],
     '103df': [[1, 72, 70, 1, 55], [0, 1, 1, 0], .1],


     '010': [[90, 0, -90, 90, 0], [1, 0, 0, 1], .8],
     '010f': [[90, 0, -90, 90, 0], [1, 1, 1, 1], .1],
     '010df': [[90, 0, -90, 90, 0], [0, 1, 1, 1], .1],

     '014': [[30, 50, -90, 150, 30], [0, 1, 1, 0], .8],
     '014f': [[30, 50, -90, 150, 30], [1, 1, 1, 1], .1],
     '014df': [[30, 50, -90, 150, 30], [1, 0, 0, 1], .1],

     '015': [[164, 124, -152, 221, 62], [1, 0, 0, 1], .8],
     '015f': [[164, 124, -152, 221, 62], [1, 1, 1, 1], .1],
     '015df': [[164, 124, -152, 221, 62], [0, 1, 1, 0], .1],

     '016': [[0, 0, -24, 0, 0], [0, 1, 1, 0], .8],
     '016f': [[0, 0, -24, 0, 0], [1, 1, 1, 1], .1],
     '016df': [[0, 0, -24, 0, 0], [1, 0, 0, 1], .1],

     '017': [[90, 30, -80, 10, 10], [0, 1, 1, 0], .8],
     '017f': [[90, 30, -80, 10, 10], [1, 1, 1, 1], .1],
     '017df': [[90, 30, -80, 10, 10], [1, 0, 0, 1], .1],

     '011': [[1, 40, 10, 10, 60], [0, 1, 1, 0], .8],
     '011f': [[1, 40, 10, 10, 60], [1, 1, 1, 1], .1],
     '011df': [[1, 40, 10, 10, 60], [1, 0, 0, 1], .1],

     '012': [[104, 48, -114, 124, 27], [1, 0, 0, 1], .8],
     '012f': [[104, 48, -114, 124, 27], [1, 1, 1, 1], .1],
     '012df': [[104, 48, -114, 124, 27], [0, 1, 1, 0], .1],
     
     '013': [[72, 1, -70, 55, 1], [0, 1, 1, 0], .8],
     '013f': [[72, 1, -70, 55, 1], [1, 1, 1, 1], .1],
     '013df': [[72, 1, -70, 55, 1], [1, 0, 0, 1], .1]
      }


class ReferenceGenerator(object):
    def __init__(self, pose='000', graph=g, ref=ref):
        self.graph = Graph(graph)
        self.pose = pose
        self.ref = ref
        self.idx = 0
        self.last_deps = None

    def get_next_reference(self, act_position, act_eps, xref):
        xref = np.r_[xref]
        act_pos = np.r_[act_position]
        dpos = xref - act_pos
        act_dir = np.r_[np.cos(np.radians(act_eps)),
                        np.sin(np.radians(act_eps))]
        deps = calc_angle(dpos, act_dir)
        act_dist = np.linalg.norm(dpos)

        def suitability(translation_, rotation, v=None):
            translation_ = np.r_[translation_]
            # translation is configured for eps=90
            translation = rotate(translation_, np.radians(act_eps-90))
            dir_ = np.r_[np.cos(np.radians(act_eps+rotation)),
                         np.sin(np.radians(act_eps+rotation))]
            pos_ = act_pos + translation
            dist_ = np.linalg.norm(xref-pos_)
            deps_ = calc_angle(xref-pos_, dir_)

            return (dist_, deps_)

        if act_dist < 1:
            pose_id = '000'
        else:
            if len(self.graph.get_children(self.pose)) > 1:
                deps = {}
                ddist = {}
                for child in self.graph.get_children(self.pose):
                    v, (translation, rotation) = child
                    dist_, deps_ = suitability(translation, rotation, v)
                    deps[v] = deps_
                    ddist[v] = dist_

                min_deps = min([abs(deps[key]) for key in deps])
                max_deps = max([abs(deps[key]) for key in deps])
                min_ddist = min([ddist[key] for key in ddist])
                w = .5
                dec = {key: (w*ddist[key]/min_ddist
                             + (1-w)*abs(deps[key])/max_deps) for key in deps}
                print dec
                if min_deps > 70:  # ganz falsche Richtung
                    deps_ = {key: abs(deps[key]) for key in deps}
                    pose_id = min(deps_, key=deps_.get)
                else:
                    pose_id = min(dec, key=dec.get)

                self.last_deps = deps[pose_id]
            else:  # only 1 child
                pose_id, _ = self.graph.get_children(self.pose)[0]

        self.pose = pose_id
        self.idx += 1

        alpha, feet, process_time = self.__get_ref(pose_id)
        return alpha, feet, process_time

    def __get_ref(self, pose_id):
        return self.ref[pose_id]


def rotate(vec, theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.r_[c*vec[0]-s*vec[1], s*vec[0]+c*vec[1]]


def normalize(vec):
    x, y = vec
    leng = np.sqrt(x**2 + y**2)
    return np.r_[x/leng, y/leng]


def calc_angle(vec1, vec2, rotate_angle=0., jump=0):
    theta = np.radians(rotate_angle)
    vec1 = rotate(vec1, theta)
    x1, y1 = vec1  # normalize(vec1)
    x2, y2 = vec2  # normalize(vec2)
    phi1 = np.arctan2(y1, x1)
    vec2 = rotate([x2, y2], -phi1+jump)
    phi2 = np.degrees(np.arctan2(vec2[1], vec2[0]) - jump)
    alpha = -phi2
    return alpha


class Graph(object):

    def __init__(self, graph_dict=None):
        """ initializes a graph object
            If no dictionary or None is given, an empty dictionary will be used
        """
        if graph_dict is None:
            graph_dict = {}
        self.__graph_dict = graph_dict

    def vertices(self):
        """ returns the vertices of a graph """
        return list(self.__graph_dict.keys())

    def edges(self):
        """ returns the edges of a graph """
        return self.__generate_edges()

    def __generate_edges(self):
        """ A static method generating the edges of the
            graph "graph". Edges are represented as sets
            with one (a loop back to the vertex) or two
            vertices
        """
        edges = []
        for vertex in self.__graph_dict:
            for neighbour, cost in self.__graph_dict[vertex]:
                if (vertex, neighbour, cost) not in edges:
                    edges.append((vertex, neighbour, cost))
        return edges

    def __str__(self):
        res = "vertices: "
        for k in self.__graph_dict:
            res += str(k) + " "
        res += "\nedges: "
        for edge in self.__generate_edges():
            res += str(edge) + " "
        return res

    def find_isolated_vertices(self):
        """ returns a list of isolated vertices. """
        graph = self.__graph_dict
        isolated = []
        for vertex in graph:
            print(isolated, vertex)
            if not graph[vertex]:
                isolated += [vertex]
        return isolated

    def find_path(self, start_vertex, end_vertex, path=[]):
        """ find a path from start_vertex to end_vertex
            in graph """
        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return path
        if start_vertex not in graph:
            return None
        for vertex, _ in graph[start_vertex]:
            if vertex not in path:
                extended_path = self.find_path(vertex, end_vertex, path)
                if extended_path:
                    return extended_path
        return None

    def find_all_paths(self, start_vertex, end_vertex, path=[]):
        """ find all paths from start_vertex to
            end_vertex in graph """
        graph = self.__graph_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return [path]
        if start_vertex not in graph:
            return []
        paths = []
        for vertex, _ in graph[start_vertex]:
            if vertex not in path:
                extended_paths = self.find_all_paths(vertex, end_vertex,
                                                     path)
                for p in extended_paths:
                    paths.append(p)
        return paths

    def get_children(self, vertex):
        return self.__graph_dict[vertex]


if __name__ == '__main__':
    try:
        from graphviz import Digraph

        def render_graph(graph):
            """ requirements:
            pip install graphviz
            apt-get install graphviz
            """
            dot = Digraph()
            for v in graph.vertices():
                dot.node(v, v)
            for e in graph.edges():
                v = e[0]
                w = e[1]
                c = e[2]
                dot.edge(v, w, label=str(c) if c else None)
            dot.render('tree', view=True)

        graph = Graph(g)
        render_graph(graph)
    except ImportError:
        print('Missing package gaphiviz')
        print('run: "pip install graphviz" and "apt-get install graphviz" ')
