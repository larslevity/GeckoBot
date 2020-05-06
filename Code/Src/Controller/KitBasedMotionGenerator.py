# -*- coding: utf-8 -*-
"""
Created on Wed May  6 10:28:26 2020

@author: ls
"""

import numpy as np

from Src.Controller import rotate_on_spot as ros


g = {  # manually tuned
     'rest': [('R', ((.0, .0), -1)), ('L', ((0, 0), 1)),
              ('rest', ((0, 0), 0))],
     # CRAWL
     'C1_0': [('C1_2:dfx', None)],
     'C1_2:dfx': [('L', ((0, 1), 1)), ('R', ((0, 1), -1)),
                  ('C1_0', ((0, .1), 130)), ('C1_0', ((0, .1), -130))],

     # RIGHT
     'R': [  # ('rest', ((0, 0), 0)),
             ('R:fix', ((0, .71), 1)), ('R:fix', ((.1, .2), -80)),
             ('R:fix', ((.1, .5), -10)), ('R2_0', ((.1, .4), -20)),
             ('C1_0', ((0, 0), 120)), ('C1_0', ((0, 0), -120))],
     'R:fix': [('R:dfx', None)],
     'R:dfx': [('L', ((0, .71), 1)),
               ('R1_0', ((.1, .4), -10)),
#               ('R3_0', ((.1, .2), -80))
               ],

     'R3_0': [('R3_0:fix', None)],
     'R3_0:fix': [('R3_0:dfx', None)],
     'R3_0:dfx': [('R3_1', None)],
     'R3_1': [('R3_1:fix', None)],
     'R3_1:fix': [('R3_1:dfx', None)],
     'R3_1:dfx': [('R3_2', ((0, .2), -130)), ('R3_3', ((.1, .4), -70))],
     'R3_2': [('R3_2:fix', None)],
     'R3_2:fix': [('R3_2:dfx', None)],
     'R3_2:dfx': [('R3_1', None)],
     'R3_3': [('R3_3:fix', None)],
     'R3_3:fix': [('R3_3:dfx', None)],
     'R3_3:dfx': [('R', None)],

     'R1_0': [('R1_0:fix', None)],
     'R1_0:fix': [('R1_0:dfx', None)],
     'R1_0:dfx': [('R', None)],

     'R2_0': [('R2_0:fix', None)],
     'R2_0:fix': [('R2_0:dfx', None)],
     'R2_0:dfx': [('R2_1', None)],
     'R2_1': [('R2_1:fix', None)],
     'R2_1:fix': [('R2_1:dfx', None)],
     'R2_1:dfx': [('R2_0', ((0, .4), -30)), ('R', ((0, .6), -15))],

     # LEFT
     'L': [  # ('rest', ((0, 0), 0)),
             ('L:fix', ((0, .71), -1)), ('L:fix', ((-.1, .2), 80)),
             ('L:fix', ((-.1, .5), 10)), ('L2_0', ((-.1, .4), 20)),
             ('C1_0', ((0, 0), 120)), ('C1_0', ((0, 0), -120))],
     'L:fix': [('L:dfx', None)],
     'L:dfx': [('R', ((0, .71), -1)),
               ('L1_0', ((-.1, .4), 10)),
#               ('L3_0', ((-.1, .2), 80))
               ],

     'L3_0': [('L3_0:fix', None)],
     'L3_0:fix': [('L3_0:dfx', None)],
     'L3_0:dfx': [('L3_1', None)],
     'L3_1': [('L3_1:fix', None)],
     'L3_1:fix': [('L3_1:dfx', None)],
     'L3_1:dfx': [('L3_2', ((0, .2), 130)), ('L3_3', ((0, .4), 70))],
     'L3_2': [('L3_2:fix', None)],
     'L3_2:fix': [('L3_2:dfx', None)],
     'L3_2:dfx': [('L3_1', None)],
     'L3_3': [('L3_3:fix', None)],
     'L3_3:fix': [('L3_3:dfx', None)],
     'L3_3:dfx': [('L', None)],

     'L1_0': [('L1_0:fix', None)],
     'L1_0:fix': [('L1_0:dfx', None)],
     'L1_0:dfx': [('L', None)],

     'L2_0': [('L2_0:fix', None)],
     'L2_0:fix': [('L2_0:dfx', None)],
     'L2_0:dfx': [('L2_1', None)],
     'L2_1': [('L2_1:fix', None)],
     'L2_1:fix': [('L2_1:dfx', None)],
     'L2_1:dfx': [('L2_0', ((0, .4), 30)), ('L', ((0, 0.6), 15))]
    }

t_move = 1.2
t_fix = .2
t_dfx = .2


