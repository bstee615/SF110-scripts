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
    def run_command(command):
        proc = subprocess.run(command, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")
        return proc.stdout, proc.returncode
    try:
        test_dir = cwd/"evosuite-tests"
        if test_dir.exists():
            shutil.rmtree(cwd/"evosuite-tests")
        output["clean"] = run_command("ant clean")

        output["generate"] = {classname: False for classname in group["class"]}
        if err:
            raise Exception(f"Process exited with error code: {err}")
        for classname in group["class"]:
            output["generate"][classname], err = run_command(f"java -jar ../lib/evosuite-1.0.6.jar -class {classname}")
            if err:
                raise Exception(f"Process exited with error code: {err}")

        output["compile-test"], err = run_command("ant compile-tests")
        if err:
            raise Exception(f"Process exited with error code: {err}")

        output["run-test"], err = run_command("ant evosuite-test")
        if err:
            raise Exception(f"Process exited with error code: {err}")
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
