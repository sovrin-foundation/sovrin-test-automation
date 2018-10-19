#!/bin/bash
args=$#
args_left=$args

fees=''
fees_def='
    1:0
    100:0
    101:0
    102:0
    1001:0
'
genesis_path=''
libsovtoken_path='/usr/lib/libsovtoken.so'
pool_name=''
seed_trustess=false
setup_sovtoken_only=false
sovtoken_install=false
sovtoken_packages_def='sovtoken sovtokenfees'
sovtoken_packages=''
wallet_name='default'
wallet_key="${WALLET_KEY}"
trustee_seeds_def='
    000000000000000000000000Trustee1,V4SGRU86Z58d6TV7PBUe6f
    000000000000000000000000Trustee2,LnXR1rPnncTPZvRdmJKhJQ
    000000000000000000000000Trustee3,PNQm3CwyXbN5e39Rw3dXYx
'
trustee_dids_def='
    V4SGRU86Z58d6TV7PBUe6f
    LnXR1rPnncTPZvRdmJKhJQ
    PNQm3CwyXbN5e39Rw3dXYx
'
trustee_seeds=""
trustee_dids=""

##- Functions -##
function check_install_sovtoken {
    local pkgs_installed=false
    local plist
    local installed
    local ns_split
    local nsp
    local nsv
    local p_split
    local p
    local spd
    local v
    local vers_ins_str

    if [ -z "$sovtoken_packages" ] ; then
        sovtoken_packages="$sovtoken_packages_def"
    fi
    #Add in our default packages
    for spd in $sovtoken_packages_def ; do
        if ! val_in_array "$spd" "$sovtoken_packages" ; then
            sovtoken_packages="$sovtoken_packages $spd"
        fi
    done
    #Get our list of installed sovtoken packages from dpkg
    plist=( $(/usr/bin/dpkg-query -f '${Package}|${Version}\n' -W $(echo $sovtoken_packages | tr ' ' '\n' | cut -d ',' -f 1) 2>/dev/null) )
    #Sort list of packages "sovtoken" must come before sovtokenfees, and convert to bash array
    sovtoken_packages=( $(echo "$sovtoken_packages" | sort) )
    #Loop through each sovtoken package and make sure it is installed and at correct version if specified
    for sp in "${sovtoken_packages[@]}" ; do
        #Split up the sovtoken package to get the needed package name and version
        ns_split=( ${sp//,/ } )
        nsp=${ns_split[0]}
        nsv=${ns_split[1]}
        #If a version was specified, generate a string to use for apt-get install
        if [ ! -z "$nsv" ] ; then
            vers_inst_str="=${nsv}"
        fi
        installed=false
        #Compare our needed sovtoken package to the ones returned from dpkg that are already installed
        for pinf in "${plist[@]}" ; do
            p_split=( ${pinf//|/ } )
            p=${p_split[0]}
            v=${p_split[1]}
            if [ "$nsp" == "$p" ] ; then
                #Check that the correct version is installed
                if [ ! -z "$nsv" ] ; then
                    if [ "$v" == "$nsv" ] ; then
                        installed=true
                        break
                    fi
                else
                    installed=true
                    break
                fi
            fi
        done
        if [ "$installed" = false ] ; then
            /usr/bin/apt-get install "${nsp}${vers_ins_str}"
            pkgs_installed=true
        fi
    done
    if [ "$pkgs_installed" == true ] ; then
        restart_indy_node
        echo -n
    fi
}

function pre_check {
    if [ ! -f "$(which indy-cli)" ] ; then
        echo "Error: Can't find indy-cli"
        exit 1
    fi
    if [ ! -f "$libsovtoken_path" ] ; then
        echo "Error: Can't find /usr/lib/libsovtoken.so"
        exit 1
    fi
    if [ -z "$wallet_key" -a "$setup_sovtoken_only" != true ] ; then
        echo "Error: No wallet key was passed. Please set either --wallet-key or set the environment variable WALLET_KEY"
        exit 1
    fi
}

function restart_indy_node {
    local sctl_indy_node=( $(/bin/systemctl list-unit-files | grep enabled | grep indy | grep -v control | grep -o '^indy.\w\+') )
    if [ "${#sctl_indy_node[@]}" -eq 0 ] ; then
        echo "No indy-node systemctl files found, aborting indy-node restart."
        echo "Please restart the ledger yourself"
        exit 1
    fi
    if /bin/systemctl is-active indy-node-control.service >/dev/null ; then
        echo "Stopping indy-node-control.service"
        /bin/systemctl stop indy-node-control.service
        sleep 2
    fi
    echo "Making sure that indy-node process(es) are stopped"
    for indy_n in "${sctl_indy_node[@]}"; do
        if /bin/systemctl is-active $indy_n >/dev/null; then
            echo "Stopping still active $indy_n service"
            /bin/systemctl stop $indy_n
        fi
    done
    echo "Starting up indy-node process(es)"
    for indy_n in "${sctl_indy_node[@]}"; do
        if ! /bin/systemctl is-active $indy_n >/dev/null; then
            echo "Starting $indy_n service"
            /bin/systemctl start $indy_n
        fi
    done
    if ! /bin/systemctl is-active indy-node-control.service >/dev/null; then
        echo "Starting indy-node-control.service"
        /bin/systemctl start indy-node-control.service
    fi
}

function parse_text_table {
    local hl=0
    local prev_cmd
    while read line; do
        if [[ "$line" =~ ^\+-+ ]] ; then
            let hl+=1
            continue
        else
            if [[ $hl == 0 ]] ; then
                prev_cmd="$line"
            fi
        fi
        if [ -z "$line" ] ; then
            cmd_pref=''
            hl=0
            continue
        fi
        if [[ $hl -ge 2 ]] ; then
            echo "$line" | sed 's/^| //; s/ |$//; s/ //g' | sed "s/^/${prev_cmd// /%20}|/"
        fi
    done
}

function process_multi_sig_txn {
    local cli_context
    local res
    local to_sign="$1"
    local trustee_dids_array=( $trustee_dids )
    local primary_did=${trustee_dids_array[0]}
    
    printf -v cli_context "wallet open ${wallet_name} key=${wallet_key}"
    printf -v cli_context "$cli_context\npool connect ${pool_name}\n"
    for did in "${trustee_dids_array[@]}" ; do
        res=$(echo -e "${cli_context}\ndid use $did\nledger sign-multi txn=$to_sign" | run_indy_cmd)
        if [ $? -ne 0 ] ; then
            echo "## ERROR: Could not sign txn using did: $did"
            echo "--------------"
            echo "$res"
            echo "--------------"
            exit 1
        fi
        to_sign=$(echo "$res" | sed 's/\x1B\[[0-9;]\+[A-Za-z]//g' | grep -o '^ *{.*}$' | sed 's/^ *//g')
        echo "## New output to sign: $to_sign"
    done
    #Finalize the txn
    res=$(echo -e "${cli_context}\ndid use $primary_did\nledger custom $to_sign" | run_indy_cmd)
    if [ $? -ne 0 ] ; then
        echo "## ERROR: Could not finalize transaction with signed txn"
        echo "--------------"
        echo "$res"
        echo "--------------"
        exit 1
    fi
}

function run_indy_cmd {
    local cmd="$1"
    local parse_table=$2
    local hl
    local out
    local pout
    local cmd_pref
    local prev_line

    #Read from stdin if $cmd is empty
    if [ -z "$cmd" ] ; then
        while read line; do
            printf -v cmd "${cmd}\n${line}"
        done
    fi
    cli_res=$(indy-cli --plugins /usr/lib/libsovtoken.so:sovtoken_init <<EOF
$cmd
EOF
)   
    # Check to see if we got an error
    if echo "$cli_res" | grep -qi 'execution failed' ; then
        echo "$cli_res"
        return 1
    fi
    if [ "$parse_table" == true ] ; then
        out=$(echo "$cli_res" | parse_text_table)
    else
        out="$cli_res"
    fi
    if [ ! -z "$out" ] ; then
        echo "$out"
    fi
}

function set_fees {
    local trustee_dids_array
    local primary_did
    local cli_context
    local prepare
    local prepare_cmd
    local res
    local to_sign

    if [ -z "$trustee_dids" ] ; then
        trustee_dids="$trustee_dids_def"
    fi
    if [ -z "$fees" ] ; then
        fees="$fees_def"
    fi
    fees=( $fees )
    fees="${fees[*]}"
    fees="${fees// /,}"
    trustee_dids_array=( $trustee_dids )
    primary_did=${trustee_dids_array[0]}
    printf -v cli_context "wallet open ${wallet_name} key=${wallet_key}"
    printf -v cli_context "$cli_context\npool connect ${pool_name}\n"
    printf -v prepare_cmd "$cli_context\ndid use $primary_did\n"
    echo "## Preparing to set fees"
    prepare=$(run_indy_cmd "${prepare_cmd}ledger set-fees-prepare payment_method=sov fees=$fees")
    if [ $? -ne 0 ] ; then
       echo "## ERROR: Could not run set-fees-prepare statement"
       echo "--------------"
       echo "$prepare"
       echo "--------------"
       exit 1
    fi
    to_sign=$(echo "$prepare" | sed 's/\x1B\[[0-9;]\+[A-Za-z]//g' | grep -o '^ *{.*}$' | sed 's/^ *//g')
    echo "## Will sign SET_FEES transaction: $to_sign"
    process_multi_sig_txn "$to_sign"
    # Show current fees
    echo "## Displaying current fees after out change"
    echo -e "${cli_context}\ndid use $primary_did\nledger get-fees payment_method=sov" | run_indy_cmd | grep -E '\-\+|\|'
}

function seed_trustees {
    echo "## Seeding trustees into wallet"
    local cur_dids=$(echo -e "wallet open ${wallet_name} key=${wallet_key}\ndid list" |run_indy_cmd '' true)
    local cur_did_array=()
    local cli_context
    local cli_context_did
    local cli_context_did_ledger
    local ledger_out
    local new_did
    local new_did_out
    local new_did_verkey
    local primary_did
    local seeds_array

    printf -v cli_context "wallet open ${wallet_name} key=${wallet_key}\n"
    if [ -z "$trustee_seeds" ] ; then
        trustee_seeds="$trustee_seeds_def"
    fi
    seeds_array=( $trustee_seeds )
    if [ $? -ne 0 ] ; then
       echo "## ERROR: Could not list dids in the wallet"
       echo "--------------"
       echo "$dids"
       echo "--------------"
    fi
    primary_did=${seeds_array[0]}
    primary_did=( ${primary_did//,/ } )
    primary_did=${primary_did[1]}
    printf -v cli_context_did "${cli_context}\ndid use ${primary_did}\n"
    printf -v cli_context_did_ledger "${cli_context_did}\npool connect ${pool_name}\n"
    if [ ! -z "$cur_dids" ] ; then
        cur_did_array=( $cur_dids )
    fi
    for seed in "${seeds_array[@]}"; do
        did_exists=false
        s_split=( ${seed//,/ } )
        s_did="${s_split[1]}"
        s_seed="${s_split[0]}"
        for de in "${cur_did_array[@]}" ; do
            d_split=( ${de//|/ } )
            did="${d_split[1]}"
            if [ "$did" == "$s_did" ] ; then
                did_exists=true
                break
            fi
        done
        if [ "$did_exists" == false ] ; then
            new_did_out=$(run_indy_cmd "${cli_context}did new seed=${s_seed}")
            if [ $? -ne 0 ] ; then
                echo "## ERROR: Could not add did from seed: ${s_seed} to wallet: ${wallet_name}"
                echo "--------------"
                echo "$new_did_out"
                echo "--------------"
                exit 1
            fi
            new_did_out=$(echo "$new_did_out" | grep 'has been created' | sed 's/.\+"\(.\+\)" has been created with "\(.\+\)".\+/\1,\2/')
            new_did_out=( ${new_did_out//,/ } )
            new_did=${new_did_out[0]}
            new_did_verkey=${new_did_out[1]}
            echo "## Added new DID: ${new_did} to the wallet: ${wallet_name}"
            echo "## Adding new DID: ${new_did} with verkey: ${new_did_verkey} to the ledger pool: ${pool_name}"
            ledger_out=$(run_indy_cmd "${cli_context_did_ledger}ledger nym did=${new_did} verkey=${new_did_verkey} role=TRUSTEE")
            if [ $? -ne 0 ] ; then
                echo "## ERROR: Could not add did: ${new_did} to the ledger pool: ${pool_name}"
                echo "--------------"
                echo "$ledger_out"
                echo "--------------"
                exit 1
            fi
        else
            echo "## DID: ${s_did} already exists in wallet, skipping" >&2
        fi
    done
}

function setup_indy_cli {
    setup_pool
    setup_wallet
}

function setup_pool {
    local pools
    local pn_set=false
    local pool_array=()
    local p_split
    local p

    pools=$(run_indy_cmd 'pool list' true)
    if [ $? -ne 0 ] ; then
       echo "## ERROR: Could not list current pools"
       echo "--------------"
       echo "$pools"
       echo "--------------"
    fi
    if [ ! -z "$pools" ] ; then
        pool_array=( "$pools" )
    fi
    if [ "${#pool_array[@]}" -eq 1 ] ; then
        if [ -z "$pool_name" ] ; then
            p_split=${pool_array[0]}
            p_split=( ${p_split//|/ } )
            pool_name=${p_split[1]}
            pn_set=true
        fi
    fi
    if [ "$pn_set" == false ] ; then
        if [ -z "$pool_name" ] ; then
            echo "## ERROR: No pool name specified, please specify which pool to use with --pool-name"
            exit 2
        fi
        for p in "${pool_array[@]}" ; do
            p_split=( ${p//|/ } )
            if [ "${p_split[1]}" == "$pool_name" ] ; then
                pn_set=true
            fi
        done
    fi
    if [ "$pn_set" == false ] ; then
        if [ -z "$genesis_path" ] ; then
            echo "## ERROR: Cannot create pool: $pool_name, you must supply a genesis file with --genesis-path"
            exit 2
        fi
        echo "## Creating new pool: ${pool_name} from genesis file: ${genesis_path}"
        if ! run_indy_cmd "pool create ${pool_name} gen_txn_file=${genesis_path}" true ; then
            echo "## ERROR: Errors ocurred trying to create pool"
            exit 2
        fi
    fi
}

function setup_wallet {
    local wallets
    local wn_set=false
    local wallet_array=()
    local w_split
    local w

    wallets=$(run_indy_cmd 'wallet list' true)
    if [ $? -ne 0 ] ; then
       echo "## ERROR: Could not list current wallets"
       echo "--------------"
       echo "$wallets"
       echo "--------------"
    fi
    if [ ! -z "$wallets" ] ; then
        wallet_array=( "$wallets" )
    fi
    if [ "${#wallet_array[@]}" -eq 1 ] ; then
        if [ -z "$wallet_name" ] ; then
            w_split=${wallet_array[0]}
            w_split=( ${w_split//|/ } )
            wallet_name=${w_split[1]}
            wn_set=true
        fi
    fi
    if [ "$wn_set" == false ] ; then
        if [ -z "$wallet_name" ] ; then
            echo "## ERROR: No wallet name specified, please specify which pool to use with --wallet-name"
            exit 2
        fi
        for w in "${wallet_array[@]}" ; do
            w_split=( ${w//|/ } )
            if [ "${w_split[1]}" == "$wallet_name" ] ; then
                wn_set=true
            fi
        done
    fi
    if [ "$wn_set" == false ] ; then
        if [ -z "$wallet_key" ] ; then
            echo "## ERROR: Cannot create wallet: $wallet_name, you must supply a wallet key either with --wallet-key or setting environment variable WALLET_KEY"
            exit 2
        fi
        echo "## Creating new wallet: ${wallet_name}"
        if ! run_indy_cmd "wallet create ${wallet_name} key=${wallet_key}" true; then
            echo "## ERROR: Errors ocurred trying to create wallet"
            exit 2
        fi
    fi
}

function val_in_array {
    local ar="$2"
    local val="$1"
    for ae in $ar ; do
        ar_split=( ${ae//,/ } )
        arp=${ar_split[0]}
        if [ "$arp" == "$val" ] ; then
            return 0
        fi
    done
    return 1
}

function help {
cat <<EOF
Usage: $(basename $0) <OPTIONS>

    OPTIONS:
        --fee <TYPE:COST>     Add a new fee for TYPE that costs COST. Add
                              multiple --fee options for setting multiple fees
                              [NOTE] If this option is omitted, then all fees
                              will be set to 0
        --genesis-path <path> Path to genesis file when there is pool that has
                              been created in a wallet. Used to create a new
                              pool
        --install-sovtoken    Check and make sure that the sovtoken packages
                              are installed to ledger on this node.
        --pool-name <name>    Name of the pool to connect to for ledger
                              operations. If there is only one pool found,
                              then it will be used, if this option wasn't passed
        --setup-sovtoken-only When this is set, only check to make sure that
                              proper sovtoken and pre-reqs are installed, but
                              don't worry about actually setting fees or
                              checking/setting up indy-cli and wallet
        --seed-trustees       When this is set, try and add new seeds and dids
                              to the wallet an ledger
        --sovtoken-vers <version>
                              Version of the sovtoken package, to make sure is 
                              installed when using the option --install-sovtoken
        --sovtokenfees-vers <version>
                              Version of the sovtokenfees package, to make sure
                              is installed when using the option
                              --install-sovtoken
        --trustee-seed <SEED,DID>
                              Both SEED and DID are required, and should be
                              separated with a comma. This is used in
                              conjunction with --seed-trustees. This will make
                              sure that the seed SEED is added to the wallet. 
                              If it was found NOT to be in the wallet, then
                              after adding to the wallet it will also be added
                              to the ledger with the TRUSTEE role.
                              [NOTE] Pass this option multiple times to add
                              multiple dids. The first one passed will be the
                              DID used to talk to the ledger
        --trustee-did <DID>   This a DID that is used to sign the multi-sig
                              txn. Pass this multiple times to sign with more
                              than one DID. The first one passed will be the
                              one to create the initial transaction as well as
                              submit to the ledger.
                              [NOTE] The DIDs mentioned here must be in the
                              wallet as well as on the ledger
        --wallet-name <NAME>  The wallet name to open or create for operations.
                              If there is only one wallet found, then it will
                              be used, if this option wasn't passed.
        --wallet-key <KEY>    Wallet key to use for opening the wallet name
                              passed with --wallet-name. This option is
                              REQUIRED. But can be set with the environment
                              variable WALLET_KEY
        --help,-h             Display this help
EOF
}

##- Argument Parsing -##
while [ $args_left -ge 1 ] ; do
    case "$1" in
        --fee)
            if [ ! -z "$2" ] ; then
                fees="$fees ${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --genesis-path)
            if [ ! -z "$2" ] ; then
                genesis_path="${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --install-sovtoken)
            sovtoken_install=true
            ;;
        --pool-name)
            if [ ! -z "$2" ] ; then
                pool_name="${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --setup-sovtoken-only)
            setup_sovtoken_only=true
            sovtoken_install=true
            ;;
        --seed-trustees)
            seed_trustees=true
            ;;
        --sovtoken-vers)
            if [ ! -z "$2" ] ; then
                sovtoken_packages="$sovtoken_packages sovtoken,${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --sovtokenfees-vers)
            if [ ! -z "$2" ] ; then
                sovtoken_packages="$sovtoken_packages sovtokenfees,${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --trustee-seed)
            if [ ! -z "$2" ] ; then
                trustee_seeds="$trustee_seeds ${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --trustee-did)
            if [ ! -z "$2" ] ; then
                trustee_dids="$trustee_dids ${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --wallet-name)
            if [ ! -z "$2" ] ; then
                wallet_name="${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --wallet-key)
            if [ ! -z "$2" ] ; then
                wallet_key="${2}"
                shift
                let args_left=args_left-1
            fi
            ;;
        --help|-h)
            help
            exit 0
            ;;
        *)
            echo "Unknown argument: $1"
    esac
    shift
    let args_left=args_left-1
done

##- Main -##
pre_check
if [ "$sovtoken_install" == true ] ; then
    check_install_sovtoken
fi
if [ "$setup_sovtoken_only" == true ] ; then
    exit 0
fi
setup_indy_cli
if [ "$seed_trustees" == true ] ; then
    seed_trustees
fi
set_fees
