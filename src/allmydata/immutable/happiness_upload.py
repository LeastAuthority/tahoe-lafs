
from Queue import PriorityQueue
#from allmydata.util.happinessutil import augmenting_path_for, residual_network


def augmenting_path_for(graph):
    """
    I return an augmenting path, if there is one, from the source node
    to the sink node in the flow network represented by my graph argument.
    If there is no augmenting path, I return False. I assume that the
    source node is at index 0 of graph, and the sink node is at the last
    index. I also assume that graph is a flow network in adjacency list
    form.
    """
    bfs_tree = bfs(graph, 0)
    if bfs_tree[len(graph) - 1]:
        n = len(graph) - 1
        path = [] # [(u, v)], where u and v are vertices in the graph
        while n != 0:
            path.insert(0, (bfs_tree[n], n))
            n = bfs_tree[n]
        return path
    return False

def bfs(graph, s):
    """
    Perform a BFS on graph starting at s, where graph is a graph in
    adjacency list form, and s is a node in graph. I return the
    predecessor table that the BFS generates.
    """
    # This is an adaptation of the BFS described in "Introduction to
    # Algorithms", Cormen et al, 2nd ed., p. 532.
    # WHITE vertices are those that we haven't seen or explored yet.
    WHITE = 0
    # GRAY vertices are those we have seen, but haven't explored yet
    GRAY  = 1
    # BLACK vertices are those we have seen and explored
    BLACK = 2
    color        = [WHITE for i in xrange(len(graph))]
    predecessor  = [None for i in xrange(len(graph))]
    distance     = [-1 for i in xrange(len(graph))]
    queue = [s] # vertices that we haven't explored yet.
    color[s] = GRAY
    distance[s] = 0
    while queue:
        n = queue.pop(0)
        for v in graph[n]:
            if color[v] == WHITE:
                color[v] = GRAY
                distance[v] = distance[n] + 1
                predecessor[v] = n
                queue.append(v)
        color[n] = BLACK
    return predecessor

def residual_network(graph, f):
    """
    I return the residual network and residual capacity function of the
    flow network represented by my graph and f arguments. graph is a
    flow network in adjacency-list form, and f is a flow in graph.
    """
    new_graph = [[] for i in xrange(len(graph))]
    cf = [[0 for s in xrange(len(graph))] for sh in xrange(len(graph))]
    for i in xrange(len(graph)):
        for v in graph[i]:
            if f[i][v] == 1:
                # We add an edge (v, i) with cf[v,i] = 1. This means
                # that we can remove 1 unit of flow from the edge (i, v)
                new_graph[v].append(i)
                cf[v][i] = 1
                cf[i][v] = -1
            else:
                # We add the edge (i, v), since we're not using it right
                # now.
                new_graph[i].append(v)
                cf[i][v] = 1
                cf[v][i] = -1
    return (new_graph, cf)

def _convert_mappings(index_to_peer, index_to_share, maximum_graph):
    """
    Now that a maximum spanning graph has been found, convert the indexes
    back to their original ids so that the client can pass them to the
    uploader.
    """

    converted_mappings = {}
    for share in maximum_graph:
        peer = maximum_graph[share]
        if peer == None:
            converted_mappings.setdefault(index_to_share[share], None)
        else:
            converted_mappings.setdefault(index_to_share[share], set([index_to_peer[peer]]))
    return converted_mappings

def _compute_maximum_graph(graph, shareIndices):
    """
    This is an implementation of the Ford-Fulkerson method for finding
    a maximum flow in a flow network applied to a bipartite graph.
    Specifically, it is the Edmonds-Karp algorithm, since it uses a
    breadth-first search to find the shortest augmenting path at each
    iteration, if one exists.

    The implementation here is an adapation of an algorithm described in
    "Introduction to Algorithms", Cormen et al, 2nd ed., pp 658-662.
    """

    if graph == []:
        return {}

    dim = len(graph)
    flow_function = [[0 for sh in xrange(dim)] for s in xrange(dim)]
    residual_graph, residual_function = residual_network(graph, flow_function)

    path = augmenting_path_for(residual_graph)
    while path:
        # Delta is the largest amount that we can increase flow across
        # all of the edges in path. Because of the way that the residual
        # function is constructed, f[u][v] for a particular edge (u, v)
        # is the amount of unused capacity on that edge. Taking the
        # minimum of a list of those values for each edge in the
        # augmenting path gives us our delta.
        delta = min(map(lambda (u, v), rf=residual_function: rf[u][v],
                        path))
        for (u, v) in path:
            flow_function[u][v] += delta
            flow_function[v][u] -= delta
        residual_graph, residual_function = residual_network(graph,flow_function)
        path = augmenting_path_for(residual_graph)
        #print('loop', len(residual_graph))

    new_mappings = {}
    for shareIndex in shareIndices:
        peer = residual_graph[shareIndex]
        if peer == [dim - 1]:
            new_mappings.setdefault(shareIndex, None)
        else:
            new_mappings.setdefault(shareIndex, peer[0])

    return new_mappings

