# SPDX-FileCopyrightText: 2025 Natalie Cuthbert <natalie@cuthbert.co.za>
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy 


SOCK_AVAILABILITY_TABLE = {
    'GEOMETRY':    ('NodeSocketFloat', 'NodeSocketInt', 'NodeSocketVector', 'NodeSocketColor', 'NodeSocketBool', 'NodeSocketRotation', 'NodeSocketMatrix', 'NodeSocketString', 'NodeSocketMenu', 'NodeSocketObject', 'NodeSocketGeometry', 'NodeSocketCollection', 'NodeSocketTexture', 'NodeSocketImage', 'NodeSocketMaterial',),
}

TREE_TO_GROUP_EQUIV = {        
    'GeometryNodeTree': 'GeometryNodeGroup',
}


def get_all_nodes(ignore_ng_name:str="RigNodes", approxmatch_idnames:str="", exactmatch_idnames: set | None = None, ngtypes:set | None =None) -> set|list:
    """get nodes instances across many nodetree editor types.
    - ngtypes: the editor types to be supported in {'GEOMETRY'}. will use all if None
    - ignore_ng_name: ignore getting nodes from a nodetree containing a specific name.
    - approxmatch_idnames: only get nodes whose include the given token.
    - exactmatch_idnames: only get nodes included in the set of given id names.
    """
 
    if (ngtypes is None):
        ngtypes = {'GEOMETRY'}

    nodes = set()

    for ng in bpy.data.node_groups:
        
        #does the type of the nodegroup correspond to what we need?
        if (ng.type not in ngtypes):
            continue
        
        #we ignore specific ng names?
        if (ignore_ng_name and (ignore_ng_name in ng.name)):
            continue
        
        #batch add all these nodes.
        nodes.update(ng.nodes)
        continue

    #only node with matching exact id?
    if (exactmatch_idnames):
        nodes = [n for n in nodes if (n.bl_idname in exactmatch_idnames)]

    #only with node with 
    if (approxmatch_idnames):
        nodes = [n for n in nodes if (approxmatch_idnames in n.bl_idname)]

    return nodes


def send_refresh_signal(socket):
    """lazy trick to send a refresh signal to the nodetree"""

    if (not socket.links):
        return None

    node_tree = socket.id_data 
    
    links_data = []
    for link in socket.links:
        links_data.append((link.to_socket, link.to_node))
    
    # Perform unlink/relink
    links_to_remove = list(socket.links)
    for link in links_to_remove:
        node_tree.links.remove(link)
    
    for to_socket, to_node in links_data:
        node_tree.links.new(socket, to_socket)
    
    return None
