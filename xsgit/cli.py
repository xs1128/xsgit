import argparse
import os
import textwrap
import sys
import subprocess

from . import base, data, diff, remote


def main():
    """
    Call and run the functions for parsing arguments
    """
    with data.change_git_dir("."):
        args = parse_args()
        args.func(args)


def parse_args():
    """
    Initialize parsers:
    Main: commands
        1. init
        2. hash_object
        3. cat-file
        4. write-tree
        5. read-tree
        6. commit
        7. log
        8. checkout
        9. tag
        10. k
        11. branch
        12. diff
        13. merge
        14. fetch
        15. push
        16. add
        17. show
        18. status
        19. merge-base
    """
    parser = argparse.ArgumentParser()

    commands = parser.add_subparsers(dest="command")
    commands.required = True

    oid = base.get_oid

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser("hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser("cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument("object", type=oid)

    write_tree_parser = commands.add_parser("write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser("read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree", type=oid)

    commit_parser = commands.add_parser("commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser("log")
    log_parser.set_defaults(func=log)
    log_parser.add_argument("oid", default="@", type=oid, nargs="?")

    show_parser = commands.add_parser("show")
    show_parser.set_defaults(func=show)
    show_parser.add_argument("oid", default="@", type=oid, nargs="?")

    diff_parser = commands.add_parser("diff")
    # use underscore to differentiate from python built in diff
    diff_parser.set_defaults(func=_diff)
    diff_parser.add_argument("--cached", action="store_true")
    diff_parser.add_argument("commit", nargs="?")

    checkout_parser = commands.add_parser("checkout")
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument("commit")

    tag_parser = commands.add_parser("tag")
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument("name")
    tag_parser.add_argument("oid", default="@", type=oid, nargs="?")

    # Graphical visualization thingy
    k_parser = commands.add_parser("k")
    k_parser.set_defaults(func=k)

    branch_parser = commands.add_parser("branch")
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument("name", nargs="?")
    branch_parser.add_argument("starting", default="@", type=oid, nargs="?")

    status_parser = commands.add_parser("status")
    status_parser.set_defaults(func=status)

    reset_parser = commands.add_parser("reset")
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument("commit", type=oid)

    merge_parser = commands.add_parser("merge")
    merge_parser.set_defaults(func=merge)
    merge_parser.add_argument("commit", type=oid)

    # Return the common ancestor of two commits
    merge_base_parser = commands.add_parser("merge-base")
    merge_base_parser.set_defaults(func=merge_base)
    merge_base_parser.add_argument("commit1", type=oid)
    merge_base_parser.add_argument("commit2", type=oid)

    fetch_parser = commands.add_parser("fetch")
    fetch_parser.set_defaults(func=fetch)
    fetch_parser.add_argument("remote")

    push_parser = commands.add_parser("push")
    push_parser.set_defaults(func=push)
    push_parser.add_argument("remote")
    push_parser.add_argument("branch")

    add_parser = commands.add_parser("add")
    add_parser.set_defaults(func=add)
    add_parser.add_argument("files", nargs="+")

    return parser.parse_args()


def init(args):
    """
    Init function
    """
    base.init()
    print(
        f"Initialized empty xsgit repository in {
            os.getcwd()}/{data.GIT_DIR}"
    )


def hash_object(args):
    """
    Perform file read and pass to hash_object function in data.py
    """
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))


def cat_file(args):
    """
    Deal with stdout after getting return from decryption function
    """
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))


def write_tree(args):
    """
    Process files and directories into objects
    Dirctories will be type of "tree"
    Files will be in the type of "blob"
    """
    print(base.write_tree())


def read_tree(args):
    """
    Take in the object type and extract the encrypted data inside
    """
    base.read_tree(args.tree)


def commit(args):
    """
    Create a commit message
    """
    print(base.commit(args.message))


def _print_commit(oid, cmt, refs=None):
    """
    Return the commit string
    """
    refs_str = f" ({', '.join(refs)})" if refs else ""
    print(f"commit {oid}{refs_str}\n")
    print(textwrap.indent(cmt.message, "    "))
    print("")


def log(args):
    """
    Return the log of commits
    """
    refs = {}
    for refname, ref in data.iter_refs():
        refs.setdefault(ref.value, []).append(refname)

    for oid in base.iter_commits_and_parents({args.oid}):
        cmt = base.get_commit(oid)
        _print_commit(oid, cmt, refs.get(oid))


