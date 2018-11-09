import string

import pytest
from chaossovtoken.common.cli.batch_builder import BatchBuilder


def test_can_build():
    empty = BatchBuilder().build()
    print(empty)
    assert "exit" in empty


def test_add_command():
    builder = BatchBuilder()
    assert builder is not None

    cmd_to_add = "ledger add_nym"

    builder.add_command(cmd_to_add)

    assert cmd_to_add in builder.build()

    builder = BatchBuilder()
    assert builder is not None

    cmd_to_add = "ledger add_nym"
    builder.add_command(cmd_to_add)
    builder.add_command(cmd_to_add)

    assert (cmd_to_add + cmd_to_add).translate(str.maketrans('', '', string.whitespace)) in \
           builder.build().translate(str.maketrans('', '', string.whitespace))


def test_add_command_in_seq():
    builder = BatchBuilder()
    assert builder is not None

    cmd_to_add = "ledger add_nym"

    builder.add_command(cmd_to_add)

    assert cmd_to_add in builder.build()

    builder = BatchBuilder()
    assert builder is not None

    cmd_to_add = "ledger add_nym"

    batch_str = builder.add_command(cmd_to_add).add_command(cmd_to_add).build()

    assert (cmd_to_add + cmd_to_add).translate(str.maketrans('', '', string.whitespace)) in \
           batch_str.translate(str.maketrans('', '', string.whitespace))


def test_trim_add_command():
    builder = BatchBuilder()
    assert builder is not None

    cmd_to_add = "              ledger add_nym          "

    builder.add_command(cmd_to_add)

    assert cmd_to_add.strip() in builder.build()