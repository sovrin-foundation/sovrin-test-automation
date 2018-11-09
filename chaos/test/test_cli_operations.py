from chaossovtoken.common.cli.operations import _batch_execution_failed


def test_check_status():
    assert not _batch_execution_failed(b'')

    assert _batch_execution_failed(b"Batch execution failed")
