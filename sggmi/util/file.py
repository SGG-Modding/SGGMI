from pathlib import PurePath
from typing import Mapping
import hashlib


def is_subfile(target_path: PurePath, parent_path: PurePath) -> bool:
    return target_path.relative_to(parent_path) and target_path.is_file()


def is_subdirectory(target_path: PurePath, parent_path: PurePath) -> bool:
    return target_path.relative_to(parent_path) and target_path.is_dir()


def in_scope(filename: PurePath, config: Mapping, permit_DNE: bool = False) -> bool:
    if not (permit_DNE or filename.exists()):
        return False

    try:
        filename.relative_to(config.scope_dir)
    except ValueError:
        return False

    return True


def in_source(filename: PurePath, config: Mapping, permit_DNE=False) -> bool:
    if not (filename.exists() or permit_DNE):
        return False

    return filename.relative_to(config.scope_dir) and config.mods_dir.relative_to(
        config.scope_dir
    )


def is_edited(base, config) -> bool:
    edited_path: PurePath = config.edit_cache_dir / f"{base}{config.edited_suffix}"
    if edited_path.is_file():
        with open(edited_path, "r") as edited_file:
            data = edited_file.read()

        return data == hash_file(PurePath.joinpath(config.scope_dir, base))
    return False


def check_scopes(config) -> bool:
    if not in_scope(config.scope_dir, config):
        print(
            f"FAILED {config.scope_dir} is not in scope",
            config=config,
        )
        return False

    if not in_scope(config.deploy_dir, config):
        print(
            f"FAILED {config.deploy_dir} is not in scope",
            config=config,
        )
        return False

    return True


def hash_file(file, out=None, modes=[], blocksize=65536):
    """
    Return file as a list of hashes
    """
    lines = []

    for mode in modes:
        hasher = hashlib.new(mode)
        with open(file, "rb") as afile:
            buf = afile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(blocksize)
            lines.append(mode + "\t" + hasher.hexdigest())

    content = "\n".join(lines)
    if out:
        with open(out, "w") as ofile:
            ofile.write(content)

    return content
