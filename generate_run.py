from pathlib import Path
import subprocess
import json
import shutil
import traceback
import pandas as pd
import tqdm
from multiprocessing import Pool
from functools import partial
import argparse

def process_one_project(t, args):
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
        classes = group["class"]
        if args.max_classes_per_project:
            classes = classes.head(args.max_classes_per_project)
        for classname in classes: # to limit execution time, limit to first 10 classes alphabetically
            output["generate"][classname] = run_command(f"java -jar ../lib/evosuite-1.0.6.jar -Dglobal_timeout {args.test_generation_timeout} -class {classname}")

        output["compile-test"] = run_command("ant compile-evosuite")
        if output['compile-test']['returncode']:
            raise Exception(f"Process {output['compile-test']['command']} exited with error code: {output['compile-test']['returncode']}")

        output["run-test"] = run_command("ant evosuite-test", timeout=args.test_run_timeout)
        if output['run-test']['returncode']:
            raise Exception(f"Process {output['run-test']['command']} exited with error code: {output['run-test']['returncode']}")
    except Exception as ex:
        output["error"] = {
            "message": str(ex),
            "stacktrace": traceback.format_exc(),
        }
    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_generation_timeout", type=int, default=60*2,
                        help="Maximum number of seconds to allow EvoSuite for test generation.")
    parser.add_argument("--test_run_timeout", type=int, default=60*3,
                        help="Maximum number of seconds to allow EvoSuite for test generation.")
    parser.add_argument("--max_projects", type=int,
                        help="Maximum number of projects to process (sorted by ID ascending)")
    parser.add_argument("--max_classes_per_project", type=int,
                        help="Maximum number of classes to generate tests for per project (sorted lexicographically)")
    parser.add_argument("--nproc", type=int,
                        help="Number of processes to run in parallel")
    args = parser.parse_args()

    # Load manifest of programs and classes
    with open("classes.txt") as f:
        classes = [tuple(l.strip().split()) for l in f.readlines()]
    build_dir = Path(".").absolute()
    df = pd.DataFrame(classes, columns=["program", "class"])
    df["program_no"] = df["program"].str.split("_").str[0].astype(int)
    df = df.sort_values(["program_no", "class"])
    if args.max_projects:
        df = df.head(args.max_projects)
    print("Loaded manifest:")
    print(df)

    # Generate/run tests and write results to file
    with open("results.jsonl", "w") as f, Pool(args.nproc) as pool:
        g = df.groupby("program")
        it = pool.imap_unordered(partial(process_one_project, args=args), g)
        for output in tqdm.tqdm(it, total=len(g), desc="Processing repos"):
            print(json.dumps(output), file=f, flush=True)
