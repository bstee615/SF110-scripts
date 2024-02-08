from pathlib import Path
import os
import pandas as pd

with open("classes.txt") as f:
    classes = [tuple(l.strip().split()) for l in f.readlines()]
build_dir = Path(".").absolute()
df = pd.DataFrame(classes, columns=["program", "class"])
df = df.sort_values(["program", "class"])
print(df)

for program, g in df.groupby("program"):
    os.chdir(build_dir/program)
    print("COMPILING...")
    os.system("ant compile")
    print("GENERATING TESTS...")
    for classname in g["class"]:
        os.system(f"java -jar ../lib/evosuite-1.0.6.jar -class {classname}")
    print("COMPILING TESTS...")
    os.system("ant compile-tests")
    print("RUNNING TESTS...")
    os.system("ant evosuite-test")