def _flow_network(peerIndices, shareIndices):
    """
    Given set of peerIndices and a set of shareIndices, I create a flow network
    to be used by _compute_maximum_graph. The return value is a two
    dimensional list in the form of a flow network, where each index represents
    a node, and the corresponding list represents all of the nodes it is connected
    to.

    This function is similar to allmydata.util.happinessutil.flow_network_for, but
    we connect every peer with all shares instead of reflecting a supplied servermap.
    """
    graph = []
    # The first entry in our flow network is the source.
    # Connect the source to every server.
    graph.append(peerIndices)
    sink_num = len(peerIndices + shareIndices) + 1
    # Connect every server with every share it can possibly store.
    for peerIndex in peerIndices:
        graph.insert(peerIndex, shareIndices)
    # Connect every share with the sink.
    for shareIndex in shareIndices:
        graph.insert(shareIndex, [sink_num])
    # Add an empty entry for the sink.
    graph.append([])
    return graph

def _servermap_flow_graph(peers, shares, servermap):
    """
    Generates a flow network of peerIndices to shareIndices from a server map
    of 'peer' -> ['shares']. According to Wikipedia, "a flow network is a
    directed graph where each edge has a capacity and each edge receives a flow.
    The amount of flow on an edge cannot exceed the capacity of the edge." This
    is necessary because in order to find the maximum spanning, the Edmonds-Karp algorithm
    converts the problem into a maximum flow problem.
    """
    if servermap == {}:
        return []

    peer_to_index, index_to_peer = _reindex(peers, 1)
    share_to_index, index_to_share = _reindex(shares, len(peers) + 1)
    graph = []
    sink_num = len(peers) + len(shares) + 1
    graph.append([peer_to_index[peer] for peer in peers])
    for peer in peers:
        indexedShares = [share_to_index[s] for s in servermap[peer]]
        graph.insert(peer_to_index[peer], indexedShares)
    for share in shares:
        graph.insert(share_to_index[share], [sink_num])
    graph.append([])
    return graph

def _reindex(items, base):
    """
    I take an iteratble of items and give each item an index to be used in
    the construction of a flow network. Indices for these items start at base
    and continue to base + len(items) - 1.

    I return two dictionaries: ({item: index}, {index: item})
    """
    item_to_index = {}
    index_to_item = {}
    for item in items:
        item_to_index.setdefault(item, base)
        index_to_item.setdefault(base, item)
        base += 1
    return (item_to_index, index_to_item)

def _maximum_matching_graph(graph, servermap):
    """
    :param graph: an iterable of (server, share) 2-tuples

    Calculate the maximum matching of the bipartite graph (U, V, E)
    such that:

        U = peers
        V = shares
        E = peers x shares

    Returns a dictionary {share -> set(peer)}, indicating that the share
    should be placed on each peer in the set. If a share's corresponding
    value is None, the share can be placed on any server. Note that the set
    of peers should only be one peer when returned.
    """
    peers = [x[0] for x in graph]
    shares = [x[1] for x in graph]
    peer_to_index, index_to_peer = _reindex(peers, 1)
    share_to_index, index_to_share = _reindex(shares, len(peers) + 1)
    shareIndices = [share_to_index[s] for s in shares]
    if servermap:
        graph = _servermap_flow_graph(peers, shares, servermap)
    else:
        peerIndices = [peer_to_index[peer] for peer in peers]
        graph = _flow_network(peerIndices, shareIndices)
    max_graph = _compute_maximum_graph(graph, shareIndices)
    return _convert_mappings(index_to_peer, index_to_share, max_graph)


