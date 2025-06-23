import os
import itertools
import operator
import string

from collections import deque, namedtuple
from . import data, diff


def init():
    """
    Initialization of the base of our system
    """
    data.init()
    data.update_ref("HEAD", data.RefValue(
        symbolic=True, value="refs/heads/main"))


def write_tree():
    """
    Write into tree and set up the recursive structure
    """
    index_as_tree = {}
    with data.get_index() as index:
        for path, oid in index.items():
            path = path.split("/")
            dirpath, filename = path[:-1], path[-1]

            curr = index_as_tree

            for dirname in dirpath:
                curr = curr.setdefault(dirname, {})
            curr[filename] = oid

    def write_tree_recursive(tree_dict):
        entries = []
        for name, value in tree_dict.items():
            if isinstance(value, dict):
                type_ = "tree"
                oid = write_tree_recursive(value)
            else:
                type_ = "blob"
                oid = value

            entries.append((name, oid, type_))

        tree = "".join(f"{type_} {oid} {name}\n"
                       for name, oid, type_ in sorted(entries))
        return data.hash_object(tree.encode(), "tree")

    return write_tree_recursive(index_as_tree)


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


def get_working_tree():
    """
    Go through curr directory and get info form files
    """
    result = {}
    for root, _, fnames, in os.walk("."):
        for fname in fnames:
            path = os.path.relpath(f"{root}/{fname}")
            if is_ignored(path) or not os.path.isfile(path):
                continue
            with open(path, "rb") as f:
                result[path] = data.hash_object(f.read())

    return result


def get_index_tree():
    """
    Return index
    """
    with data.get_index() as index:
        return index


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


def read_tree(tree_oid, update_working=False):
    """
    Include indcices in tree reading
    """
    with data.get_index() as index:
        index.clear()
        index.update(get_tree(tree_oid))

        if update_working:
            _checkout_index(index)


def read_tree_merged(t_base, t_HEAD, t_other, update_working=False):
    """
    Merge trees by writing into files
    """
    with data.get_index() as index:
        index.clear()
        index.update(diff.merge_trees(
            get_tree(t_base),
            get_tree(t_HEAD),
            get_tree(t_other)
        ))

    if update_working:
        _checkout_index(index)


def _checkout_index(index):
    """
    Checkout to a particular index
    """
    _empty_curr_directory()
    for path, oid in index.items():
        os.makedirs(os.path.dirname(f"./{path}"), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data.get_object(oid, "blob"))


def commit(message):
    """
    Committing a message and encode the message into a blob
    """
    commit_msg = f"tree {write_tree()}\n"

    HEAD = data.get_ref("HEAD").value
    if HEAD:
        commit_msg += f"parent {HEAD}\n"

    MERGE_HEAD = data.get_ref("MERGE_HEAD").value
    if MERGE_HEAD:
        commit_msg += f"parent {MERGE_HEAD}\n"
        data.delete_ref("MERGE_HEAD", deref=False)

    commit_msg += "\n"
    commit_msg += f"{message}\n"

    # print(commit_msg)

    oid = data.hash_object(commit_msg.encode(), "commit")

    # Set the latest commit as HEAD
    data.update_ref("HEAD", data.RefValue(symbolic=False, value=oid))

    return oid


def checkout(name):
    """
    Given an oid and get read the tree and set our HEAD to the tree
    """
    oid = get_oid(name)
    cmt = get_commit(oid)
    read_tree(cmt.tree, update_working=True)

    if is_branch(name):
        HEAD = data.RefValue(symbolic=True, value=f"refs/heads/{name}")
    else:
        HEAD = data.RefValue(symbolic=False, value=oid)

    data.update_ref("HEAD", HEAD, deref=False)


def reset(oid):
    """
    Reset HEAD to certain oid
    """
    data.update_ref("HEAD", data.RefValue(symbolic=False, value=oid))


