FROM sovrin_xenial

# ------ Environment Args ------ #
ARG node_num
ARG port_client
ARG port_node
ENV node_num=${node_num}
ENV port_client=${port_client}
ENV port_node=${port_node}

# ------ Install packages ------ #
RUN apt-get update -y && apt-get -y install \
    sovrin \
    sovtokenfees 

# ------ Start up node ------ #
RUN generate_indy_pool_transactions \
    --nodes 4 \
    --clients 1 \
    --nodeNum ${node_num} \
    --ips="node1,node2,node3,node4"

EXPOSE ${port_node} ${port_client}

CMD start_indy_node "Node${node_num}" 0.0.0.0 ${port_node} 0.0.0.0 ${port_client}