def _filter_g3(g3, m1, m2):
    """
    This implements the last part of 'step 6' in the spec, "Then
    remove (from G3) any servers and shares used in M1 or M2 (note
    that we retain servers/shares that were in G1/G2 but *not* in the
    M1/M2 subsets)"
    """
    sequence = m1.values() + m2.values()
    sequence = filter(lambda x: x is not None, sequence)
    if len(sequence) == 0:
        return g3
    m12_servers = reduce(lambda a, b: a.union(b), sequence)
    # m1 and m2 may contain edges like "peer -> None" but those
    # shouldn't be considered "actual mappings" by this removal
    # algorithm (i.e. an edge "peer0 -> None" means there's nothing
    # placed on peer0)
    m12_shares = set(
        [k for k, v in m1.items() if v] +
        [k for k, v in m2.items() if v]
    )
    new_g3 = set()
    for edge in g3:
        if edge[0] not in m12_servers and edge[1] not in m12_shares:
            new_g3.add(edge)
    return new_g3


def _merge_dicts(result, inc):
    """
    given two dicts mapping key -> set(), merge the *values* of the
    'inc' dict into the value of the 'result' dict if the value is not
    None.

    Note that this *mutates* 'result'
    """
    for k, v in inc.items():
        existing = result.get(k, None)
        if existing is None:
            result[k] = v
        elif v is not None:
            result[k] = existing.union(v)

def _index_peers(ids, base):
    """
    I create a bidirectional dictionary of indexes to ids with
    indexes from base to base + |ids| - 1 inclusively. I am used
    in order to create a flow network with vertices 0 through n.
    """
    reindex_to_name = {}
    for item in ids:
        reindex_to_name.setdefault(item, base)
        reindex_to_name.setdefault(base, item)
        base += 1
    return reindex_to_name

def _reindex_shares(shares, base):
    """
    I create a dictionary of sharenum -> index (where 'index' is as defined
    in _index_peers) and a dictionary of index -> sharenum. Since share
    numbers  use the same name space as the indexes, two dictionaries need
    to be created instead of one like in _reindex_peers.
    """
    share_to_index = {}
    index_to_share = {}
    for share in shares:
        share_to_index.setdefault(share, base)
        index_to_share.setdefault(base, share)
        base += 1
    return (share_to_index, index_to_share)

def _servermap_flow_graph(peers, shares, servermap):
    """
    Generates a flow network of peerids to shareids from a server map
    of 'peerids' -> ['shareids']. According to Wikipedia, "a flow network is a
    directed graph where each edge has a capacity and each edge receives a flow.
    The amount of flow on an edge cannot exceed the capacity of the edge." This
    is necessary because in order to find the maximum spanning, the Edmonds-Karp algorithm
    converts the problem into a maximum flow problem.
    """
    if servermap == {}:
        return []

    peerids = peers
    shareids = shares
    peer_to_index = _index_peers(peerids, 1)
    share_to_index, index_to_share = _reindex_shares(shareids, len(peerids) + 1)
    graph = []
    sink_num = len(peerids) + len(shareids) + 1
    graph.append([peer_to_index[peer] for peer in peerids])
    for peerid in peerids:
        shares = [share_to_index[s] for s in servermap[peerid]]
        graph.insert(peer_to_index[peerid], shares)
    for shareid in shareids:
        graph.insert(share_to_index[shareid], [sink_num])
    graph.append([])
    return graph

def _compute_maximum_graph(graph, shareids):
    """
    This is an implementation of the Ford-Fulkerson method for finding
    a maximum flow in a flow network applied to a bipartite graph.
    Specifically, it is the Edmonds-Karp algorithm, since it uses a
    BFS to find the shortest augmenting path at each iteration, if one
    exists.

    The implementation here is an adapation of an algorithm described in
    "Introduction to Algorithms", Cormen et al, 2nd ed., pp 658-662.
    """

    if graph == []:
        return {}

    dim = len(graph)
    flow_function = [[0 for sh in xrange(dim)] for s in xrange(dim)]
    residual_graph, residual_function = residual_network(graph, flow_function)

    while augmenting_path_for(residual_graph):
        path = augmenting_path_for(residual_graph)
        # Delta is the largest amount that we can increase flow across
        # all of the edges in path. Because of the way that the residual
        # function is constructed, f[u][v] for a particular edge (u, v)
        # is the amount of unused capacity on that edge. Taking the
        # minimum of a list of those values for each edge in the
        # augmenting path gives us our delta.
        delta = min(map(lambda (u, v), rf=residual_function: rf[u][v],
                        path))
        for (u, v) in path:
            flow_function[u][v] += delta
            flow_function[v][u] -= delta
        residual_graph, residual_function = residual_network(graph,flow_function)

    new_mappings = {}
    for share in shareids:
        peer = residual_graph[share]
        if peer == [dim - 1]:
            new_mappings.setdefault(share, None)
        else:
            new_mappings.setdefault(share, peer[0])

    return new_mappings

