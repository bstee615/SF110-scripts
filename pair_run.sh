#!/bin/bash

# Run container disconnected
image_name="benjijang/sf110:latest"
project="$1"
class="$2"
container_name="pair_${project}_${class}"

docker run -itd --name $container_name $image_name

# Run unit test
docker exec -it $container_name bash /workspace/pair_test.sh $project $class

# Run tracer
docker exec -it $container_name bash /workspace/pair_trace.sh

# Both processes will wait on a timeout until both are initialized.
# Once each process initializes (expect to take only a few seconds), tracer will connect on port 8787.
# Tracing will start and conclude automatically.
