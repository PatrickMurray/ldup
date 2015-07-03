# LDUP: List Duplicates

A command line utility to find and list duplicate files all while minimizing memory usage, disk reads, and hash operations when possible.

## Setup

One may install the utility by simply running the included setup script.

`sudo ./setup.sh`

## Usage

The utility accepts four optional arguments:

- `-h, --help`: shows a help message and exits
- `-r, --recursive`: traverses subdirectories
- `--hidden`: includes hidden files and directories
- `--json`: outputs the final JSON results

These optional arguments may be followed by an arbitrary number of directories that the user would like to evaluate. By default, if no directories are provided, the user's current working directory will be examined.

### Examples

`ldup` or `ldup .`

Evaluates all non-hidden files in the user's current directory without branching down to subdirectories.

`ldup -r`

Evaluates all non-hidden files in the user's current directory and subdirectories.

`ldup -r --hidden ~`

Examines the user's home directory and all subsequent subdirectories, regardless of whether any directories or files are intend to be hidden.# ldup
