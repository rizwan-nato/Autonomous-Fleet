import networkx as nx
import matplotlib.pyplot as plt

class Graph:
    def __init__(self):
        # CONSTANTES
        # number of line cross on a side of the square
        SIZE = 5
        # weights
        WEIGHT_FINAL = 10
        WEIGHT_STRAIGHT = 1
        WEIGHT_ANGLE = 4

        self.G = nx.DiGraph()
        self.removed_edges = {} # key: central node, value: OutEdgeDataView of edges
        self.path_dict = {}

        # list of end point nodes
        self.end_points = []
        for x in range(SIZE):
            for y in range(SIZE):
                self.end_points.append((x,y))

        # list of nodes representing roads
        roads = []
        for node in self.end_points:
            x = node[0]
            y = node[1]
            if y+1<SIZE:
                roads.append(((x,y),(x,y+1)))
            if x+1<SIZE:
                roads.append(((x,y),(x+1,y)))

        # edge from roads to end points
        final_edges = []
        starting_edges = []
        for node in roads:
            # road to end point
            final_edges.append((node, node[0], WEIGHT_FINAL))
            final_edges.append((node, node[1], WEIGHT_FINAL))
            # starting point to road
            starting_edges.append((node[0], node, WEIGHT_STRAIGHT))
            starting_edges.append((node[1], node, WEIGHT_STRAIGHT))

        # edge between straight roads
        straight_edges = []
        for node in self.end_points:
            x = node[0]
            y = node[1]
            if x-1>= 0 and x+1<SIZE:
                straight_edges.append((((x-1,y),(x,y)),((x,y),(x+1,y)), WEIGHT_STRAIGHT))
                straight_edges.append((((x,y),(x+1,y)),((x-1,y),(x,y)), WEIGHT_STRAIGHT))
            elif y-1 >= 0 and y+1<SIZE:
                straight_edges.append((((x,y-1),(x,y)),((x,y),(x,y+1)), WEIGHT_STRAIGHT))
                straight_edges.append((((x,y),(x,y+1)),((x,y-1),(x,y)), WEIGHT_STRAIGHT))

        # edge between angled roads
        right_edges = []
        left_edges = []
        for node in roads:
            point_a = node[0]
            point_b = node[1]

            if point_a[0] < point_b[0]: # xa<xb, horizontal line
                up_left = (point_a, (point_a[0],point_a[1]+1))
                up_right = (point_b, (point_b[0],point_b[1]+1))
                down_left = ((point_a[0],point_a[1]-1), point_a)
                down_right = ((point_b[0],point_b[1]-1), point_b)

                if up_left in roads:
                    pen_weight = self.penalize_weight(node, up_left, WEIGHT_ANGLE, SIZE)
                    right_edges.append((node,up_left, pen_weight))
                    left_edges.append((up_left,node, pen_weight))
                if up_right in roads:
                    pen_weight = self.penalize_weight(node, up_right, WEIGHT_ANGLE, SIZE)
                    left_edges.append((node,up_right, pen_weight))
                    right_edges.append((up_right,node,pen_weight))
                if down_left in roads:
                    pen_weight = self.penalize_weight(node, down_left, WEIGHT_ANGLE, SIZE)
                    left_edges.append((node,down_left, pen_weight))
                    right_edges.append((down_left,node, pen_weight))
                if down_right in roads:
                    pen_weight = self.penalize_weight(node, down_right, WEIGHT_ANGLE, SIZE)
                    right_edges.append((node,down_right, pen_weight))
                    left_edges.append((down_right, node, pen_weight))

        # add edge to graph (adding missing node is automatic)
        self.G.add_weighted_edges_from(starting_edges, cmd="start")
        self.G.add_weighted_edges_from(final_edges, cmd="stop")
        self.G.add_weighted_edges_from(straight_edges, cmd="straight")
        self.G.add_weighted_edges_from(left_edges, cmd="left")
        self.G.add_weighted_edges_from(right_edges, cmd="right")

        # launching ramp
        """
        # vi007
        self.G.add_edge("stock", "ramp", weight=WEIGHT_ANGLE, cmd="left")
        self.G.add_edge("ramp", "stock", weight=WEIGHT_ANGLE, cmd="right")

        self.G.add_edge("ramp", (0,0), weight=WEIGHT_STRAIGHT/2+WEIGHT_FINAL, cmd="straight")
        self.G.add_edge((0,0), "ramp", weight=WEIGHT_STRAIGHT/2+WEIGHT_FINAL, cmd="straight")

        self.G.add_edge("ramp", ((0,0),(1,0)), weight=WEIGHT_STRAIGHT, cmd="straight")
        self.G.add_edge(((0,0),(1,0)), "ramp", weight=WEIGHT_STRAIGHT, cmd="straight")

        self.G.add_edge("ramp", ((0,0),(0,1)), weight=WEIGHT_ANGLE, cmd="left")
        self.G.add_edge(((0,0),(0,1)), "ramp", weight=WEIGHT_ANGLE, cmd="right")
        """
        # vi003
        self.G.add_edge("ramp", (0, 0), weight=WEIGHT_STRAIGHT / 2 + WEIGHT_FINAL, cmd="straight")
        self.G.add_edge((0, 0), "ramp", weight=WEIGHT_STRAIGHT / 2 + WEIGHT_FINAL, cmd="straight")

        self.G.add_edge("ramp", ((0, 0), (1, 0)), weight=WEIGHT_ANGLE, cmd="right")
        self.G.add_edge(((0, 0), (1, 0)), "ramp", weight=WEIGHT_ANGLE, cmd="left")

        self.G.add_edge("ramp", ((0, 0), (0, 1)), weight=WEIGHT_STRAIGHT, cmd="straight")
        self.G.add_edge(((0, 0), (0, 1)), "ramp", weight=WEIGHT_STRAIGHT, cmd="straight")



    def dijkstra(self, start, end):
        return nx.dijkstra_path(self.G, start, end)

    def show_graph(self):
        edges = self.G.edges()
        weights = [self.G[u][v]['weight'] for u,v in edges]
        nx.draw_networkx(self.G, width=weights)
        plt.show()

    def cross_planning(self,start,end, bot):
        cmd_dict = nx.get_edge_attributes(self.G, 'cmd')
        used_nodes = self.dijkstra(start,end)
        used_edges = [(used_nodes[k],used_nodes[k+1]) for k in range(len(used_nodes)-1)]
        self.path_dict[bot] = used_edges
        #return [cmd_dict[edge] for edge in used_edges]
        plan = [cmd_dict[edge] for edge in used_edges]
        self.skip_start(plan)
        return plan

    def penalize_weight(self, node1,node2, base_weight, size):
        # overly complex stuff to penalize corner by rising their weight
        # exclude (0,0) as it is a true intersection with the ramp
        maxi = size-1
        if ((node1[0] in [(maxi,maxi), (maxi, 0), (0, maxi)] or
             node1[1] in [(maxi,maxi), (maxi, 0), (0, maxi)]) and
            (node2[0] in [(maxi,maxi), (maxi, 0), (0, maxi)] or
             node2[1] in [(maxi,maxi), (maxi, 0), (0, maxi)])):
            return base_weight*3
        return base_weight

    def where_am_i(self, bot, counter):
        print("\nPOS :\nCounter {}".format(counter))
        used_edges = self.path_dict[bot]
        if counter>= len(used_edges):
            print(used_edges[-1][1])
            return used_edges[-1][1]
        print(used_edges[counter][0])
        return used_edges[counter][0]


    def skip_start(self, plan):
        if 'start' in plan:
            plan.remove('start')
    """
    def add_obstacle(self, obstacle_node, exclude_edge=None):
        print("[GRAPH] obstacle {}".format(obstacle_node))
        edges_to_obstacle = list(self.G.in_edges(obstacle_node, data=True))
        edges_to_obstacle += list(self.G.out_edges(obstacle_node, data=True))

        # exclude incoming edge to not isolate robot
        if exclude_edge:
            for k in range(len(edges_to_obstacle)-1,-1,-1):
                if exclude_edge[0] in edges_to_obstacle[k] and exclude_edge[1] in edges_to_obstacle[k] :
                    edges_to_obstacle.pop(k)

        self.G.remove_edges_from(edges_to_obstacle)
        self.removed_edges[obstacle_node] = edges_to_obstacle"""

    def add_obstacle(self, obstacle_node, last_node):
        print("[GRAPH] obstacle {}".format(obstacle_node))
        edges_to_obstacle = list(self.G.in_edges(obstacle_node, data=True))
        edges_to_obstacle += list(self.G.out_edges(obstacle_node, data=True))

        # exclude incoming edge to not isolate robot
        last_neigh = list(self.G.neighbors(last_node))
        last_neigh.append(last_node)
        curr_neigh = list(self.G.neighbors(obstacle_node))
        common = [node for node in curr_neigh if node in last_neigh and node not in self.end_points]
        back_edge = [(obstacle_node,node) for node in common]
        for edge in back_edge:
            for k in range(len(edges_to_obstacle)-1,-1,-1):
                if edge[0] in edges_to_obstacle[k] and edge[1] in edges_to_obstacle[k] :
                    edges_to_obstacle.pop(k)

        self.G.remove_edges_from(edges_to_obstacle)
        self.removed_edges[obstacle_node] = edges_to_obstacle

    def cancel_obstacle(self, obstacle_node):
        #self.G.add_weighted_edges_from(self.removed_edges[obstacle_node])
        for edge in self.removed_edges[obstacle_node]:
            self.G.add_edge(edge[0], edge[1], weight=edge[2]["weight"], cmd=edge[2]["cmd"])
        del self.removed_edges[obstacle_node]

def test():
    waze = Graph()
    waze.cross_planning("ramp", (2,2), '1')
    instructions_done = 2
    pos = waze.where_am_i('1', instructions_done)
    last_pos = waze.where_am_i('1',instructions_done-1)
    waze.add_obstacle(pos, last_pos)
    L = waze.cross_planning(pos, (2,2),'1')
    print(L)