FROM sovrin_xenial

# ------ Environment Args ------ #
ARG pool_ip=pool

# ------ Install packages ------ #
RUN apt-get update -y && apt-get -y install \
    sovrin \
    sovtokenfees \
    supervisor 

# ------ Start up nodes ------ #
ADD ./setup.sh /tmp/setup.sh
RUN /bin/bash /tmp/setup.sh ${pool_ip}

EXPOSE 9701 9702 9703 9704 9705 9706 9707 9708

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
