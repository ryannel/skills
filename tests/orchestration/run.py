"""Runs the orchestration tests in several processes at once.

    python3 tests/orchestration/run.py                      # every test, in min(8, CPU count) processes
    python3 tests/orchestration/run.py -j 4                 # in 4 processes
    python3 tests/orchestration/run.py test_agent_loop.FirstRuns test_names

Each process runs its share of the tests one at a time, as `python3 -m unittest discover tests/orchestration`
would, and that command still runs them all in one process. The runner splits the suite by test rather than by
class, longest first into the process with the least work, using the times the last run measured. It keeps them
in .timings.json beside this file, which git ignores; without it, it deals the tests out in turn.

It prints the report of every test that failed and exits 1 if any did. It uses the standard library only."""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TIMINGS = HERE / ".timings.json"


def tests_in(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from tests_in(test)
        else:
            yield test


def load(names):
    """The ids of the tests named, or of every test, the saved repositories each starts from (see
    support.shares), and the errors met loading them."""
    loader = unittest.TestLoader()
    if names:
        prefix = "tests.orchestration."
        suite = unittest.TestSuite(loader.loadTestsFromName(n[len(prefix):] if n.startswith(prefix) else n)
                                   for n in names)
    else:
        suite = loader.discover(str(HERE), top_level_dir=str(HERE))
    tests = list(tests_in(suite))
    starts = {t.id(): getattr(getattr(t, getattr(t, "_testMethodName", ""), None), "shares", ()) for t in tests}
    return [t.id() for t in tests], starts, loader.errors


def split(ids, n, times, starts=None):
    """The ids in n shares of about equal time, keeping together the tests that start from the same saved
    repository. With no recorded times, dealt out in turn."""
    groups, by_name = [], {}
    for i in ids:
        names = (starts or {}).get(i) or ()
        group = next((by_name[x] for x in names if x in by_name), None)
        if group is None:
            group = []
            groups.append(group)
        group.append(i)
        for x in names:
            by_name.setdefault(x, group)
    shares = [[0.0, []] for _ in range(min(n, len(groups)) or 1)]
    known = [times[i] for i in ids if i in times]
    usual = sorted(known)[len(known) // 2] if known else 1.0
    order = groups if not known else sorted(groups, key=lambda g: -sum(times.get(i, usual) for i in g))
    for k, group in enumerate(order):
        share = shares[k % len(shares)] if not known else min(shares, key=lambda s: s[0])
        share[0] += sum(times.get(i, usual) for i in group)
        share[1] += group
    return [s[1] for s in shares]


class Timed(unittest.TextTestResult):
    """A result that keeps how long each test took."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.times = {}

    def startTest(self, test):
        self._started = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        super().stopTest(test)
        self.times[test.id()] = round(time.perf_counter() - self._started, 3)


def worker(ids_path, out_path):
    """Runs the ids in ids_path, one at a time, and writes what happened to out_path."""
    sys.path.insert(0, str(HERE))
    ids = json.loads(Path(ids_path).read_text())
    log = open(out_path + ".log", "w")
    runner = unittest.TextTestRunner(stream=log, verbosity=0, resultclass=Timed)
    result = runner.run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(i) for i in ids))
    report = {"ran": result.testsRun, "times": result.times, "skipped": len(result.skipped),
              "failed": [[str(t), text] for t, text in result.failures + result.errors],
              "unexpected": [str(t) for t in result.unexpectedSuccesses]}
    Path(out_path).write_text(json.dumps(report))
    return 0 if result.wasSuccessful() else 1


def main():
    parser = argparse.ArgumentParser(description="Runs the orchestration tests in several processes at once.")
    parser.add_argument("names", nargs="*", help="test modules, classes or tests, as unittest names them")
    parser.add_argument("-j", type=int, default=min(8, os.cpu_count() or 1), help="how many processes")
    parser.add_argument("--worker", nargs=2, metavar=("IDS", "OUT"), help=argparse.SUPPRESS)
    a = parser.parse_args()
    if a.worker:
        return worker(*a.worker)
    started = time.time()
    ids, starts, errors = load(a.names)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    try:
        times = json.loads(TIMINGS.read_text())
    except (OSError, ValueError):
        times = {}
    shares = split(ids, max(1, a.j), times, starts)
    with tempfile.TemporaryDirectory(prefix="orchestrate-run-") as tmp:
        procs = []
        for k, share in enumerate(shares):
            ids_path, out_path = f"{tmp}/ids{k}.json", f"{tmp}/out{k}.json"
            Path(ids_path).write_text(json.dumps(share))
            with open(out_path + ".err", "w") as err:  # what the script prints, such as its warnings
                procs.append((subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--worker", ids_path,
                                                out_path], stdin=subprocess.DEVNULL, stdout=err, stderr=err),
                              out_path))
        reports, crashed = [], []
        for proc, out_path in procs:
            proc.wait()
            try:
                reports.append(json.loads(Path(out_path).read_text()))
            except (OSError, ValueError):
                crashed.append("".join(Path(out_path + end).read_text() for end in (".log", ".err")
                                       if Path(out_path + end).exists())[-20000:])
    for report in reports:
        times.update(report["times"])
    try:
        TIMINGS.write_text(json.dumps(times, indent=0, sort_keys=True))
    except OSError:
        pass
    failed = [f for r in reports for f in r["failed"]] + [[f"{t} (unexpected success)", ""]
                                                          for r in reports for t in r["unexpected"]]
    for name, text in failed:
        print("=" * 70 + f"\nFAIL: {name}\n" + "-" * 70 + f"\n{text}", file=sys.stderr)
    for text in crashed:
        print("=" * 70 + "\nA test process stopped without a report:\n" + text, file=sys.stderr)
    ran = sum(r["ran"] for r in reports)
    work = sum(sum(r["times"].values()) for r in reports)
    skipped = sum(r["skipped"] for r in reports)
    print(f"Ran {ran} tests in {len(shares)} processes in {time.time() - started:.1f} s "
          f"({work:.1f} s of test time){f', {skipped} skipped' if skipped else ''}: "
          + (f"{len(failed)} failed" if failed else "OK" if not crashed else f"{len(crashed)} processes crashed"))
    return 1 if failed or crashed or ran != len(ids) else 0


if __name__ == "__main__":
    sys.exit(main())
