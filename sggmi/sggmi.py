
import logging
import logging.config
import os
import stat
from distutils.dir_util import copy_tree
from distutils.errors import DistutilsFileError
from pathlib import Path, PurePath
from shutil import copyfile, rmtree
from typing import Iterable, Mapping

from config import config
from commands.mod_edit import ModEdit
from mod_file import ModFile
from util.file import hash_file, is_edited

# Global Preprocessing


def initialize_logs():
    """Create the logs directory, if it doesn't exist, and load the config"""
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    logging.config.fileConfig("sggmi.logging.config")


def copy_touched_files_to_deploy_directory(touched_files: Iterable[Path]):
    """Copy all necessary mod files to the Deploy directory

    Parameters
    ----------
    touched_files : Iterable[Path]
        all required mod files
    """
    for file_path in touched_files:
        file_relative_path = file_path.parent.relative_to(config.mods_dir)
        (config.deploy_dir / file_relative_path).mkdir(parents=True, exist_ok=True)
        copyfile(
            config.mods_dir / file_relative_path, config.deploy_dir / file_relative_path
        )


def sort_mod_edits_by_base_file(
    mod_edits: Iterable[ModEdit],
) -> dict[Path, list[ModEdit]]:
    """Given a list of ModEdits, return a dictionary mapping each unique target
    file to the relevant ModEdits. The sort is stable, so it should leave the priority
    sorting intact.

    Parameters
    ----------
    mod_edits : Iterable[ModEdit]
        all edits to be applied

    Returns
    -------
    dict[Path, list[ModEdit]]
        _description_
    """
    result = {}
    for mod_edit in mod_edits:
        if mod_edit.target_file not in result:
            result[mod_edit.target_file] = []
        result[mod_edit.target_file].append(mod_edit)
    return result


def create_working_copies_of_affected_files(mod_edits: Iterable[ModEdit]):
    """To prevent damage to base files, create a backup in config.base_cache_dir
    and a working copy in config.edit_cache_dir

    Parameters
    ----------
    mod_edits : Iterable[ModEdit]
        edits to be applied to the base files
    """
    for base_file in sort_mod_edits_by_base_file(mod_edits).keys():
        logging.debug(
            f"Creating copy of {base_file.name} in {config.base_cache_dir.relative_to(config.scope_dir).name}"
        )

        Path(config.base_cache_dir / base_file.parent).mkdir(
            parents=True, exist_ok=True
        )
        Path(config.edit_cache_dir / base_file.parent).mkdir(
            parents=True, exist_ok=True
        )

        copyfile(config.scope_dir / base_file, config.base_cache_dir / base_file)
        copyfile(config.scope_dir / base_file, config.edit_cache_dir / base_file)

        hash_file(
            config.scope_dir / base_file,
            config.edit_cache_dir / f"{base_file}{config.edited_suffix}",
        )


def cleanup(folder_path: PurePath):
    folder = Path(folder_path)
    if not folder.exists():
        logging.debug("Skipping cleanup - folder does not exist.")
        return True

    if folder.is_file():
        empty = True
        for entry in folder.iterdir():
            if cleanup(entry):
                empty = False
        if empty:
            os.rmdir(folder)
            return False
        return True

    if isinstance(folder, str):
        return None

    file_path = folder.relative_to(config.base_cache_dir)
    if Path(config.scope_dir / file_path).is_file():
        if is_edited(file_path):
            copyfile(folder, config.scope_dir / file_path)
        file_path.unlink()
        return False
    return True


def restore_base():
    if not cleanup(config.base_cache_dir):
        try:
            copy_tree(config.base_cache_dir, config.scope_dir)
        except DistutilsFileError:
            pass


def detect_modfiles(config: Mapping) -> list[ModFile]:
    """Detect any modfiles from Mods directory and generate a list of ModFile objects

    Parameters
    ----------
    config : Mapping
        _description_

    Returns
    -------
    list[ModFile]
        _description_
    """
    logging.info("\nReading mod files...")
    return [ModFile(mod_file.name) for mod_file in Path(config["mods_dir"]).iterdir()]


def process_modfiles(mod_files: Iterable[ModFile]) -> list[ModEdit]:
    """Process the provided mod files, generating a list of ModEdits sorted by
    priority.

    Parameters
    ----------
    mod_files : Iterable[ModFile]
        _description_

    Returns
    -------
    list[Command]
        _description_
    """
    mod_edits = []
    for mod_file in mod_files:
        mod_edits.extend(mod_file.process())

    return sorted(mod_edits, key=lambda mod_edit: mod_edit.priority)


def execute_mod_edits(mod_edits: Iterable[ModEdit]):
    """Apply ModEdits to the working copies of the game files

    Parameters
    ----------
    base : _type_
        _description_
    mod_edits : Iterable[ModEdit]
        _description_

    Raises
    ------
    RuntimeError
        _description_
    """
    sorted_edits = sort_mod_edits_by_base_file(mod_edits)

    for base_file, edits in sorted_edits.items():
        try:
            for mod_edit in edits:
                # Make ModEdit target edit cache instead of base file
                mod_edit.execute(config.edit_cache_dir / base_file)
        except Exception as exc:
            raise RuntimeError("Something went wrong importing mods!") from exc


def deploy_mods():
    """Detect, parse, and execute all modfiles in the Mods directory. Deploy
    the mods specified by performing all edits in a working cache and then copying
    them over the base files.
    """
    # remove the edit cache and base cache from the last run
    def set_write_permissions_and_try_again(func, path, _):
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    # remove anything in the base cache that is not in the edit cache
    print("Cleaning edits... (if there are issues validate/reinstall files)")
    restore_base()

    logging.debug("Deleting caches...")
    rmtree(config.edit_cache_dir, onerror=set_write_permissions_and_try_again)
    rmtree(config.base_cache_dir, onerror=set_write_permissions_and_try_again)

    logging.debug("Creating working directories...")
    config.edit_cache_dir.mkdir(parents=True, exist_ok=True)
    config.base_cache_dir.mkdir(parents=True, exist_ok=True)
    config.mods_dir.mkdir(parents=True, exist_ok=True)
    config.deploy_dir.mkdir(parents=True, exist_ok=True)

    mod_files = detect_modfiles()
    mod_edits = process_modfiles(mod_files)

    create_working_copies_of_affected_files(mod_edits)
    execute_mod_edits(mod_edits)

    sorted_edits = sort_mod_edits_by_base_file(mod_edits)
    for base_file in sorted_edits.keys():
        copyfile(config.edit_cache_dir / base_file, config.scope_dir / base_file)

    logging.info("Modified files:")
    num_file_edits = len(sorted_edits.keys())
    num_mod_files = len(mod_files)

    for base_file, edits in sorted_edits.items():
        num_file_edits += 1
        logging.info(base_file.name)
        for edit in edits:
            logging.info(f"  - {edit.target_file}")

    logging.info(
        f"\n{str(num_file_edits)} file{('s', '')[num_file_edits == 1]} modified by {num_mod_files} mod file{'s' * (num_mod_files != 1)}."
    )
