import os
import shutil

from . import base, data

REMOTE_REFS_BASE = "refs/heads/"
LOCAL_REFS_BASE = "refs/remote/"


def fetch(remote_path):
    """
    Fetch info from path passed in
    """
    # Get ref from server
    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)

    # Only fetch missing objects
    for oid in base.iter_objects_in_commits(refs.values()):
        data.fetch_object_if_missing(oid, remote_path)

    # Update local
    for remote_name, value in refs.items():
        refname = os.path.relpath(remote_name, REMOTE_REFS_BASE)
        data.update_ref(f"{LOCAL_REFS_BASE}/{refname}",
                        data.RefValue(symbolic=False, value=value))


def push(remote_path, refname):
    """
    Push the data local to remote's branch
    """
    # Get ref data
    remote_refs = _get_remote_refs(remote_path)
    remote_ref = remote_refs.get(refname)
    local_ref = data.get_ref(refname).value
    assert local_ref

    assert not remote_ref or base.is_ancestor_of(local_ref, remote_ref)

    # Filter out unnecessary trees or blobs
    known_remote_refs = filter(data.object_exists, remote_refs.values())
    remote_objects = set(base.iter_objects_in_commits(known_remote_refs))
    local_objects = set(base.iter_objects_in_commits({local_ref}))
    # Use set operations
    objects_to_push = local_objects - remote_objects

    # Push missing objects
    # Since the commits with same thingy will have same hash
    for oid in objects_to_push:
        data.push_object(oid, remote_path)

    # Update server ref to local data
    with data.change_git_dir(remote_path):
        data.update_ref(refname, data.RefValue(
            symbolic=False, value=local_ref))


def _get_remote_refs(remote_path, prefix=""):
    """
    Make the callee function cleaner
    """
    with data.change_git_dir(remote_path):
        return {refname: ref.value for refname, ref in data.iter_refs(prefix)}


# For copying files
# def update_remote_dir(remote_path):
#     """
#     Update the remote repo's working tree to match pushed
#     """
#     # Clear everything first
#     for item in os.listdir(remote_path):
#         item_path = os.path.join(remote_path, item)
#         if item != ".xsgit":
#             if os.path.isdir(item_path):
#                 shutil.rmtree(item_path)
#             else:
#                 os.remove(item_path)
#
#     copy_working_to_remote(".", remote_path)
#
#
# def copy_working_to_remote(local_path, remote_path):
#     """
#     Recurively copy local files and directories into the remote
#     """
#     for item in os.listdir(local_path):
#         if item == '.xsgit':
#             continue
#
#         # Store local and remote item path and copy at the same time
#         local_item_path = os.path.join(local_path, item)
#         remote_item_path = os.path.join(remote_path, item)
#
#         # Check whether recursive call or not
#         if os.path.isdir(local_item_path):
#             os.makedirs(remote_item_path, exist_ok=True)
#             copy_working_to_remote(local_item_path, remote_item_path)
#         else:
#             shutil.copy2(local_item_path, remote_item_path)
