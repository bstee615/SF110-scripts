#!/bin/bash

project="$1"
class="$2"

project_dir="$(dirname $0)/$project"

cd $project_dir
# TODO: add a string property "traced.class" implement an ant target which copies, but:
# 1. Waits for the tracer
# 2. Traces only the class assigned by the property traced.class. The glob should be "**/${class}_ESTest.java".
ant evosuite-trace -Dtraced.class="$class"
