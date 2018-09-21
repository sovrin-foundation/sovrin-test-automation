FROM sovrin_xenial

# ------ Environment Args ------ #

# ------ Install dependencies ------ #
RUN apt-get update -y && apt-get -y install \
    libsovtoken \
    indy-cli

# ------ Add local files ------ #
ADD ./scripts /scripts
ADD ./genesis_txn.txt /tmp/genesis_txn.txt
ADD ./batch_cli_startup.txt /tmp/batch_cli_startup.txt

RUN echo "export PATH=$PATH:/scripts" >> $HOME/.bash_profile;

ENTRYPOINT /bin/bash -c "source $HOME/.bash_profile; /bin/bash"