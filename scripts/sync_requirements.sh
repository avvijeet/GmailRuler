#!/bin/bash

# Remove comments and empty lines from requirements.txt and generate requirements.in
grep -v '^[[:space:]]*#.*$' requirements.txt | grep -v '^[[:space:]]*$' | cut -d = -f 1 >requirements.in

# Upgrade pip to the latest version
pip install --upgrade pip

# Install pip-tools for managing dependencies
pip install pip-tools

# Compile dependencies from requirements.in to requirements.txt using pip-compile with backtracking resolver
#   --generate-hashes               Generate pip 8 style hashes in the resulting requirements file.
pip-compile requirements.in -o requirements.txt --resolver backtracking --strip-extras --no-allow-unsafe --pre --verbose --color

# Uninstall pip-tools to avoid potential conflicts
pip uninstall pip-tools -y

# Clean up generated requirements.in file
rm requirements.in