ref = {
     'rest': [[0, 0, 0, 0, 0], [1, 0, 0, 0], .1],

     # CRAWL
     'C1_0': [[45, 45, 0, 45, 45], [1, 0, 0, 1], t_move],
     'C1_2:dfx': [[45, 45, 10, 45, 45], [0, 1, 1, 0], t_dfx],

     # RIGHT
     'R': [[0, 90, 90, 0, 90], [0, 1, 1, 0], t_move],
     'R:fix': [[0, 90, 90, 0, 90], [1, 1, 1, 1], t_fix],
     'R:dfx': [[0, 90, 90, 0, 90], [1, 0, 0, 1], t_dfx],

     'R3_0': [[50, 30, 90, 30, 150], [1, 0, 0, 1], t_move],
     'R3_0:fix': [[50, 30, 90, 30, 150], [1, 1, 1, 1], t_fix],
     'R3_0:dfx': [[50, 30, 90, 30, 150], [0, 1, 1, 0], t_dfx],

     'R3_1': [[124, 164, 152, 62, 221], [0, 1, 1, 0], t_move],
     'R3_1:fix': [[124, 164, 152, 62, 221], [1, 1, 1, 1], t_fix],
     'R3_1:dfx': [[124, 164, 152, 62, 221], [1, 0, 0, 1], t_dfx],

     'R3_2': [[0, 0, 24, 0, 0], [1, 0, 0, 1], t_move],
     'R3_2:fix': [[0, 0, 24, 0, 0], [1, 1, 1, 1], t_fix],
     'R3_2:dfx': [[0, 0, 24, 0, 0], [0, 1, 1, 0], t_dfx],

     'R3_3': [[30, 90, 80, 10, 10], [1, 0, 0, 1], t_move],
     'R3_3:fix': [[30, 90, 80, 10, 10], [1, 1, 1, 1], t_fix],
     'R3_3:dfx': [[30, 90, 80, 10, 10], [0, 1, 1, 0], t_dfx],

     'R1_0': [[40, 1, -10, 60, 10], [1, 0, 0, 1], t_move],
     'R1_0:fix': [[40, 1, -10, 60, 10], [1, 1, 1, 1], t_fix],
     'R1_0:dfx': [[40, 1, -10, 60, 10], [0, 1, 1, 0], t_dfx],

     'R2_0': [[48, 104, 114, 27, 124], [0, 1, 1, 0], t_move],
     'R2_0:fix': [[48, 104, 114, 27, 124], [1, 1, 1, 1], t_fix],
     'R2_0:dfx': [[48, 104, 114, 27, 124], [1, 0, 0, 1], t_dfx],

     'R2_1': [[1, 72, -10, 1, 55], [1, 0, 0, 1], t_move],
     'R2_1:fix': [[1, 72, -10, 1, 55], [1, 1, 1, 1], t_fix],
     'R2_1:dfx': [[1, 72, -10, 1, 55], [0, 1, 1, 0], t_dfx],

     #   LEFT
     'L': [[90, 0, -90, 90, 0], [1, 0, 0, 1], t_move],
     'L:fix': [[90, 0, -90, 90, 0], [1, 1, 1, 1], t_fix],
     'L:dfx': [[90, 0, -90, 90, 0], [0, 1, 1, 0], t_dfx],

     'L3_0': [[30, 50, -90, 150, 30], [0, 1, 1, 0], t_move],
     'L3_0:fix': [[30, 50, -90, 150, 30], [1, 1, 1, 1], t_fix],
     'L3_0:dfx': [[30, 50, -90, 150, 30], [1, 0, 0, 1], t_dfx],

     'L3_1': [[164, 124, -152, 221, 62], [1, 0, 0, 1], t_move],
     'L3_1:fix': [[164, 124, -152, 221, 62], [1, 1, 1, 1], t_fix],
     'L3_1:dfx': [[164, 124, -152, 221, 62], [0, 1, 1, 0], t_dfx],

     'L3_2': [[0, 0, -24, 0, 0], [0, 1, 1, 0], t_move],
     'L3_2:fix': [[0, 0, -24, 0, 0], [1, 1, 1, 1], t_fix],
     'L3_2:dfx': [[0, 0, -24, 0, 0], [1, 0, 0, 1], t_dfx],

     'L3_3': [[90, 30, -80, 10, 10], [0, 1, 1, 0], t_move],
     'L3_3:fix': [[90, 30, -80, 10, 10], [1, 1, 1, 1], t_fix],
     'L3_3:dfx': [[90, 30, -80, 10, 10], [1, 0, 0, 1], t_dfx],

     'L1_0': [[1, 40, 10, 10, 60], [0, 1, 1, 0], t_move],
     'L1_0:fix': [[1, 40, 10, 10, 60], [1, 1, 1, 1], t_fix],
     'L1_0:dfx': [[1, 40, 10, 10, 60], [1, 0, 0, 1], t_dfx],

     'L2_0': [[104, 48, -114, 124, 27], [1, 0, 0, 1], t_move],
     'L2_0:fix': [[104, 48, -114, 124, 27], [1, 1, 1, 1], t_fix],
     'L2_0:dfx': [[104, 48, -114, 124, 27], [0, 1, 1, 0], t_dfx],

     'L2_1': [[72, 1, -70, 55, 1], [0, 1, 1, 0], t_move],
     'L2_1:fix': [[72, 1, -70, 55, 1], [1, 1, 1, 1], t_fix],
     'L2_1:dfx': [[72, 1, -70, 55, 1], [1, 0, 0, 1], t_dfx]
      }


