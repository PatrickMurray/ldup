#! /usr/bin/env python3


#  
#   /$$       /$$
#  | $$      | $$
#  | $$  /$$$$$$$ /$$   /$$  /$$$$$$
#  | $$ /$$__  $$| $$  | $$ /$$__  $$
#  | $$| $$  | $$| $$  | $$| $$  \ $$
#  | $$| $$  | $$| $$  | $$| $$  | $$
#  | $$|  $$$$$$$|  $$$$$$/| $$$$$$$/
#  |__/ \_______/ \______/ | $$____/
#                          | $$
#                          | $$
#                          |__/
#  


from argparse import ArgumentParser
import io, os, json, hashlib


def main():
	arguments = get_arguments()
	directories = transform_directories(arguments.directories)
	filenames = get_filenames(arguments, directories)
	store = collect_data(filenames)
	filter_duplicates(store)
	output(arguments, store)


def get_arguments():
	"""
	Parses system arguments for the parameters specified below to which
	the program is to follow during its runtime.
	
	System Arguments:
		ldup [-h] [-r] [---hidden] [--json] [DIRECTORIES]
	
	Parameters:
		-h, --help			displays a synopsis of the program's usage
		
		-r, --recursive		modifies traversal of the provided
							directories to include their subdirectories
		
		--hidden			changes the scope of files to include hidden
							files and files that are in hidden
							directories
		
		--json				alters the output to be valid JSON
	
	@return		object
	"""
	parser = ArgumentParser(description="Searches for and lists duplicate files contained in the DIRECTORY(ies) provided (the current directory by default).")
	parser.add_argument("-r", "--recursive", action="store_true", help="traverse subdirectories")
	parser.add_argument("--hidden", action="store_true", help="includes hidden files")
	parser.add_argument("--json", action="store_true", help="returns json of duplicate files")
	parser.add_argument("directories", metavar="DIRECTORY", nargs="*")
	return parser.parse_args()


def transform_directories(directories):
	"""
	Transforms the list of directories by replacing keywords and
	removing duplicate entries to prevent extraneous operations. By
	default, if no directory is provided by the user, their current
	directory will be examined.
	
	Example:
		Suppose that the program is being run from foo's home directory,
		and the following system arguments are provided:
		
		Input:
			directories = [".", "/home/foo", "/home/foo/Downloads"]
		
		Transformation:
			directories = ["/home/foo", "/home/foo/Downloads"]
	"""
	# Replace keywords
	keywords = {
		"." : os.getcwd()
	}
	for index, directory in enumerate(directories):
		if directory in keywords:
			directories[index] = keywords[directory]
	
	# Remove duplicates and validate that the directories exist
	transformed = []
	for directory in directories:
		if directory not in transformed and os.path.isdir(directory):
			transformed.append(directory)
	
	# If the user doesn't provide any directories
	if len(transformed) == 0:
		transformed.append(os.getcwd())
	return transformed


def get_filenames(arguments, directories):
	"""
	Gathers a list of filenames to be examined. If the recursive flag is
	thrown at runtime, subdirectories will be traversed. Dependent on
	the hidden flag being thrown, hidden files and subdirectories will
	be ignored.
	
	Example:
		Suppose the user bar runs the program from the Documents folder
		in their home directory and passes the hidden flag. Since the
		recursive flag is not given, neither the subdirectory nor the
		hidden subdirectory is traversed.
		
		Structure:
			/home/bar/Documents
				School/
					Web\ Programming/
						textbook.pdf
						notes.odt
				.Secret\ Folder/
					Tax2015.odx
				.passwords.txt
				Resume.odt
				To_Do_List.txt
		
		Output:
			filepaths = [
				"/home/bar/Documents/.passwords.txt",
				"/home/bar/Documents/Resume.odt",
				"/home/bar/Documents/To_Do_list.txt"
			]
		
	@return		list
	"""
	# If the recursive flag was thrown by the user
	if arguments.recursive:
		return get_filenames_recursive(arguments, directories)
	
	# Otherwise, gather a list of files in each directory
	filepaths = []
	for directory in directories:
		for filename in os.listdir(directory):
			filepath = os.path.join(directory, filename)
			# Ignore the file if the the hidden flag is not thrown and it is hidden
			if not arguments.hidden and is_hidden(filepath):
				continue
			# Don't allow duplicate files and verify that it is indeed a file and not a subdirectory
			if filepath not in filepaths and os.path.isfile(filepath):
				filepaths.append(filepath)
	return filepaths


