import logging
import os
import shutil
import subprocess

LOG = logging.getLogger(__name__)

README_FNAME = "README.txt"
WARNING_FNAME = "DO_NOT_MODIFY_DATA_IN_THIS_FOLDER.txt"
README_CONTENTS = """\
This folder us being used as a storage backend for the XNAT imaging database

You MUST NOT rename or modify any files in this folder outside of XNAT.

You MAY copy files directly from here elsewhere for processing, etc.
"""

class MigrateError(Exception):
    """
    Exception subclass to indicate 'expected' failures.

    If one of these occurs we will simply display the reason but not the 
    stack trace
    """
    pass

class Migrate:
    def __init__(self, options):
        self.options = options
        self.src_proj_dir = os.path.join(options.xnat_archive, options.project)
        if options.xnat_backup:
            self.dest_backup_dir = os.path.join(options.xnat_backup, options.project)
        self.dest_archive_dir = os.path.join(options.rdrive, options.rdrive_xnat_dirname)
        self.dest_proj_dir = os.path.join(self.dest_archive_dir, options.project)
        self.dest_dir_created = False
        self.xnat_backed_up = False
        self.data_copied = False
        self.data_size = 0

    def run(self):
        cmd = getattr(self, self.options.command, None)
        if not cmd:
            raise ValueError(f"No such command: {self.options.command}")
        
        try:
            cmd()
        except MigrateError as exc:
            self._fail(str(exc))
        except Exception as exc:
            self._fail(str(exc))
            raise

    def init(self):
        self._init_cps_folder()

    def sync(self):
        self._check_xnat_folder(require_writable=False)
        self._check_cps_folder()
        self._update_data()

    def backup(self):
        self._check_backup_folder()
        self._backup_data()

    def link(self):
        self._check_xnat_folder(require_writable=True)
        self._check_cps_folder()
        self._update_data()
        self._create_link()

    def _fail(self, reason):
        LOG.error(reason)
        LOG.error("Command failed")
        if self.xnat_backed_up:
            LOG.warn(f"XNAT data was already backed up to {self.options.xnat_backup} - check and remove before trying again")
        if self.dest_dir_created:
            LOG.warn(f"Destination folder {self.dest_archive_dir} already created- check and remove before trying again")
        if self.data_copied:
            LOG.warn(f"Data was already copied to destination folder {self.options.rdrive} - check and remove before trying again")

    def _check_xnat_folder(self, require_writable=True):
        """
        Check that the project can be found in the expected place 
        and report total size, etc
        """
        LOG.info(f"Checking current XNAT archive for project {self.options.project}")
        if require_writable:
            test = self._dir_writable
        else:
            test = self._dir_exists
        
        test(self.options.xnat_archive, "XNAT archive folder")
        test(self.src_proj_dir, "XNAT project archive folder")
        
        if os.path.islink(self.src_proj_dir):
            raise MigrateError(f"Project archive folder: {self.src_proj_dir} is already linked to another folder")

        self.data_size = self._dir_size(self.src_proj_dir)
        data_size_mb = float(self.data_size) / 1048576
        LOG.info(f" - Total data size in archive: {data_size_mb:.1f} Mb")

    def _check_cps_folder(self):
        """
        Check that the CPS folder is writable and the destination folder exists

        FIXME can we check if there is room for data?
        """
        LOG.info(f"Checking destination CPS folder")
        self._dir_writable(self.options.rdrive, "CPS folder")
        self._dir_writable(self.dest_archive_dir, "Destination CPS folder for XNAT data")

    def _check_backup_folder(self):
        """
        Check that the backup folder is writable and the dest dir does not yet exist
        """
        LOG.info(f"Checking XNAT backup CPS folder")
        self._dir_writable(self.options.xnat_backup, "XNAT backup folder")

        self._dir_not_exists(self.dest_backup_dir, "Destination backup folder for XNAT data")
        LOG.info(f" - Destination backup folder for XNAT data: {self.dest_backup_dir}")

    def _init_cps_folder(self):
        """
        Initialize the CPS folder for XNAT
        """
        LOG.info(f"Initializing CPS folder for XNAT")
        self._dir_writable(self.options.rdrive, "CPS folder")
        self._dir_not_exists(self.dest_archive_dir, "Destination CPS folder for XNAT data")
    
        os.mkdir(self.dest_archive_dir)
        LOG.info(f" - Folder created")

        readme_fname = os.path.join(self.dest_archive_dir, README_FNAME)
        with open(readme_fname, "w") as f:
            f.write(README_CONTENTS)
        LOG.info(f" - Created README file: {readme_fname}")

        warning_fname = os.path.join(self.dest_archive_dir, WARNING_FNAME)
        with open(warning_fname, "w") as f:
            f.write(README_CONTENTS)
        LOG.info(f" - Created warning file: {warning_fname}")

    def _backup_data(self):
        LOG.info(f"Backing up XNAT project data")
        self._sync(self.src_proj_dir, self.dest_backup_dir)

    def _update_data(self):
        LOG.info(f"Synchronizing XNAT project data with destination folder")
        self._sync(self.src_proj_dir, self.dest_proj_dir)

    def _create_link(self):
        LOG.info(f"Replacing XNAT project archive with link")
        self._confirm()
        shutil.rmtree(self.src_proj_dir)
        LOG.info(f" - Removed {self.src_proj_dir}")
        os.symlink(self.dest_proj_dir, self.src_proj_dir)
        LOG.info(f" - Created link to {self.dest_proj_dir}")

    def _confirm(self):
        resp = input(" - Confirm by typing 'yes' - any other response will not migrate project: ")
        if resp.strip() != "yes":
            raise MigrateError("User did not confirm")

    def _dir_writable(self, path, desc):
        LOG.info(f" - {desc}: {path}")
        if not os.path.isdir(path):
            raise MigrateError(f"{desc}: {path} - not found or not a directory")

        if not os.access(path, os.W_OK):
            raise MigrateError(f"{desc}: {path} - not writable by current user")
    
    def _dir_not_exists(self, path, desc):
        LOG.info(f" - {desc}: {path}")
        if os.path.exists(path):
            raise MigrateError(f"{desc}: {path} - already exists")

    def _dir_exists(self, path, desc):
        LOG.info(f" - {desc}: {path}")
        if not os.path.isdir(path):
            raise MigrateError(f"{desc}: {path} - not found or not a directory")
            
        if not os.access(path, os.R_OK):
            raise MigrateError(f"{desc}: {path} - not readable by current user")

    def _sync(self, src, dest):
        LOG.info(f" - Copying data from {src}")
        LOG.info(f" - Copying data to {dest}")
        root, leaf = os.path.split(dest)
        assert leaf == os.path.basename(src)
        subprocess.call(["rsync", "-a", src, root])
        LOG.info(f" - Data copied")
        copy_data_size = self._dir_size(dest)
        if copy_data_size != self.data_size:
            raise MigrateError(f"Destination data size {copy_data_size} does not match source data size {self.data_size}")
        else:
            LOG.info(f" - Size matches source: {copy_data_size}")

    def _dir_size(self, dir):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        return total_size
