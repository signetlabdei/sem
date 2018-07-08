import sem
from click.testing import CliRunner


def test_cli():
    runner = CliRunner()
    result = runner.invoke(sem)
    print(result.output)
    assert result.exit_code == 0
