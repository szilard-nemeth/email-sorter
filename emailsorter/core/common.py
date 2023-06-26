from enum import Enum
from os.path import expanduser

from pythoncommons.file_utils import FileUtils

# Symlink names
LATEST_DATA_ZIP_LINK_NAME = "latest-command-data-zip"

PROJECT_NAME = "email-sorter"
SECRET_PROJECTS_DIR = FileUtils.join_path(expanduser("~"), ".secret", "projects", "nsziszy")


class EmailSorterConfig:
    PROJECT_OUT_ROOT = None


class EmailSorterEnvVar(Enum):
    PROJECT_DETERMINATION_STRATEGY = "PROJECT_DETERMINATION_STRATEGY"


class CommandType(Enum):
    EMAIL_SORTER = (PROJECT_NAME, PROJECT_NAME, True)

    # TODO Unify value vs. output_dir_name: Using both causes confusion
    def __init__(self, value, output_dir_name, session_based: bool, session_link_name: str = ""):
        self.real_name = value
        self.output_dir_name = output_dir_name
        self.session_based = session_based

        if session_link_name:
            self.session_link_name = session_link_name
        else:
            self.session_link_name = f"latest-session-{value}"

        self.log_link_name = f"latest-log-{value}"
        self.command_data_name = f"latest-command-data-{value}"
        self.command_data_zip_name: str = f"{LATEST_DATA_ZIP_LINK_NAME}-{value}"

    @staticmethod
    def from_str(val):
        allowed_values = {ct.name: ct for ct in CommandType}
        return CommandType._validate(val, allowed_values, "Invalid enum key")

    @staticmethod
    def by_real_name(val):
        allowed_values = {ct.real_name: ct for ct in CommandType}
        return CommandType._validate(val, allowed_values, "Invalid enum value by real name")

    @staticmethod
    def by_output_dir_name(val):
        allowed_values = {ct.output_dir_name: ct for ct in CommandType}
        return CommandType._validate(val, allowed_values, "Invalid enum value by output dir name")

    @classmethod
    def _validate(cls, val, allowed_values, err_message_prefix):
        if val in allowed_values:
            return allowed_values[val]
        else:
            raise ValueError("{}: {}".format(err_message_prefix, val))
