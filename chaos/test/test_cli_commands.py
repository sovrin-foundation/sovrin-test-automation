from chaossovtoken.common.cli.batch_builder import BatchBuilder
from chaossovtoken.common.cli.commands import cmd_open_wallet, cmd_open_pool_and_wallet

from chaossovtoken.common.cli.commands import _add_parameter


def test_add_parameter():
    rtn = _add_parameter("", "key", "value")
    assert rtn == " key=\"value\""

    assert _add_parameter("", "D", "V", check_bool=False)


def test_open_wallet():
    builder = BatchBuilder()
    with cmd_open_wallet(builder, "foo"):
        assert "CLOSING" not in builder.build()

    assert "CLOSING" in builder.build()


def test_open_pool_and_wallet():
    builder = BatchBuilder()
    with cmd_open_pool_and_wallet(builder, "foo", "bar"):
        builder.add_command("cmd")

    # print(builder.build())