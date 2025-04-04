import os

from . import data


def write_tree(directory="."):
    """
    Recursively generate encoded tree object
    """
    # Use os.scandir as a recursive generator
    entries = []
    with os.scandir(directory) as itr:
        for entry in itr:
            full = f"{directory}/{entry.name}"
            if is_ignored(full):
                continue

            # Determine type of entry
            if entry.is_file(follow_symlinks=False):
                type_ = "blob"
                with open(full, "rb") as f:
                    oid = data.hash_object(f.read())
            elif entry.is_dir(follow_symlinks=False):
                type_ = "tree"
                oid = write_tree(full)

            entries.append((entry.name, oid, type_))

    tree = ""
    for name, oid, type_ in sorted(entries):
        tree = "".join(f"{type_} {oid} {name}\n")
    return data.hash_object(tree.encode(), "tree")


def _iter_tree_entries(oid):
    """
    Function that generate an iterator for the entries in input tree object
    """
    if not oid:
        return

    tree = data.get_object(oid, "tree")
    # Iterator that yields entry info until recursion ends in callee function
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(" ", 2)
        yield type_, oid, name


def get_tree(oid, base_path=""):
    """
    Go through the tree object recursively
    Store key(path),value(oid) pair in the result dictionary
    Return the dictionary of tree info after recursively get all of the objects
    """
    result = {}
    for type_, oid_, name in _iter_tree_entries(oid):
        assert "/" not in name
        assert name not in ("..", ".")
        path = base_path + name

        if type == "blob":
            result[path] = oid_
        elif type == "tree":
            result.update(get_tree(oid_, f"{path}/"))
        else:
            assert False, f"Unknown tree entry {type_}"
    return result


def _empty_curr_directory():
    """
    Clear current directory iteratively before reading a tree objct
    """
    for root, directories, files in os.walk(".", topdown=False):
        for f in files:
            path = os.path.relpath(f"{root}/{f}")

            if is_ignored(path) or not os.path.isfile(path):
                continue

            os.remove(path)

        for directory in directories:
            path = os.path.relpath(f"{root}/{directory}")
            if is_ignored(path):
                continue
            try:
                os.rmdir(path)
            except (FileNotFoundError, OSError):
                pass


def read_tree(tree_oid):
    """
    Write binary files in path for the tree extracted
    """
    _empty_curr_directory()
    for path, oid in get_tree(tree_oid, base_path="./").items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data.get_object(oid))


def commit(message):
    """
    Committing a message and encode the message into a blob
    """
    commit_msg = f"tree {write_tree()}\n"

    HEAD = data.get_HEAD()
    if HEAD:
        commit_msg += f"parent {HEAD}"

    commit_msg += "\n"
    commit_msg += f"{message}\n"

    # print(commit_msg)

    oid = data.hash_object(commit_msg.encode(), "commit")

    # Set the latest commit as HEAD
    data.set_HEAD(oid)

    return oid


def is_ignored(path):
    """
    Helper function to skip files to be included
    """
    return ".xsgit" in path.split("/")
