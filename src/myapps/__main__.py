"""Entry point for `python -m myapps`."""

import sys


def _check_imports(argv: list[str]) -> int:
    """`--check-imports <names-file> <report-file>`: tries to import every
    module listed (one per line) in names-file, writes a JSON report of the
    ones that failed to report-file, and exits without starting the GUI.

    Used by packaging/pyinstaller/check_stdlib_bundle.py to prove that a
    frozen build can import the same standard-library modules a source run
    can - i.e. that what plugins rely on is really bundled. The report goes
    to a file, not stdout: a windowed frozen build (console=False) has no
    stdout/stderr at all on Windows.
    """
    import importlib
    import json

    names_file, report_file = argv
    with open(names_file, encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip()]
    failed: dict[str, str] = {}
    for name in names:
        try:
            importlib.import_module(name)
        except BaseException as exc:  # noqa: BLE001 - SystemExit included: record, never abort
            failed[name] = f"{type(exc).__name__}: {exc}"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump({"checked": len(names), "failed": failed}, f, indent=2, sort_keys=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--check-imports":
        sys.exit(_check_imports(sys.argv[2:]))

    from myapps.app import main

    sys.exit(main())
