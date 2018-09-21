Provides docker images to run the indy-cli and libsovtoken with a pool of 4
nodes containing the payment plugins.

## Setup base image
This builds the base image used by the client and pool services. Unless there
are future changes, you should only have to run this command once.
```
docker build -t sovrin_xenial ./base
```

## Access client
To access the client container. This will take some time the first time you run
this.
```
docker-compose run client
```
This will start the pool automatically. You can also start the pool with
`docker-compose up`.


## Get started with indy-cli
Once you have accessed the client container, you can interact with indy-cli.

### Startup Script
There is a startup script, which will create the pool config, connect to the
pool, create a wallet, 4 trustees, and mints 1 token (100000000 sovatoms) to
the address `pay:sov:24AE7WLojJd3Z22L6CAY876cLbGskZd3N4ocaE9T1jwX6MXtvP`
```
bash startup.sh
```

### Starting indy-cli
Otherwise, you can access the cli normally. You do need to load in libsovtoken
every time for payment functionality.
```
indy-cli

// These next commands will be run in the cli. Your terminal should start with
// indy>

load-plugin library=/usr/lib/libsovtoken.so initializer=sovtoken_init

// This pool config is already created if you run the startup script.
pool create sovrin_payment_pool gen_txn_file=tmp/genesis_txn.txt

pool connect sovrin_payment_pool protocol-version=2 timeout=15

// This wallet is already created if you run the startup script.
wallet create wallet_sovrin key=sov

wallet open wallet_sovrin key=sov
```