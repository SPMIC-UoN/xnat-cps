import os
import logging

LOG = logging.getLogger(__name__)

XNAT_CPS_FOLDER_NAME = "XNAT_DO_NOT_MODIFY"
README_CONTENTS = """\
This folder us being used as a storage backend for the XNAT imaging database

You MUST NOT rename or modify any files in this folder outside of XNAT.

You MAY copy files directly from here elsewhere for processing, etc.
"""

class MigrateError(Exception):
    pass

class Migrate:
    def __init__(self):
        self.xnat_backed_up = False
        self.data_copied = False

    def run(self, options):
        try:
            options.src_dir = self._check_xnat_project(options.xnat_archive, options.project)
            options.dest_dir = self._check_cps_folder(options.rdrive)
            self._confirm(options.xnat_archive, options.rdrive, options.project)

            self._create_cps_folder(options.rdrive)
            if options.use_rsync:
                self._initial_rsync(options.xnat_archive, options.rdrive, options.project)
            else:
                self._backup_xnat_project(options.xnat_archive, options.project)
                self.xnat_backed_up = True
                self._copy_data(options.xnat_archive, options.rdrive, options.project)
                self.data_copied = True
                self._create_link(options.xnat_archive, options.rdrive, options.project)
        except MigrateError as exc:
            self._fail(str(exc))
        except Exception as exc:
            self._fail(str(exc))
            raise

    def _fail(self, reason):
        LOG.error(reason)
        LOG.error("Could not migrate project")
        if self.xnat_backed_up:
            LOG.warn(f"XNAT data was already backed up to {options.xnat_backup} - check and remove before trying again")
        if self.data_copied:
            LOG.warn(f"Data was already copied to CPS folder {options.rdrive} - check and remove before trying again")

    def _confirm(self, xnat_archive, rdrive, project):
        LOG.info(f"Migrating project {project}")
        LOG.info(f" - Source XNAT archive: {xnat_archive}")
        LOG.info(f" - Destination CPS folder: {rdrive}")
        resp = input("Confirm by typing 'yes' - any other response will not migrate project: ")
        if resp.strip() != "yes":
            raise MigrateError("User did not confirm migration")

    def _check_xnat_project(self, xnat_archive, project):
        """
        Check that the project can be found in the expected place 
        and report total size, etc
        """
        LOG.info(f"Checking current XNAT archive for project {project}")
        LOG.info(f" - XNAT archive folder: {xnat_archive}")
        if not os.path.isdir(xnat_archive):
            raise MigrateError(f"XNAT archive folder: {xnat_archive} - not found or not a directory")
        
        if not os.access(xnat_archive, os.W_OK):
            raise MigrateError(f"XNAT archive folder: {xnat_archive} - not writable by current user")

        proj_dir = os.path.join(xnat_archive, project)
        LOG.info(f" - Project archive folder: {proj_dir}")
        if not os.path.isdir(proj_dir):
            raise MigrateError(f"Project {project} not found in XNAT archive folder: {xnat_archive}")

        if not os.access(proj_dir, os.W_OK):
            raise MigrateError(f"Project archive folder: {proj_dir} - not writable by current user")

        if os.path.islink(proj_dir):
            raise MigrateError(f"Project archive folder: {proj_dir} is already linked to another folder")

        data_size_mb = float(self._dir_size(proj_dir)) / 1048576
        LOG.info(f" - Total data size in archive: {data_size_mb:.1f} Mb")

    def _check_cps_folder(self, rdrive):
        """
        Check that the CPS folder is writable and the destination folder does not yet exist

        FIXME can we check if there is room for data?
        """
        LOG.info(f"Checking destination CPS folder")
        LOG.info(f" - CPS folder: {rdrive}")
        if not os.path.isdir(rdrive):
            raise MigrateError(f"CPS folder: {rdrive} - not found or not a directory")

        if not os.access(rdrive, os.W_OK):
            raise MigrateError(f"CPS folder: {rdrive} - not writable by current user")

        xnat_dir = os.path.join(rdrive, XNAT_CPS_FOLDER_NAME)
        LOG.info(f" - Destination CPS folder for XNAT data: {xnat_dir}")
        if os.path.exists(xnat_dir):
            raise MigrateError(f"XNAT destination folder on CPS drive: {xnat_dir} - already exists")
        return xnat_dir

    def _create_cps_folder(self, rdrive):
        LOG.info(f"Creating destination CPS folder")
        LOG.info(f" - CPS folder: {rdrive}")

        xnat_dir = os.path.join(rdrive, XNAT_CPS_FOLDER_NAME)
        os.mkdir(xnat_dir)
        LOG.info(f" - Created destination XNAT folder: {xnat_dir}")

        readme_fname = os.path.join(xnat_dir, "README.txt")
        with open(readme_fname, "w") as f:
            f.write(README_CONTENTS)
        LOG.info(f" - Created README file: {readme_fname}")

        warning_fname = os.path.join(xnat_dir, "DO_NOT_MODIFY_DATA_IN_THIS_FOLDER.txt")
        with open(warning_fname, "w") as f:
            f.write(README_CONTENTS)
        LOG.info(f" - Created warning file: {warning_fname}")

    def _dir_size(self, dir):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size