def _convert_mappings(peer_to_index, share_to_index, maximum_graph):
    """
    Now that a maximum spanning graph has been found, convert the indexes
    back to their original ids so that the client can pass them to the
    uploader.
    """

    converted_mappings = {}
    for share in maximum_graph:
        peer = maximum_graph[share]
        if peer == None:
            converted_mappings.setdefault(share_to_index[share], None)
        else:
            converted_mappings.setdefault(share_to_index[share],
                                          set([peer_to_index[peer]]))
    return converted_mappings

def _flow_network(peerids, shareids):
    """
    Given set of peerids and shareids, I create a flow network
    to be used by _compute_maximum_graph.
    """
    graph = []
    graph.append(peerids)
    sink_num = len(peerids + shareids) + 1
    for peerid in peerids:
        graph.insert(peerid, shareids)
    for shareid in shareids:
        graph.insert(shareid, [sink_num])
    graph.append([])
    return graph

def _extract_ids(mappings):
    shares = set()
    peers = set()
    for share in mappings:
        if mappings[share] == None:
            pass
        else:
            shares.add(share)
            for item in mappings[share]:
                peers.add(item)
    return (peers, shares)

def calculate_happiness(mappings):
    """
    I return the happiness of the mappings
    """
    happy = 0
    for share in mappings:
        if mappings[share] is not None:
            happy += 1
    return happy

def _distribute_homeless_shares(mappings, homeless_shares, peers_to_shares):
    """
    Shares which are not mapped to a peer in the maximum spanning graph
    still need to be placed on a server. This function attempts to
    distribute those homeless shares as evenly as possible over the
    available peers. If possible a share will be placed on the server it was
    originally on, signifying the lease should be renewed instead.
    """
    servermap_peerids = set([key for key in peers_to_shares])
    servermap_shareids = set()
    for key in peers_to_shares:
        for share in peers_to_shares[key]:
            servermap_shareids.add(share)

    # First check to see if the leases can be renewed.
    to_distribute = set()
    for share in homeless_shares:
        if share in servermap_shareids:
            for peerid in peers_to_shares:
                if share in peers_to_shares[peerid]:
                    mappings[share] = set([peerid])
                    break
        else:
            to_distribute.add(share)
    # This builds a priority queue of peers with the number of shares
    # each peer holds as the priority.
    priority = {}
    pQueue = PriorityQueue()
    for peerid in servermap_peerids:
        priority.setdefault(peerid, 0)
    for share in mappings:
        if mappings[share] is not None:
            for peer in mappings[share]:
                if peer in servermap_peerids:
                    priority[peer] += 1
    if priority == {}:
        return
    for peerid in priority:
        pQueue.put((priority[peerid], peerid))
    # Distribute the shares to peers with the lowest priority.
    for share in to_distribute:
        peer = pQueue.get()
        mappings[share] = set([peer[1]])
        pQueue.put((peer[0]+1, peer[1]))