def get_filenames_recursive(arguments, directories):
	"""
	Similar to get_filenames() in that it follows the provided runtime
	arguments and returns a list of files that are to be examined;
	however, this modified function walks all subdirectories and is only
	called when the recursive flag is passed.
	
	@return		list
	"""
	filepaths = []
	for directory in directories:
		for subdirectory, _, files in os.walk(directory, followlinks=False):
			for filename in files:
				filepath = os.path.join(subdirectory, filename)
				# Ignore hidden files if the flag is not thrown
				if not arguments.hidden and is_hidden(filepath):
					continue
				# Ensure the entry is not a duplicate and verify that it is a file
				if filepath not in filepaths and os.path.isfile(filepath):
					filepaths.append(filepath)
	return filepaths


def is_hidden(filename):
	"""
	Determines if a file is hidden or is in a hidden directory.
	
	Example:
		filename = "/home/bar/Documents/.Secret\ Folder/super_secret.txt"
		 => True
		
		filename = "/home/bar/Documents/.passwords.txt"
		 => True
		
		filename = "/home/bar/Documents/Resume.odt"
		 => False
	
	@return		bool
	"""
	blocks = filename.split("/")
	for block in blocks:
		if block.startswith("."):
			return True
	return False


def collect_data(filenames):
	"""
	Gathers only the minimal amount of information needed to determine
	if any of the files listed are duplicates. This is accomplished by
	postponing resource heavy operations (such as disk reads and
	hashing) when necessary; in doing so, greatly reducing the program's
	runtime and resource usage.
		
	@return		dict
	"""
	store = {}
	for filename in filenames:
		size = get_file_size(filename)
		if size not in store:
			# Store the filename in case another file of the same size
			# is discovered and they need to be hashed.
			store[size] = filename
		else:
			# If the size is already in the store, and it's value is a
			# string, it contains a filename that must now be hashed.
			if type(store[size]) == str:
				# Temporarily store the filename
				tmp = store[size]
				# Let the size now be a dictionary
				store[size] = {}
				hash = get_file_hash(tmp)
				# Store the file's hash digest in the dictionary as a
				# key and let it's value be the list of all files with
				# it's size and hash digest.
				store[size][hash] = [tmp]
			# Hash the current file
			hash = get_file_hash(filename)
			# If the hash is already in the dictionary, append the
			# filename to the list
			if hash in store[size]:
				store[size][hash].append(filename)
			else:
				# Otherwise, assign the hash as a key in the dictionary
				# and let its value be the list containing the current
				# file.
				store[size][hash] = [filename]
	return store


def get_file_size(filename):
	"""
	Returns a file's size on the disk in bytes.
	
	@return		int
	"""
	return os.stat(filename).st_size


def get_file_hash(filename):
	"""
	Computes and returns a file's hash digest.
	
	@return		str
	"""
	# Use SHA-2 256-bit
	hash_function = hashlib.sha256()
	# Use the storage's default buffer
	buffer_size = io.DEFAULT_BUFFER_SIZE
	with open(filename, "rb") as handler:
		buffer = handler.read(buffer_size)
		# While the buffer is not empty
		while len(buffer) > 0:
			# Update the hash digest
			hash_function.update(buffer)
			# Get the next buffer
			buffer = handler.read(buffer_size)
	# Return the digest as uppercase hexadecimal
	return hash_function.hexdigest().upper()


def filter_duplicates(store):
	"""
	Prepares the store for being outputted by filtering it in such a
	manner that only duplicate files remain.
	
	Non-duplicate entries:
		1.	store[size] is a strings
		2.	store[size][hash] contains only one element
	"""
	# Mark file sizes for deletion
	marked = []
	for size in store:
		# If the size's value is a string (ergo an unhashed filename),
		# mark that size for deletion.
		if type(store[size]) == str:
			marked.append(size)
	# Commit deletions
	for mark in marked:
		del store[mark]
	# Remove hash digests that only contain one filename
	marked = {}
	for size in store:
		for hash in store[size]:
			if len(store[size][hash]) <= 1:
				if size not in marked:
					marked[size] = []
				marked[size].append(hash)
	# Commit deletions
	for size in marked:
		for hash in marked[size]:
			del store[size][hash]
		if len(store[size]) >= 0:
			del store[size]


def output(arguments, store):
	"""
	Displays all duplicate files in the format specified by the user.
	"""
	# If JSON is requested
	if arguments.json:
		print(json.dumps(store, sort_keys=True, indent=2, separators=(',', ': ')))
	else:
		# Otherwise display each hash and the size of the file, followed
		# by each occurence of the duplication.
		for size in store:
			for hash in store[size]:
				print(hash, size)
				for filename in store[size][hash]:
					print("  %s" % filename)
				print()


if __name__ == "__main__":
	main()
