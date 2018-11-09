import os
import json
import random
import subprocess
import time
from chaosindy.common import *
from chaosindy.common.cli import *
from chaosindy.common.cli.operations import cli_get_payment_addresses, \
    cli_generate_payment_addresses, BatchExecutionFailedException, \
    cli_get_payment_sources, cli_create_pool, cli_create_wallet
from chaosindy.execute.execute import FabricExecutor, ParallelFabricExecutor
from chaossovtoken.common import *
from chaossovtoken.common.cli import *
from chaossovtoken.common.cli.operations import cli_transfer_sovatoms
from logzero import logger
from multiprocessing import Pool
from os.path import expanduser, join
from typing import Union, List, Dict

# TODO: Modify to allow more than one wallet? One wallet per Trustee?
def transfer_from_cli(genesis_file: str, sovatoms: Union[int,str],
    transfers: int,
    from_payment_addresses: str = None,
    excluded_from_payment_addresses: str = None,
    to_payment_addresses: str = None,
    generate_to_payment_addresses: Union[str,int] = 0,
    change_payment_address: str = DEFAULT_CHAOS_PAYMENT_ADDRESS1,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    plugin_path: str = DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_PATH,
    plugin_initializer: str = DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_INITIALIZER,
    timeout: Union[str,int] = DEFAULT_CHAOS_LEDGER_TRANSACTION_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Transfer sovatoms into a payment address

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param sovatoms: The number of sovatoms to transfer
    :type sovatoms: Union[int,str]
    :param transfers: How many times to transfer sovatoms from the
        from_payment_addresses to the to_payment_addresses.
    :type transfers : Union[int,str]
    :param from_payment_addresses: A comma separated list of payment addresses
        from which to get payment sources. All txos will be gathered from all
        "from payment addresses". When from_payment_addresses is blank or
        set to None, all payment sources available in the given wallet will be
        used. Payment addresses can be excluded from the list of
        from_payment_addresses using the excluded_from_payment_addresses kwarg
        Optional. (Default: None)
    :type from_payment_addresses: str
    :param excluded_from_payment_addresses: A comma separated list of payment
        addresses to filter out of from_payment_addresses.
        Optional. (Default: None)
    :type excluded_from_payment_addresses: str
    :param to_payment_addresses: A comma separated list of the payment addresses
        to which to send payment. Each address will get the given number of
        sovatoms.
        Optional. (Default: None)
    :type to_payment_addresses: str
    :param generate_to_payment_addresses: How many random payment addresses
        should be generated and appended to the to_payment_addresses list?
        Each address will get the given number of sovatoms.
        Optional. (Default: 0)
    :type generate_to_payment_addresses: Union[str,int]
    :param change_payment_addresses: The payment address to which change should
        be transfered
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_PAYMENT_ADDRESS1)
    :type change_payment_addresses: str
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

    # Convert a comma separated list into a python list
    # Default to an empty list if None
    if from_payment_addresses:
        from_payment_addresses = from_payment_addresses.split(",")
    else:
        # Deriving payment addresses from the list of addressed in the wallet
        logger.debug("Deriving \"from payment addresses\" from the %s wallet.",
                     wallet_name)
        try:
            from_payment_addresses = cli_get_payment_addresses(output_dir,
                wallet_name, wallet_key, payment_method="sov") 
        except BatchExecutionFailedException:
            logger.error("Failed to derive \"from payment addresses\" from " \
                         "the %s wallet.", wallet_name)
            return False
        
    if excluded_from_payment_addresses:
        # Filter all excluded_from_payment_addresses from from_payment_addresses
        from_payment_addresses = [
            x for x in from_payment_addresses if x not in excluded_from_payment_addresses
        ]

    # Generate payment addresses?
    # Convert a comma separated list into a python list
    # Default to an empty list if None
    if to_payment_addresses:
        to_payment_addresses = to_payment_addresses.split(",")
    else:
        to_payment_addresses = []

    # Append randomly generated addresses to the to_payment_address list?
    if int(generate_to_payment_addresses) > 0:
        logger.debug("Generating %s randomly generated payment addresses",
            generate_to_payment_addresses)
        try:
            to_payment_addresses.extend(
                cli_generate_payment_addresses(output_dir,
                    plugin_path, plugin_initializer, wallet_name,
                    wallet_key=wallet_key, payment_method="sov",
                    number_of_addresses=generate_to_payment_addresses))
        except BatchExecutionFailedException:
            logger.error("Failed to generate %s randomly generated payment " \
                         "addresses", generate_to_payment_addresses)
            return False

    # IMPORTANT! - Many of the following operations could theoretically
    #              be combined into one operation. However, Indy CLI bails out
    #              on the first command that fails. "Already exists" failures
    #              are okay... Therefore, any operations that can fail should be
    #              executed in their own batch file.

    # Transfer sovatoms a given number of times
    for i in range(1,int(transfers) + 1):
        logger.debug("Processing %i of %s transfers", i, transfers)

        try:
            ledger_get_payment_sources = cli_get_payment_sources(
                output_dir,
                from_payment_addresses,
                plugin_path,
                plugin_initializer,
                pool,
                wallet_name,
                wallet_key=wallet_key,
                payment_method="sov")
        except BatchExecutionFailedException:
            logger.error("Failed to get \"payment sources\" from the %s"\
                         " wallet.", wallet_name)
            return False

        inputs = get_sufficient_txos(ledger_get_payment_sources,
            int(sovatoms) * len(to_payment_addresses))

    
        # Transfer sovatoms
        # Note: Do not cheat and use the txo in the receipt. Rather loop
        #       and get payment sources again.
        try:
            cli_transfer_sovatoms(output_dir,
                                  inputs,
                                  to_payment_addresses,
                                  sovatoms,
                                  change_payment_address,
                                  plugin_path,
                                  plugin_initializer,
                                  pool,
                                  wallet_name,
                                  wallet_key=wallet_key,
                                  payment_method="sov")
        except BatchExecutionFailedException:
            logger.error("Failed to transfer sovatoms. Inputs = {} outputs = " \
                         "{} sovatoms = {} wallet_name = {} wallet_key = {} " \
                         "pool = {}".format(inputs, to_payment_addresses,
                         sovatoms, wallet_name, wallet_key, pool))
            return False
    return True

