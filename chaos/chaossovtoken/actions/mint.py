from chaosindy.common import *
from chaosindy.common.cli.operations import cli_create_pool, \
    cli_create_wallet, cli_create_local_did, cli_create_ledger_did, \
    cli_create_payment_address, cli_mint_tokens
from chaossovtoken.common import *
from logzero import logger
from typing import Union, List


# TODO: Modify to allow more than one wallet? One wallet per Trustee?
def mint_from_cli(genesis_file: str, sovatoms: Union[int,str],
                  did: str = DEFAULT_CHAOS_TRUSTEE_DID1,
                  trustee_seed: str = DEFAULT_CHAOS_TRUSTEE_SEED1,
                  number_of_signing_trustees: Union[int,str] = len(DEFAULT_CHAOS_TRUSTEE_DICT.keys()),
                  payment_address: str = DEFAULT_CHAOS_PAYMENT_ADDRESS1,
                  payment_address_method: str = DEFAULT_CHAOS_PAYMENT_ADDRESS_METHOD1,
                  payment_address_seed: str = DEFAULT_CHAOS_PAYMENT_ADDRESS_SEED1,
                  wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
                  wallet_key: str = DEFAULT_CHAOS_WALLET_KEY,
                  pool: str = DEFAULT_CHAOS_POOL,
                  plugin_path: str = DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_PATH,
                  plugin_initializer: str = DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_INITIALIZER,
                  timeout: Union[str,int] = DEFAULT_CHAOS_LEDGER_TRANSACTION_TIMEOUT,
                  ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Mint sovatoms into a payment address

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param sovatoms: The number of sovatoms to mint
    :type sovatoms: Union[int,str]
    :param did: A trustee DID
        Optional when seed kwargs are not given. Otherwise, required.
        (Default: chaosindy.common.DEFAULT_CHAOS_TRUSTEE_DID1)
    :type did: str
    :param trustee_seed : A steward or trustee seed. 1 of 3 or more required for
        minting. A did OR a seed is required, but not both. The did will be used
        if both are given. Needed to prepare and submit the minting transaction.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_TRUSTEE_SEED1)
    :type trustee_seed: str
    :param number_of_signing_trustees: The minimum number of trustees required
        to mint. Note: This will likely/eventually be controled by the config
        ledger.
        Optional. (Default: len(DEFAULT_CHAOS_TRUSTEE_DICT.keys()))
    :type number_of_signing_trustees: str
    :param payment_address: A payment address to receive minted tokens. A
        payment_address OR a payment_address_seed is required, but not both. The
        payment_address will be used if both are given.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_PAYMENT_ADDRESS1)
    :type payment_address: str
    :param payment_address_method: A payment address method. Required if
        payment_address_seed is given.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_PAYMENT_ADDRESS_METHOD1)
    :type payment_address_method: str
    :param payment_address_seed: A payment address seed. A payment_address OR a
        payment_address_seed is required, but not both. The payment_address will
        be used if both are given.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_PAYMENT_ADDRESS_SEED1)
    :type payment_address_seed: str
    :param wallet_name: The name of the wallet to use when getting validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_NAME)
    :type wallet_name: str
    :param wallet_key: The key to use when opening the wallet designated by
        wallet_name.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_KEY)
    :type wallet_key: str
    :param pool: The pool to connect to when getting validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_POOL)
    :type pool: str
    :param plugin_path: The path to the plugin's .so file. Include lib in this
        string. Example /usr/lib/libsovtoken.so
        Optional. (Default: chaossovtoken.common.DEFAULT_LIBSOVTOKEN_PLUGIN_PATH)
    :type plugin_path: str
    :param plugin_initializer: The initializer function/method to call while
        loading the plugin.
        Optional. (Default: chaossovtoken.common.DEFAULT_LIBSOVTOKEN_PLUGIN_INITIALIZER)
    :type plugin_initializer: str
    :param timeout: How long indy-cli can take to perform the operation before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_LEDGER_TRANSACTION_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """
    output_dir = get_chaos_temp_dir()

    # IMPORTANT! - Many of the following create_ calls blocks could
    #              theoretically be combined into one script. However, Indy CLI
    #              bails out on the first command that fails. "Already exists"
    #              failures are okay... Therefore, any operations that can fail
    #              should be in their own batch file.

    # Ensure that a pool and a wallet exist. Ignore errors when one or both
    # "already exist"

    # Pool creation
    if not cli_create_pool(output_dir, pool, genesis_file):
        logger.error("Unable to create pool via CLI -- genesis_file:%s", genesis_file)
        return False


    # Wallet creation
    if not cli_create_wallet(output_dir, wallet_name, wallet_key):
        logger.error("Unable to create wallet via CLI -- wallet_name:%s", wallet_name)
        return False

    # Trustee 1 DID creation
    if trustee_seed:
        logger.info("Create Trustee DID")
        cli_create_local_did(output_dir,
                             trustee_seed,
                             wallet_name,
                             wallet_key=wallet_key,
                             did_metadata="Default Trustee")


    # DID creation for all other Trustees
    # As Trustee 1, ensure Trustee2-4 have the trustee role. This assumes that
    # the first trustee has already been given the Trustee role. In other words,
    # the DID associated with the 0000000000000000000000Trustee1 seed was given
    # the role of Trustee when the pool was setup.
    for i in range(2, number_of_signing_trustees + 1):
        cli_create_ledger_did(output_dir,
                              did,
                              DEFAULT_CHAOS_TRUSTEE_DICT[i]['did'],
                              DEFAULT_CHAOS_TRUSTEE_DICT[i]['verkey'],
                              DEFAULT_CHAOS_TRUSTEE_DICT[i]['seed'],
                              "TRUSTEE",
                              pool,
                              wallet_name,
                              wallet_key=wallet_key,
                              did_metadata="Trustee " + str(i)
                             )

    if payment_address_seed:
        cli_create_payment_address(output_dir,
                                   payment_address_seed,
                                   payment_address_method,
                                   plugin_path,
                                   plugin_initializer,
                                   wallet_name,
                                   wallet_key=wallet_key)

    trustee_dids = [did]
    for _, value in DEFAULT_CHAOS_TRUSTEE_DICT.items():
        trustee_dids.append(value['did'])

    return cli_mint_tokens(output_dir,
                           did,
                           trustee_dids,
                           payment_address,
                           sovatoms,
                           plugin_path,
                           plugin_initializer,
                           pool,
                           wallet_name,
                           wallet_key=wallet_key)


def mint_by_strategy(genesis_file: str, sovatoms: Union[int,str],
    mint_strategy: int, did: str = DEFAULT_CHAOS_TRUSTEE_DID1,
    seed: str = DEFAULT_CHAOS_TRUSTEE_SEED1,
    number_of_signing_trustees: Union[int,str] = len(DEFAULT_CHAOS_TRUSTEE_DICT.keys()),
    payment_address: str = DEFAULT_CHAOS_PAYMENT_ADDRESS1,
    payment_address_method: str = DEFAULT_CHAOS_PAYMENT_ADDRESS_METHOD1,
    payment_address_seed: str = DEFAULT_CHAOS_PAYMENT_ADDRESS_SEED1,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    plugin_path: str = DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_PATH,
    plugin_initializer: str = DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_INITIALIZER,
    timeout: Union[str,int] = DEFAULT_CHAOS_LEDGER_TRANSACTION_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Mint tokens using a given strategy

    Returns False if it fails. Otherwise, a dictionary containing information
    required at a later time to rollback changes. The caller is expected to
    perform a predicate check on the returned value.

    Call clean_pool to undo what is done by mint_by_strategy. TODO: provide
    a way to rollback minting side effects.

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param sovatoms: The number of sovatoms to mint
    :type sovatoms: Union[int,str]
    :param mint_strategy: A mint strategy defined by the
        chaossovtoken.common.SovtokenStrategy enum. Examples include:
        SovtokenStrategy.CLI
        SovtokenStrategy.SDK - Not Yet Implemented (NYI)
    :type mint_strategy: int
    :param did: A trustee DID
        Optional when seed kwargs are not given. Otherwise, required.
        (Default: chaosindy.common.DEFAULT_CHAOS_TRUSTEE_DID1)
    :type did: str
    :param seed : A steward or trustee seed. 1 of 3 or more required for
        minting. A did OR a seed is required, but not both. The did will be used
        if both are given. Needed to prepare and submit the minting transaction.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_TRUSTEE_SEED1)
    :type seed: str
    :param number_of_signing_trustees: The minimum number of trustees required
        to mint. Note: This will likely/eventually be controled by the config
        ledger.
        Optional. (Default: len(DEFAULT_CHAOS_TRUSTEE_DICT.keys()))
    :type seed: str
    :param payment_address: A payment address to receive minted tokens. A
        payment_address OR a payment_address_seed is required, but not both. The
        payment_address will be used if both are given.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_PAYMENT_ADDRESS1)
    :type payment_address: str
    :param payment_address_seed: A payment address seed. A payment_address OR a
        payment_address_seed is required, but not both. The payment_address will
        be used if both are given.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_PAYMENT_ADDRESS_SEED1)
    :type payment_address_seed: str
    :param wallet_name: The name of the wallet to use when getting validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_NAME)
    :type wallet_name: str
    :param wallet_key: The key to use when opening the wallet designated by
        wallet_name.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_KEY)
    :type wallet_key: str
    :param pool: The pool to connect to when getting validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_POOL)
    :type pool: str
    :param plugin_path: The path to the plugin's .so file. Include lib in this
        string. Example /usr/lib/libsovtoken.so
        Optional. (Default: chaossovtoken.common.DEFAULT_LIBSOVTOKEN_PLUGIN_PATH)
    :type plugin_path: str
    :param plugin_initializer: The initializer function/method to call while
        loading the plugin.
        Optional. (Default: chaossovtoken.common.DEFAULT_LIBSOVTOKEN_PLUGIN_INITIALIZER)
    :type plugin_initializer: str
    :param timeout: How long indy-cli can take to perform the operation before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_LEDGER_TRANSACTION_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """
    output_dir = get_chaos_temp_dir()
    succeeded = False
    operation = "mint via CLI/SDK"
    details = {
        "mint_strategy": mint_strategy
    }
    if mint_strategy == SovtokenStrategy.CLI.value:
        # "mint" indy-node service
        succeeded = mint_from_cli(genesis_file, sovatoms, did=did, trustee_seed=seed,
                                  payment_address=payment_address,
                                  payment_address_seed=payment_address_seed,
                                  wallet_name=wallet_name,
                                  wallet_key=wallet_key, pool=pool,
                                  plugin_path=plugin_path,
                                  plugin_initializer=plugin_initializer,
                                  timeout=timeout,
                                  ssh_config_file=ssh_config_file)
        operation = "Mint via CLI"
    elif mint_strategy == SovtokenStrategy.SDK.value:
        operation = "Mint via SDK"
        message = """%s strategy is not yet implemented."""
        logger.error(message, operation)
        return False
    else:
        message = """Mint strategy %s not supported or not found. The following
                     operation(s) is(are) supported: %s"""
        logger.error(message, mint_strategy, operation)
        return False
    if not succeeded:
        message = """Failed to %s"""
        logger.error(message, operation)
        return False
    return True