def share_placement(peers, readonly_peers, shares, peers_to_shares={}):
    """
    Generate a flow network of peerids to existing shareids and find
    its maximum spanning graph. The leases of these shares should be renewed
    by the client.
    """

    servermap_peerids = set([key for key in peers_to_shares])
    servermap_shareids = set()
    for key in peers_to_shares:
        for share in peers_to_shares[key]:
            servermap_shareids.add(share)

    # 2. Construct a bipartite graph G1 of *readonly* servers to pre-existing
    #    shares, where an edge exists between an arbitrary readonly server S and an
    #    arbitrary share T if and only if S currently holds T.

    # First find the maximum spanning of the readonly servers.
    readonly_shares = set()
    readonly_map = {}
    for peer in peers_to_shares:
        if peer in readonly_peers:
            readonly_map.setdefault(peer, peers_to_shares[peer])
            for share in peers_to_shares[peer]:
                readonly_shares.add(share)

    peer_to_index = _index_peers(readonly_peers, 1)
    share_to_index, index_to_share = _reindex_shares(readonly_shares,
                                                          len(readonly_peers) + 1)
    # "graph" is G1
    graph = _servermap_flow_graph(readonly_peers, readonly_shares, readonly_map)
    shareids = [share_to_index[s] for s in readonly_shares]
    max_graph = _compute_maximum_graph(graph, shareids)

    # 3. Calculate a maximum matching graph of G1 (a set of S->T edges that has or
    #    is-tied-for the highest "happiness score"). There is a clever efficient
    #    algorithm for this, named "Ford-Fulkerson". There may be more than one
    #    maximum matching for this graph; we choose one of them arbitrarily, but
    #    prefer earlier servers. Call this particular placement M1. The placement
    #    maps shares to servers, where each share appears at most once, and each
    #    server appears at most once.

    # "max_graph" is M1 and is a dict which maps shares -> peer
    # (but "one" of the many arbitrary mappings that give us "max
    # happiness" of the existing placed shares)
    readonly_mappings = _convert_mappings(peer_to_index,
                                               index_to_share, max_graph)

    used_peers, used_shares = _extract_ids(readonly_mappings)

    #print("readonly mappings")
    #for k, v in readonly_mappings.items():
    #    print(" {} -> {}".format(k, v))

    # 4. Construct a bipartite graph G2 of readwrite servers to pre-existing
    #    shares. Then remove any edge (from G2) that uses a server or a share found
    #    in M1. Let an edge exist between server S and share T if and only if S
    #    already holds T.

    # Now find the maximum matching for the rest of the existing allocations.
    # Remove any peers and shares used in readonly_mappings.
    new_peers = servermap_peerids - used_peers
    new_shares = servermap_shareids - used_shares
    servermap = peers_to_shares.copy()
    for peer in peers_to_shares:
        if peer in used_peers:
            servermap.pop(peer, None)
        else:
            servermap[peer] = set(servermap[peer]) - used_shares
            if servermap[peer] == set():
                servermap.pop(peer, None)
                new_peers.remove(peer)

    # 5. Calculate a maximum matching graph of G2, call this M2, again preferring
    #    earlier servers.

    # Reindex and find the maximum matching of the graph.
    peer_to_index = _index_peers(new_peers, 1)
    share_to_index, index_to_share = _reindex_shares(new_shares, len(new_peers) + 1)
    graph = _servermap_flow_graph(new_peers, new_shares, servermap)
    shareids = [share_to_index[s] for s in new_shares]
    max_server_graph = _compute_maximum_graph(graph, shareids)
    existing_mappings = _convert_mappings(peer_to_index,
                                               index_to_share, max_server_graph)
    # "max_server_graph" is M2

    #print("existing mappings")
    #for k, v in existing_mappings.items():
    #    print(" {} -> {}".format(k, v))

    # 6. Construct a bipartite graph G3 of (only readwrite) servers to
    #    shares (some shares may already exist on a server). Then remove
    #    (from G3) any servers and shares used in M1 or M2 (note that we
    #    retain servers/shares that were in G1/G2 but *not* in the M1/M2
    #    subsets)

    existing_peers, existing_shares = _extract_ids(existing_mappings)
    new_peers = new_peers - existing_peers - used_peers
    new_shares = new_shares - existing_shares - used_shares

    # Generate a flow network of peerids to shareids for all peers
    # and shares which cannot be reused from previous file allocations.
    # These mappings represent new allocations the uploader must make.
    peer_to_index = _index_peers(new_peers, 1)
    share_to_index, index_to_share = _reindex_shares(new_shares, len(new_peers) + 1)
    peerids = [peer_to_index[peer] for peer in new_peers]
    shareids = [share_to_index[share] for share in new_shares]
    graph = _flow_network(peerids, shareids)

    # XXX I think the above is equivalent to step 6, except
    # instead of "construct, then remove" the above is just
    # "remove all used peers, shares and then construct graph"

    # 7. Calculate a maximum matching graph of G3, call this M3, preferring earlier
    #    servers. The final placement table is the union of M1+M2+M3.

    max_graph = _compute_maximum_graph(graph, shareids)
    new_mappings = _convert_mappings(peer_to_index, index_to_share,
                                                                    max_graph)
    #print("new mappings")
    #for k, v in new_mappings.items():
    #    print(" {} -> {}".format(k, v))

    # "the final placement table"
    mappings = dict(readonly_mappings.items() + existing_mappings.items()
                    + new_mappings.items())
    homeless_shares = set()
    for share in mappings:
        if mappings[share] is None:
            homeless_shares.add(share)
    if len(homeless_shares) != 0:
        _distribute_homeless_shares(mappings, homeless_shares, peers_to_shares)

    return mappings
