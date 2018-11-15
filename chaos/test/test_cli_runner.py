import os

import pytest
from chaossovtoken.common.cli.cli_runner import CliRunner


def test_has_default_cli_cmd_name(tmpdir):
    runner = CliRunner(tmpdir.strpath)
    assert runner.cli_cmd_name is not None


def test_output_dir(tmpdir):
    runner = CliRunner(tmpdir.strpath)
    assert runner.output_dir is not None


def test_run_cli(tmpdir):
    runner = CliRunner(tmpdir.strpath, cli_cmd_name="cat")
    output = runner.run("foo")
    assert output is not None
    assert b"foo" == output.std_out


def test_create_batch_file_name(tmpdir):
    name = CliRunner(tmpdir.strpath)._create_batch_file_name()
    assert name is not None


def test_find_available_batch_name(tmpdir):
    name = CliRunner(tmpdir.strpath)._find_available_batch_name("foo")
    assert "foo" == name

    with open(os.path.join(tmpdir.strpath, "foo"), 'w') as f:
        f.write("foo")

    name = CliRunner(tmpdir.strpath)._find_available_batch_name("foo")
    assert "foo" != name
    assert "foo-01" == name

    with open(os.path.join(tmpdir.strpath, "foo-01"), 'w') as f:
        f.write("foo-01")

    name = CliRunner(tmpdir.strpath)._find_available_batch_name("foo")
    assert "foo" != name
    assert "foo-02" == name


@pytest.mark.skip("TODO!")
def test_bad_output_dir():
    """
        Test for negative edge cases with regards to output_dir

        folder don't exist
        given None
        unwritable
    """
    pass
