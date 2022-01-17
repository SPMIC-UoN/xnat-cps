import argparse

class ArgumentParser(argparse.ArgumentParser):
    """
    ArgumentParser for xnat-cps options
    """

    def __init__(self, **kwargs):
        argparse.ArgumentParser.__init__(self, prog="xnat-cps", add_help=False, **kwargs)

        group = self.add_argument_group("Main Options")
        group.add_argument("command", help="Command to run", choices=["init", "sync", "backup", "link"])
        group.add_argument("--project", help="XNAT project ID", required=True)
        group.add_argument("--rdrive", help="Path the CPS storage folder", required=True)
        group.add_argument("--xnat-archive", help="Path the XNAT archive folder (note this is not the same as XNAT_HOME)", required=True)
        group.add_argument("--xnat-backup", help="Path to folder where a backup of project archive will be stored - if not specified no backup is performed")
        group.add_argument("--rdrive-xnat-dirname", help="Name of subdirectory of the CPS folder that will be used to store the XNAT archive", default="XNAT_DO_NOT_MODIFY")
        group.add_argument("--use-rsync", help="Set up migration for RSYNC (copy) of XNAT data to CPS rather than symbolic link", action="store_true", default=False)

