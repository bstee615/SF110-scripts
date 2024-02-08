import json
import re

with open("results.jsonl") as f:
    for line in f:
        data = json.loads(line)
        seen = set()
        unique_summary_lines = []
        for l in data["run-test"].splitlines():
            if "Tests run:" in l:
                if l not in seen:
                    seen.add(l)
                    unique_summary_lines.append(l)
        tests_run = sum(int(re.search(r"Tests run: (\d+)", l).group(1)) for l in unique_summary_lines)
        tests_failed = sum(int(re.search(r"Failures: (\d+)", l).group(1)) for l in unique_summary_lines)
        tests_errored = sum(int(re.search(r"Errors: (\d+)", l).group(1)) for l in unique_summary_lines)
        tests_skipped = sum(int(re.search(r"Skipped: (\d+)", l).group(1)) for l in unique_summary_lines)
        tests_succeeded = tests_run - tests_failed - tests_errored - tests_skipped
        print(data["program"], tests_run, tests_errored)
