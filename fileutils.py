import os, errno
from fnmatch import fnmatch

"""Various utilities for interacting with files and directories."""

# Globbing Utilities {{{1
def getAll(pattern):
    """
    Get all items that match a particular glob pattern.
    Supports *, ? and [] globbing (including [!]), but does not support {}
    """
    import glob
    pattern = os.path.expanduser(pattern)
    pattern = os.path.expandvars(pattern)
    return glob.glob(pattern)

def getFiles(pattern):
    """
    Get all files that match a particular glob pattern.
    """
    return [each for each in getAll(pattern) if os.path.isfile(each)]

def getDirs(pattern):
    """
    Get all directories that match a particular glob pattern.
    """
    return [each for each in getAll(pattern) if os.path.isdir(each)]

def getFilesRecursively(path, acceptCriteria = None, rejectCriteria = None):
    """
    Returns a generator that iterates through all the files contained in a
    directory hierarchy.  Accept and reject criteria are glob strings, or lists
    of glob strings. For a file to be returned its name must not match any of
    the reject criteria if any are given, and it must match one of the accept
    criteria, if any are given.  If no criteria are given, all files are
    returned.
    """
    if type(acceptCriteria) == str:
        acceptCriteria = [acceptCriteria]
    if type(rejectCriteria) == str:
        rejectCriteria = [rejectCriteria]
    def yieldFile(filename):
        filename = getTail(filename)
        if acceptCriteria != None:
            if rejectCriteria != None:
                for criterion in rejectCriteria:
                    if fnmatch(filename, criterion):
                        return False
            for criterion in acceptCriteria:
                if fnmatch(filename, criterion):
                    return True
            return False
        else:
            if rejectCriteria != None:
                for criterion in rejectCriteria:
                    if fnmatch(filename, criterion):
                        return False
            return True

    if isFile(path):
        if yieldFile(path):
            yield path
    else:
        for path, subdirs, files in os.walk(path):
            for file in files:
                filename = makePath(path, file)
                if yieldFile(filename):
                    yield filename

# Type Utilities {{{1
def isFile(path):
    """
    Determine whether path corresponds to a file.
    """
    return os.path.isfile(path)

def isDir(path):
    """
    Determine whether path corresponds to a directory.
    """
    return os.path.isdir(path)

def isLink(path):
    """
    Determine whether path corresponds to a symbolic link.
    """
    return os.path.islink(path)

def exists(path):
    """
    Determine whether path corresponds to a file or directory.
    """
    return os.path.exists(path)

# File Type Utilities {{{2
def fileIsReadable(filepath):
    """
    Determine whether file exists and is readable by user.
    """
    return os.path.isfile(filepath) and os.access(filepath, os.R_OK)

def fileIsExecutable(filepath):
    """
    Determine whether file exists and is executable by user.
    """
    return os.path.isfile(filepath) and os.access(filepath, os.X_OK)

def fileIsWritable(filepath):
    """
    If filepath exists, determine whether it is writable by user.
    If not, determine if directory is writable by user.
    """
    if os.path.isfile(filepath) and os.access(filepath, os.W_OK):
        return True
    else:
        path = os.path.split(filepath)
        dirpath = os.path.join(*path[:-1])
        return os.path.isdir(dirpath) and os.access(filepath, os.W_OK)

# Directory Utilities {{{2
def dirIsReadable(dirpath):
    """
    Determine whether directory exists and is readable by user.
    """
    return os.path.isdir(dirpath) and os.access(dirpath, os.R_OK)

def dirIsWritable(dirpath):
    """
    Determine whether directory exists and is executable by user.
    """
    return os.path.isdir(dirpath) and os.access(dirpath, os.W_OK)


# Path Utilities {{{1
# Joins arguments into a filesystem path
def makePath(*args):
    """
    Join the arguments together into a filesystem path.
    """
    return os.path.join(*args)

# Splits path at directory boundaries into its component pieces
def splitPath(path):
    """
    Split the path at directory boundaries.
    """
    return os.path.split(path)

# Return normalized path
def normPath(path):
    """
    Convert to an normalized path (remove redundant separators and up-level references).
    """
    return os.path.normpath(path)

# Return absolute path
def absPath(path):
    """
    Convert to an absolute path.
    """
    return os.path.abspath(normPath(path))

# Return relative path
def relPath(path, start = None):
    """
    Convert to an relative path.
    """
    if start:
        return os.path.relpath(normPath(path), start)
    else:
        return os.path.relpath(normPath(path))

# Perform common path expansions (user, envvars)
def expandPath(path):
    """
    Expand initial ~ and any variables in a path.
    """
    path = os.path.expandvars(path)
    path = os.path.expanduser(path)
    path = os.path.normpath(path)
    return path

# Access components of a path {{{2
# Head (dir/file.ext ==> dir)
def getHead(path):
    """
    Return head of path: dir/file.ext ==> dir
    """
    return os.path.split(path)[0]

# Tail (dir/file.ext ==> file.ext)
def getTail(path):
    """
    Return tail of path: dir/file.ext ==> file.ext
    """
    return os.path.split(path)[1]

# Root (dir/file.ext ==> dir/file)
def getRoot(path):
    """
    Return root of path: dir/file.ext ==> dir/file
    """
    return os.path.splitext(path)[0]

# Extension (dir/file.ext ==> ext)
def getExt(path):
    """
    Return root of path: dir/file.ext ==> ext
    """
    ext = os.path.splitext(path)[1]
    return ext[1:] if ext else ''

# Copy, Move, Remove Utilities {{{1
def copy(src, dest):
    """
    Copy either a file or a directory.
    """
    import shutil
    destpath = splitPath(dest)[0:-1]
    destpath = makePath(*destpath)
    if destpath and not exists(destpath):
        os.makedirs(destpath)
    try:
        if isDir(src):
            shutil.copytree(src, dest, symlinks=True)
        else:
            shutil.copy2(src, dest)
    except (IOError, OSError), err:
        exit("%s: %s." % (err.filename, err.strerror))
    except shutil.Error, err:
        exit(["%s to %s: %s." % arg for arg in err.args])

def move(src, dest):
    """
    Move either a file or a directory.
    """
    import shutil
    try:
        shutil.move(src, dest)
    except (IOError, OSError), err:
        exit("%s: %s." % (err.filename, err.strerror))
    except shutil.Error, err:
        exit(["%s to %s: %s." % arg for arg in err.args])

def remove(path):
    """
    Remove either a file or a directory.
    """
    # if exists(path): # do not test for existance, this will causes misdirected symlinks to be ignored
    try:
        if isDir(path):
            import shutil
            shutil.rmtree(path)
        else:
            os.remove(path)
    except (IOError, OSError), err:
        exit("%s: %s." % (err.filename, err.strerror))

def mkdir(path):
    """
    Create a directory if it does not exist. If it does, return without complaint.
    """
    try:
        os.makedirs(path)
    except (IOError, OSError), err:
        if err.errno != errno.EEXIST:
            exit("%s: %s." % (err.filename, err.strerror))

# Execute Utilities {{{1
# Runs a shell command
def execute(cmd, accept = None):
    """
    Execute a command. Raise an ExecuteError if return status is not in accept.
    """
    import subprocess
    if accept == None:
        accept = (0,)
    status = subprocess.call(cmd, shell=True)
    if status not in accept:
        raise ExecuteError(
            "%s: unexpected exit status (%d)." % (
                cmd, status
            )
        )
    return status

class ExecuteError(Exception):
    def __init__(self, text):
        self.text = text
