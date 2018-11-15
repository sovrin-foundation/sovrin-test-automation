"""
Common operations for CLI strategy
"""
from chaosindy.common import get_indy_cli_command_output
from chaosindy.common.cli import *
from chaosindy.common.cli.batch_builder import BatchBuilder
from chaosindy.common.cli.cli_runner import CliRunner
from chaosindy.common.cli.commands import cmd_open_wallet, \
    cmd_open_pool_and_wallet, cmd_create_local_did, cmd_create_ledger_did, \
    cmd_use_did, cmd_load_plugin, cmd_create_payment_address
from chaosindy.common.cli.operations import batch_execution_failed, \
    BatchExecutionFailedException
from logzero import logger

from typing import List, Dict, Union

def cli_transfer_sovatoms(output_dir: str,
                          inputs: Dict[str,Union[str,List[str]]],
                          outputs: List[str],
                          sovatoms: Union[int,str],
                          change_payment_address: str,
                          payment_lib: str,
                          payment_lib_initializer: str,
                          pool_name: str,
                          wallet_name: str,
                          wallet_key: str=None,
                          payment_method: str='null'
                         ) -> bool:

    """
    Builds batch and runs batch on Indy CLI to get list of payment sources from
    a list of payment addresses.
    :param output_dir: str
    :param inputs: Dict[str,Union[str,List[str]]],
    :param outputs: List[str]
    :param sovatoms: Union[int,str]
    :param change_payment_address: str
    :payment_lib: str
    :payment_lib_initializer: str
    :param pool_name: str
    :param wallet_name: str
    :param wallet_key: str=None
    :payment_method: str="null"
    :return: bool
    """
    logger.info("Transferring %s sovatoms to %d addresses", sovatoms,
        len(outputs))

    # Open the pool and wallet
    batch = BatchBuilder()
    with cmd_open_pool_and_wallet(batch,
                                  pool_name,
                                  wallet_name,
                                  wallet_key=wallet_key):
        cmd_load_plugin(batch, payment_lib, payment_lib_initializer)
        payment_command = "ledger payment inputs={} outputs=".format(
            ",".join(inputs['txos']))
        separator = ""
        for to_payment_address in outputs:
            to_payment_address = ensure_address_format("pay:{}:".format(
                payment_method), to_payment_address)
            payment_command += "{}({},{})".format(separator,
                to_payment_address, sovatoms)
            separator = ","
        if(inputs['change'] > 0):
            change_payment_address = ensure_address_format("pay:{}:".format(
                payment_method), change_payment_address)
            payment_command += ",({},{})".format(
                change_payment_address, inputs['change'])
        payment_command += "\n"
        batch.add_command(payment_command)

    batch_str = batch.build()

    std_out = CliRunner(output_dir).run(batch_str,
        "indy-cli-ledger-transfer-sovatoms").std_out

    if batch_execution_failed(std_out):
        raise BatchExecutionFailedException
    return True

