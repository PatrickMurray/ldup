#! /usr/bin/env bash

# Remove a previous installation if it exists
if [ -f /usr/bin/ldup ]; then
	echo "Removing previous installation..."
	rm /usr/bin/ldup
fi

# Prepare the installation
chmod +x src/ldup.py
cp src/ldup.py /usr/bin
mv /usr/bin/ldup.py /usr/bin/ldup
