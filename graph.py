class Vertex(object):
    def __init__(self, name):
        self.name = name
        self.in_degree = []
        self.out_degree = []

    def add_in(self, edge):
        self.in_degree.append(edge)

    def add_out(self, edge):
        self.out_degree.append(edge)

    def in_count(self):
        return len(self.in_degree)

    def out_count(self):
        return len(self.out_degree)


class Edge(object):
    def __init__(self, out_of, into, value):
        self.out_of = out_of
        self.into = into
        self.element = value
        self.connect()

    def connect(self):
        self.out_of.add_out(self)
        self.into.add_in(self)


class Graph(object):
    def __init__(self, directed):
        self.directed = directed
        self._vertices = {}
        self._edges = []

    def insert_vertex(self, name):
        vertex = Vertex(name)
        self._vertices[name] = vertex
        return vertex

    def insert_edge(self, src, dest, element):
        edge = Edge(src, dest, element)
        self._edges.append(edge)
        return edge

    def vertex_count(self):
        return len(self._vertices)

    def vertices(self):
        for_ret = []
        for vertex in self._vertices.values():
            for_ret.append(vertex)
        return for_ret

    def edge_count(self):
        return len(self._edges)

    def edges(self):
        return self._edges

    def get_edge(self, u, v):
        for edge in self._edges:
            if edge.out_of == u and edge.into == v:
                return edge
        return None

    def degree(self, v, out=True):
        if out:
            return v.out_count()
        else:
            return v.in_count()

    def incident_edges(self, v, out=True):
        if out:
            return v.out_degree
        else:
            return  v.in_degree

