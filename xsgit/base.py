import os

from . import data


def write_tree(directory="."):
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


def is_ignored(path):
    """
    Helper function to skip files to be included
    """
    return ".xsgit" in path.split("/")
