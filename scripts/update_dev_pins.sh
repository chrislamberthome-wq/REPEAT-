#!/bin/bash

# update_dev_pins.sh makes requirements-dev.txt up-to-date based on setup.cfg

echo "Regenerating requirements-dev.txt..."

# Check if pip-tools is installed
if ! command -v pip-compile &> /dev/null
then
    echo "pip-compile could not be found. Install pip-tools first."
    exit
fi

# Compile the requirements-dev.txt file
pip-compile --extra dev setup.cfg --output-file requirements-dev.txt

# Verify if the file has been updated successfully
if [ $? -eq 0 ]; then
    echo "requirements-dev.txt has been updated."
else
    echo "An error occurred while updating the requirements-dev.txt."
    exit 1
fi