class CandidateHandler(dict):
    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(CandidateHandler, self).__setitem__(key, [])
        self[key].append(value)

    def minimum(self):
        min_d = {}
        for key in self:
            min_d[key] = min([abs(c) for c in self[key]])
        min_ = min([abs(min_d[key]) for key in min_d])
        min_key = min(min_d, key=min_d.get)
        return min_, min_key

    def maximum(self):
        max_d = {}
        for key in self:
            max_d[key] = max([abs(c) for c in self[key]])
        max_ = min([abs(max_d[key]) for key in max_d])
        max_key = min(max_d, key=max_d.get)
        return max_, max_key


class ReferenceGenerator(object):
    def __init__(self, pose='rest', graph=g, ref=ref):
        self.graph = Graph(graph)
        self.pose = pose
        self.ref = ref
        self.idx = 0
        self.last_deps = None
        self.check_consistency()
        self.crawl = False
        self.crawl_ptrn = None
        self.crawl_idx = None

    def check_consistency(self):
        for key in self.graph.vertices():
            try:
                self.ref[key]
            except KeyError as err:
                print(err, 'there is no ref')
        for key in self.ref:
            if key[-3:] == 'fix':
                assert sum(self.ref[key][1]) == 4  # all feet must be fix
            if key[-3:] == 'dfx':
                assert sum(self.ref[key][1]) == 2  # 2 feet must be fix
            if key[-1] != 'x':
                try:
                    assert sum(self.ref[key][1]) == 2  # 2 feet must be fix
                except AssertionError:
                    print(key, 'sum is not equal 2')

    def get_next_reference(self, act_position, act_eps, xref):
        xref = np.r_[xref]
        act_pos = np.r_[act_position]
        dpos = xref - act_pos
        act_dir = np.r_[np.cos(np.radians(act_eps)),
                        np.sin(np.radians(act_eps))]
        act_deps = calc_angle(dpos, act_dir)
        act_dist = np.linalg.norm(dpos)

        if act_dist < .5:
            pose_id = 'rest'
        elif not self.crawl:
            if len(self.graph.get_children(self.pose)) > 1:
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

                deps = CandidateHandler()
                ddist = CandidateHandler()
                for child in self.graph.get_children(self.pose):
                    v, (translation, rotation) = child
                    dist_, deps_ = suitability(translation, rotation, v)
                    deps[v] = round(deps_, 2)
                    ddist[v] = round(dist_, 2)

                if abs(act_deps) > 70:  # neglect transition
                    _, pose_id = deps.minimum()
                else:
                    max_deps, _ = deps.maximum()
                    max_ddist, _ = ddist.maximum()

                    w = .5
                    dec = CandidateHandler()
                    for key in deps:
                        for dist, eps in zip(ddist[key], deps[key]):
                            dec[key] = (
                                w*dist/max_ddist + (1-w)*abs(eps)/max_deps)
                    min_dec, pose_id = dec.minimum()

            else:  # only 1 child
                pose_id, _ = self.graph.get_children(self.pose)[0]

            if pose_id == 'C1_0':
                self.crawl = True
                alpha, feet, process_time = self.__get_ref(self.pose)
                self.crawl_ptrn = ros.rotate_on_spot(
                        act_deps, alpha, feet, t_fix, t_dfx, t_move)
                self.crawl_idx = 0

        if self.crawl:
            ref = self.crawl_ptrn[self.crawl_idx]
            alpha, feet, process_time = ref
            self.crawl_idx += 1
            pose_id = 'crawling'

            if self.crawl_idx+1 > len(self.crawl_ptrn):
                self.crawl = False
                self.crawl_idx = None
                pose_id = 'C1_2:dfx'
                self.ref[pose_id] = self.crawl_ptrn[-1]
                self.crawl_ptrn = None

        else:
            alpha, feet, process_time = self.__get_ref(pose_id)

        self.pose = pose_id
        self.idx += 1

        return alpha, feet, process_time, pose_id

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
        print('run: "pip install graphviz" or "apt-get install graphviz" ')
