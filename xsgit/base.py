import os
import itertools
import operator
import string

from collections import deque, namedtuple
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

        if type_ == "blob":
            result[path] = oid_
        elif type_ == "tree":
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

    HEAD = data.get_ref("HEAD")
    if HEAD:
        commit_msg += f"parent {HEAD}\n"

    commit_msg += "\n"
    commit_msg += f"{message}\n"

    # print(commit_msg)

    oid = data.hash_object(commit_msg.encode(), "commit")

    # Set the latest commit as HEAD
    data.update_ref("HEAD", oid)

    return oid


def checkout(oid):
    """
    Given an oid and get read the tree and set our HEAD to the tree
    """
    commit = get_commit(oid)
    read_tree(commit.tree)
    data.update_ref("HEAD", oid)


def create_tag(name, oid):
    """
    Create a tag given the name
    """
    data.update_ref(f"refs/tags/{name}", oid)


Commit = namedtuple("Commit", ["tree", "parent", "message"])


def get_commit(oid):
    """
    Iterate through the commits and return a namedtuple
    """
    # TODO: Analyze the time complexity, if bad, use trie to optimize the performance

    parent = None

    cmt = data.get_object(oid, "commit").decode()
    lines = iter(cmt.splitlines())

    tree = ""
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(" ", 1)
        if key == "tree":
            tree = value
        elif key == "parent":
            parent = value
        else:
            assert False, f"Unknown field {key}"

    message = "\n".join(lines)
    return Commit(tree=tree, parent=parent, message=message)


def iter_commits_and_parents(oids):
    """
    Loop through every objet IDs
    Run a BFS to go through all objects
    """
    oids = deque(oids)
    visited = set()

    while oids:
        oid = oids.popleft()
        if not oid or oid in visited:
            continue
        visited.add(oid)
        yield oid

        cmt = get_commit(oid)
        # Append the next parent
        oids.appendleft(cmt.parent)


def get_oid(name):
    """
    Return the oid of the tag name or the name is the oid
    Quality of life upgrade for path prefix
    """
    if name == "@":
        name = "HEAD"

    potential_refs = [
        f"{name}",
        f"refs/{name}",
        f"refs/tags/{name}",
        f"refs/heads/{name}",
    ]

    for ref in potential_refs:
        if data.get_ref(ref):
            return data.get_ref(ref)

    # Check for name to be a hashed value
    is_hex = all(c in string.hexdigits for c in name)
    if len(name) == 40 and is_hex:
        return name

    assert False, f"Unknown name {name}"


def is_ignored(path):
    """
    Helper function to skip files to be included
    """
    return ".xsgit" in path.split("/")
