from pathlib import Path
import subprocess
import json
import shutil
import traceback
import pandas as pd
import tqdm
from multiprocessing import Pool

with open("classes.txt") as f:
    classes = [tuple(l.strip().split()) for l in f.readlines()]
build_dir = Path(".").absolute()
df = pd.DataFrame(classes, columns=["program", "class"])
df["program_no"] = df["program"].str.split("_").str[0].astype(int)
df = df.sort_values(["program_no", "class"])
print("Loaded manifest:")
print(df)


def process_one_project(t):
    _, group = t
    output = {}
    output["program"] = program = group["program"].iloc[0]
    cwd = build_dir/program
    def run_command(command, timeout=None):
        proc = subprocess.run(command, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", timeout=timeout)
        return {
            "command": command,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    try:
        test_dir = cwd/"evosuite-tests"
        if test_dir.exists():
            shutil.rmtree(cwd/"evosuite-tests")
        output["clean"] = run_command("ant clean")

        output["compile"] = run_command("ant compile")
        if output['compile']['returncode']:
            raise Exception(f"Process {output['compile']['command']} exited with error code: {output['compile']['returncode']}")

        output["generate"] = {classname: None for classname in group["class"]}
        for classname in group["class"].head(10): # to limit execution time, limit to first 10 classes alphabetically
            output["generate"][classname] = run_command(f"java -jar ../lib/evosuite-1.0.6.jar -Dglobal_timeout 30 -class {classname}")

        output["compile-test"] = run_command("ant compile-tests")
        if output['compile-test']['returncode']:
            raise Exception(f"Process {output['compile-test']['command']} exited with error code: {output['compile-test']['returncode']}")

        output["run-test"] = run_command("ant evosuite-test")
        if output['run-test']['returncode']:
            raise Exception(f"Process {output['run-test']['command']} exited with error code: {output['run-test']['returncode']}")
    except Exception as ex:
        output["error"] = {
            "message": str(ex),
            "stacktrace": traceback.format_exc(),
        }
    return output

with open("results.jsonl", "w") as f, Pool(6) as pool:
    g = df.groupby("program")
    for output in tqdm.tqdm(pool.imap_unordered(process_one_project, g), total=len(g), desc="Processing repos"):
        print(json.dumps(output), file=f, flush=True)
