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
The startup script will:
1. Create a pool config called `sovrin_payment_pool`
2. Create a wallet called `wallet_sovrin` with the key `sov`.
3. Create two payment addresses:
    1. `pay:sov:24AE7WLojJd3Z22L6CAY876cLbGskZd3N4ocaE9T1jwX6MXtvP`
    2. `pay:sov:2ViUZnYGwYxx2EztvxAYq8re9ysmCVbzF72jTCXMKzrxUqGqut`
4. Mint 1 token (100000000 sovatoms) to payment address `pay:sov:24AE7WLojJd3Z22L6CAY876cLbGskZd3N4ocaE9T1jwX6MXtvP`

```
bash startup.sh
```

### Other Scripts
There are a few other scripts you can make use of as well. These are under the assumption the `startup.sh` script has been run.

#### fees_set
Will set the fees accordingly:

'1' (NYM) => 1,

'100' (ATTRIB) => 5,

'101' (SCHEMA) => 10,

'102' (CLAIM DEF) => 20,

'113' (REVOC_REG_DEF) => 30,

'114' (REVOC_REG_ENTRY) => 30,

'10001' (XFER_PUBLIC) => 6

```
bash fees_set.sh
```

#### fees_reset
Will set the fees set in the `fees_set.sh` script to 0:

'1' (NYM) => 0,

'100' (ATTRIB) => 0,

'101' (SCHEMA) => 0,

'102' (CLAIM DEF) => 0,

'113' (REVOC_REG_DEF) => 0,

'114' (REVOC_REG_ENTRY) => 0,

'10001' (XFER_PUBLIC) => 0

```
bash fees_reset.sh
```

### Starting indy-cli
You can access the cli manually. You do need to load in libsovtoken
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

## Other useful commands
Docker will use a cache, so if you want to rebuild with the latest packages, run:
```
docker-compose build --no-cache
```