def transfer_by_strategy(genesis_file: str, sovatoms: Union[int,str],
    transfer_strategy: int, transfers: int = 1, 
    from_payment_addresses: str = None,
    excluded_from_payment_addresses: str = None,
    to_payment_addresses: str = None,
    generate_to_payment_addresses: Union[str,int] = 0,
    change_payment_address: str = DEFAULT_CHAOS_PAYMENT_ADDRESS1,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    plugin_path: str = DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_PATH,
    plugin_initializer: str = DEFAULT_CHAOS_LIBSOVTOKEN_PLUGIN_INITIALIZER,
    timeout: Union[str,int] = DEFAULT_CHAOS_LEDGER_TRANSACTION_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Transfer sovatoms into a payment address

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param sovatoms: The number of sovatoms to transfer
    :type sovatoms: Union[int,str]
    :param transfers: How many times to transfer sovatoms from the
        from_payment_addresses to the to_payment_addresses.
    :type transfers : Union[int,str]
    :param transfer_strategy: A transfer strategy defined by the
        chaossovtoken.common.SovtokenStrategy enum. Examples include:
        SovtokenStrategy.CLI
        SovtokenStrategy.SDK - Not Yet Implemented (NYI)
    :type transfer_strategy: int
    :param from_payment_addresses: A comma separated list of payment addresses
        from which to get payment sources. All txos will be gathered from all
        "from payment addresses". When from_payment_addresses is blank or
        set to None, all payment sources available in the given wallet will be
        used. Payment addresses can be excluded from the list of
        from_payment_addresses using the excluded_from_payment_addresses kwarg
        Optional. (Default: None)
    :type from_payment_addresses: str
    :param excluded_from_payment_addresses: A comma separated list of payment
        addresses to filter out of from_payment_addresses.
        Optional. (Default: None)
    :type excluded_from_payment_addresses: str
    :param to_payment_addresses: The payment addresses to which to send payment.
        Each address will get the given number of sovatoms.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_PAYMENT_ADDRESS2)
    :type to_payment_addresses: str
    :param generate_to_payment_addresses: How many random payment addresses
        should be generated and appended to the to_payment_addresses list?
        Each address will get the given number of sovatoms.
        Optional. (Default: 0)
    :type generate_to_payment_addresses: Union[str,int]
    :param change_payment_addresses: The payment address to which change should
        be transfered
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_PAYMENT_ADDRESS1)
    :type change_payment_addresses: str
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
    operation = "transfer via CLI/SDK"
    details = {
        "transfer_strategy": transfer_strategy
    }
    # Note: Currently sending from and to the same number of addresses
    #       (generate_to_payment_addresses).
    operation_desc = "Transfer {} sovatoms from {} txos to {} payment " \
                     "address(es)".format(sovatoms,
                         generate_to_payment_addresses,
                         generate_to_payment_addresses)
    if transfer_strategy == SovtokenStrategy.CLI.value:
        # "transfer" indy-node service
        succeeded = transfer_from_cli(
            genesis_file,
            sovatoms,
            transfers=transfers,
            from_payment_addresses=from_payment_addresses,
            excluded_from_payment_addresses=excluded_from_payment_addresses,
            to_payment_addresses=to_payment_addresses,
            generate_to_payment_addresses=generate_to_payment_addresses,
            change_payment_address=change_payment_address,
            wallet_name=wallet_name,
            wallet_key=wallet_key,
            pool=pool,
            plugin_path=plugin_path,
            plugin_initializer=plugin_initializer,
            timeout=timeout,
            ssh_config_file=ssh_config_file)
        operation = "{} via CLI".format(operation_desc)
    elif transfer_strategy == SovtokenStrategy.SDK.value:
        operation = "{} via SDK".format(operation_desc)
        message = """%s strategy is not yet implemented."""
        logger.error(message, operation)
        return False
    else:
        message = """Transfer strategy %s not supported or not found. The
                     following operation(s) is(are) supported: %s"""
        logger.error(message, transfer_strategy, operation)
        return False
    if not succeeded:
        message = """Failed to %s"""
        logger.error(message, operation)
        return False
    return True
