FROM ubuntu:16.04

# ------ Setup certificates and repositories ------ #
RUN apt-get update -y && apt-get install -y \
    ca-certificates \
    curl \
    apt-transport-https

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88
RUN echo "deb https://repo.sovrin.org/deb xenial stable" >> /etc/apt/sources.list
RUN echo "deb https://repo.sovrin.org/sdk/deb xenial stable" >> /etc/apt/sources.list