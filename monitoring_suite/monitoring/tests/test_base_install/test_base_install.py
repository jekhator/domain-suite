"""Base install: the package imports and works in a venv without logging-suite."""

import pathlib
import subprocess
import venv

import monitoring_suite

PROBE = """
import importlib
import importlib.util
import pkgutil

assert importlib.util.find_spec("logging_suite") is None, "logging-suite present"

import monitoring_suite

failures = []
imported = 0
for module in pkgutil.walk_packages(monitoring_suite.__path__, "monitoring_suite."):
    parts = module.name.split(".")
    if "tests" in parts or parts[-1] == "conftest":
        continue
    try:
        importlib.import_module(module.name)
        imported += 1
    except Exception as error:
        failures.append(f"{module.name}: {type(error).__name__}: {error}")

assert not failures, failures
assert imported > 50, imported

from monitoring_suite.aspects import Monitored, aspects
from monitoring_suite.monitoring import CollectingSink, monitored

sink = CollectingSink()


@monitored(event="base.install", sink=sink)
def work() -> str:
    return "done"


assert work() == "done"
assert sink.events[0].labels == (), sink.events[0].labels


@aspects(Monitored(event="base.aspect", sink=sink))
def aspect_work() -> str:
    return "done"


assert aspect_work() == "done"
assert sink.events[1].labels == (), sink.events[1].labels
print("BASE-INSTALL-OK", imported)
"""


class TestBaseInstall:
    """The documented base install (no extras) imports every subpackage."""

    def test_imports_without_logging_suite(self, tmp_path: pathlib.Path) -> None:
        """A venv lacking logging-suite imports every module and emits metrics."""
        env_dir = tmp_path / "base-venv"
        venv.create(env_dir, with_pip=False, symlinks=True)
        python = env_dir / "bin" / "python"
        source_root = pathlib.Path(monitoring_suite.__file__).resolve().parents[1]
        site_packages = subprocess.run(
            [
                str(python),
                "-I",
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        (pathlib.Path(site_packages) / "monitoring_suite_source.pth").write_text(
            f"{source_root}\n"
        )

        result = subprocess.run(
            [str(python), "-I", "-c", PROBE],
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "BASE-INSTALL-OK" in result.stdout
