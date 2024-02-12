# SF110/EvoSuite

How to run the scripts:

```bash
# Unzip SF110-20130704-src.zip and SF110-20130704.zip to this directory, don't overwrite build.xmls
# Download new versions of junit, hamcrest, and evosuite to lib/
bash download_libs.sh

# Start JDK docker container with `bash run.sh`, then enter shell with `docker exec -it sf110 bash`
# Inside docker container now...
cd /workspace
apt update -y; apt install -y ant python3 python3-pip; pip install lxml pandas
python3 format.py       # Format the XMLs (should already be formatted in this repo)
python3 fix.py          # Fix the build.xmls by adding paths to the correct libraries
python3 generate_run.py # Run EvoSuite on all programs/classes; should take a long time
python3 print_item.py   # Print the results
```
