import argparse

class ArgumentParser(argparse.ArgumentParser):
    """
    ArgumentParser for xnat-cps options
    """

    def __init__(self, **kwargs):
        argparse.ArgumentParser.__init__(self, prog="xnat-cps", add_help=False, **kwargs)

        group = self.add_argument_group("Main Options")
        group.add_argument("command", help="Command to run", choices=["migrate",])
        group.add_argument("--project", help="XNAT project ID", required=True)
        group.add_argument("--rdrive", help="Path the CPS storage folder", required=True)
        group.add_argument("--xnat-archive", help="Path the XNAT archive folder (note this is not the same as XNAT_HOME)", required=True)
        group.add_argument("--xnat-backup", help="Path to folder where a backup of project archive will be stored - defaults to $HOME/xnat_backup/")
        group.add_argument("--use-rsync", help="Set up migration for RSYNC (copy) of XNAT data to CPS rather than symbolic link", action="store_true", default=False)