def merge(other):
    """
    Merge branches and resolve conflicts
    """
    HEAD = data.get_ref("HEAD").value
    assert HEAD
    merge_base = get_merge_base(other, HEAD)
    c_other = get_commit(other)

    # Handle fast-farward mege while can
    if merge_base == HEAD:
        read_tree(c_other.tree, update_working=True)
        data.update_ref("HEAD", data.RefValue(symbolic=False, value=other))
        print("Fast-forward merge, no need to commit")
        return

    data.update_ref("MERGE_HEAD", data.RefValue(symbolic=False, value=other))

    c_base = get_commit(merge_base)
    c_HEAD = get_commit(HEAD)
    read_tree_merged(c_base.tree, c_HEAD.tree,
                     c_other.tree, update_working=True)
    print("Merged in working tree\nPlease commit")


def get_merge_base(oid1, oid2):
    """
    Return the oid of the merge's base by comparing one by one
    """
    parents1 = set(iter_commits_and_parents({oid1}))

    for oid in iter_commits_and_parents({oid2}):
        if oid in parents1:
            return oid

    return None


def is_ancestor_of(cmt, potential_ancestor):
    """
    Return boolean value of check
    """
    return potential_ancestor in iter_commits_and_parents({cmt})


def create_tag(name, oid):
    """
    Create a tag given the name
    """
    data.update_ref(f"refs/tags/{name}",
                    data.RefValue(symbolic=False, value=oid))


def create_branch(name, oid):
    """
    Create a branch of the given name
    """
    data.update_ref(f"refs/heads/{name}",
                    data.RefValue(symbolic=False, value=oid))


def iter_branch_name():
    """
    Generator for branches
    """
    for refname, _ in data.iter_refs("refs/heads/"):
        yield os.path.relpath(refname, "refs/heads/")


def is_branch(branch):
    """
    Return branch or not
    """
    return data.get_ref(f"refs/heads/{branch}").value is not None


def get_branch_name():
    """
    Helper function to get branch name of a oid
    """
    HEAD = data.get_ref("HEAD", deref=False)
    if not HEAD.symbolic:
        return None

    HEAD = HEAD.value
    assert HEAD.startswith("refs/heads/")
    return os.path.relpath(HEAD, "refs/heads")


Commit = namedtuple("Commit", ["tree", "parents", "message"])


def get_commit(oid):
    """
    Iterate through the commits and return a namedtuple
    """
    # TODO: Analyze the time complexity, if bad, use trie to optimize the performance

    parents = []

    cmt = data.get_object(oid, "commit").decode()
    lines = iter(cmt.splitlines())

    tree = ""
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(" ", 1)
        if key == "tree":
            tree = value
        elif key == "parent":
            parents.append(value)
        else:
            assert False, f"Unknown field {key}"

    message = "\n".join(lines)
    return Commit(tree=tree, parents=parents, message=message)


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
        oids.extendleft(cmt.parents[:1])
        oids.extend(cmt.parents[1:])


def iter_objects_in_commits(oids):
    """

    """
    visited = set()

    def iter_objects_in_tree(oid):
        """
        Subfunction to get all oid
        """
        visited.add(oid)
        yield oid

        for type_, oid_, _ in _iter_tree_entries(oid):
            if oid_ not in visited:
                if type_ == "tree":
                    yield from iter_objects_in_tree(oid_)
                else:
                    visited.add(oid_)
                    yield oid_

    for oid in iter_commits_and_parents(oids):
        yield oid
        cmt = get_commit(oid)
        if cmt.tree not in visited:
            yield from iter_objects_in_tree(cmt.tree)


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
        if data.get_ref(ref, deref=False).value:
            return data.get_ref(ref).value

    # Check for name to be a hashed value
    is_hex = all(c in string.hexdigits for c in name)
    if len(name) == 40 and is_hex:
        return name

    assert False, f"Unknown name {name}"


def add(filenames):
    """
    Put file changes
    """
    def add_file(filename):
        filename = os.path.relpath(filename)
        with open(filename, "rb") as f:
            oid = data.hash_object(f.read())
        index[filename] = oid

    def add_directory(dirname):
        for root, _, filenames in os.walk(dirname):
            for filename in filenames:
                path = os.path.relpath(f"{root}/{filename}")
                if is_ignored(path) or not os.path.isfile(path):
                    continue
                add_file(path)

    with data.get_index() as index:
        for name in filenames:
            if os.path.isfile(name):
                add_file(name)
            elif os.path.isdir(name):
                add_directory(name)


def is_ignored(path):
    """
    Helper function to skip files to be included
    """
    return ".xsgit" in path.split("/")