def show(args):
    """
    Print commits
    """
    if not args.oid:
        return
    cmt = base.get_commit(args.oid)
    parent_tree = None
    if cmt.parents:
        parent_tree = base.get_commit(cmt.parents[0]).tree

    _print_commit(args.oid, cmt)
    result = diff.diff_trees(base.get_tree(
        parent_tree), base.get_tree(cmt.tree))

    sys.stdout.flush()
    sys.stdout.buffer.write(result)


def _diff(args):
    """
    Put the difference in the stdout buffer
    """
    oid = args.commit and base.get_oid(args.commit)

    tree_from = tree_to = None

    if args.commit:
        # Provided commit hash
        tree_from = base.get_tree(oid and base.get_commit(oid).tree)

    if args.cached:
        # If no commit, set from HEAD
        tree_to = base.get_index_tree()
        if not args.commit:
            oid = base.get_oid("@")
            tree_from = base.get_index_tree(oid and base.get_commit(oid).tree)
    else:
        tree_to = base.get_working_tree()
        if not args.commit:
            tree_from = base.get_index_tree()

    result = diff.diff_trees(tree_from, tree_to)
    sys.stdout.flush()
    sys.stdout.buffer.write(result)


def checkout(args):
    """
    Checkout to different branch
    """
    base.checkout(args.commit)


def tag(args):
    """
    Get object id from argument or current HEAD
    Create a tag of it
    """
    base.create_tag(args.name, args.oid)


def branch(args):
    """
    Display current branch name if exist
    Create new branch if new (depending on the param)
    """
    if not args.name:
        curr = base.get_branch_name()
        for brnch in base.iter_branch_name():
            prefix = "*" if brnch == curr else " "
            print(f"{prefix} {brnch}")
    else:
        base.create_branch(args.name, args.starting)
        print(f"Branch {args.name} created at {args.starting[:10]}")


def k(args):
    """
    Display git blobs and trees in a ordered manner
    """
    dot = "digraph commits {\n"
    oids = set()
    for refname, ref in data.iter_refs(deref=False):
        dot += f'"{refname}" [shape=note]\n'
        dot += f'"{refname}" -> "{ref.value}"\n'
        if not ref.symbolic:
            oids.add(ref.value)

    for oid in base.iter_commits_and_parents(oids):
        cmt = base.get_commit(oid)
        dot += f'"{oid}" [shape=box style=filled label="{oid[:10]}"]\n'

        for parent in cmt.parents:
            dot += f'"{oid}" -> "{parent}"\n'

    dot += "}"

    # Visualize the reference on your brower
    # On MacOS, open x.svg -a Browser.app
    with subprocess.Popen(
        ['dot', '-Tsvg'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    ) as proc:
        svg_data, _ = proc.communicate(dot.encode())
    with open('output.svg', 'wb') as f:
        f.write(svg_data)


def status(args):
    """
    Command that show current branch's status
    """
    HEAD = base.get_oid("@")
    brnch = base.get_branch_name()

    if brnch:
        print(f"On branch {brnch}")
    else:
        print(f"HEAD detached at {HEAD[:10]}")

    MERGE_HEAD = data.get_ref("MERGE_HEAD").value
    if MERGE_HEAD:
        print(f"Merging with {MERGE_HEAD[:10]}")

    print("\nChanges to be commited:\n")
    HEAD_tree = HEAD and base.get_commit(HEAD).tree

    for path, action in diff.iter_changed_files(base.get_tree(HEAD_tree),
                                                base.get_index_tree()):
        # Formatting the action
        print(f"{action:>12}: {path}")

    print("\nChanges not staged for commit:\n")

    for path, action in diff.iter_changed_files(base.get_index_tree(),
                                                base.get_working_tree()):
        print(f"{action:>12}: {path}")


def reset(args):
    """
    Helper function for reset of HEAD pointer
    """
    base.reset(args.commit)


def merge(args):
    """
    Helper function for merging
    """
    base.merge(args.commit)


def merge_base(args):
    """
    Helper function to check merge base of two commits
    """
    print(base.get_merge_base(args.commit1, args.commit2))


def fetch(args):
    """
    Helper function for fetching from remote
    """
    remote.fetch(args.remote)


def push(args):
    """
    Helper function for pushing to remote
    """
    remote.push(args.remote, f"refs/heads/{args.branch}")


def add(args):
    """
    Helper function that directs to add
    """
    base.add(args.files)
