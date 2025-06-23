import subprocess

from collections import defaultdict
from tempfile import NamedTemporaryFile as Temp

from . import data


def compare_trees(*trees):
    """
    Append changes into the entries dict to record changes
    """
    # Init dict
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    # Loop through items in dict and return in a tuple
    for path, oids in entries.items():
        # Unpack oids
        yield (path, *oids)


def iter_changed_files(t_ori, t_dest):
    """
    Generator or the path and the action type
    """
    for path, o_ori, o_dest in compare_trees(t_ori, t_dest):
        if o_ori != o_dest:
            action = ("new file" if not o_ori else
                      "deleted" if not o_dest else
                      "modified")
            yield path, action


def diff_trees(t_ori, t_dest):
    """
    Return the difference in the trees/commits
    """
    output = b""
    for path, o_ori, o_dest in compare_trees(t_ori, t_dest):
        # Append change string if origin and destination aren't the same
        if o_ori != o_dest:
            output += diff_blobs(o_ori, o_dest, path)
    return output


def diff_blobs(o_ori, o_dest, path="blob"):
    """
    Check the difference in each commit/blob
    """
    # Create a temporary file and make changes on it
    with Temp() as f_ori, Temp() as f_dest:
        for oid, f in ((o_ori, f_ori), (o_dest, f_dest)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()
        # Piping the output into stdout
        with subprocess.Popen(
            ["diff", "--unified", "--show-c-function",
             "--label", f"a/{path}", f_ori.name,
             "--label", f"b/{path}", f_dest.name],
                stdout=subprocess.PIPE) as proc:
            output, _ = proc.communicate()

    return output


def merge_trees(t_base, t_HEAD, t_other):
    """
    Merge trees by merging blobs
    """
    tree = {}
    for path, o_base, o_HEAD, o_other in compare_trees(t_base, t_HEAD, t_other):
        tree[path] = data.hash_object(merge_blobs(o_base, o_HEAD, o_other))

    return tree


def merge_blobs(o_base, o_HEAD, o_other):
    """
    Merge the lines in a temp files
    Pipe into stdout
    """
    with Temp() as f_base, Temp() as f_HEAD, Temp() as f_other:
        # Write blobs content to temporary file
        for oid, f in ((o_base, f_base), (o_HEAD, f_HEAD), (o_other, f_other)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()

        with subprocess.Popen(
                ["diff3", "-m",
                 "-L", "HEAD", f_HEAD.name,
                 "-L", "BASE", f_base.name,
                 "-L", "MERGE_HEAD", f_other.name],
                stdout=subprocess.PIPE) as proc:
            output, _ = proc.communicate()
            assert proc.returncode in (0, 1)

        return output
