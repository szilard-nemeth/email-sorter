from googleapiwrapper.gmail_cache import CachingStrategyType

from emailsorter.core.common import CommandType
from emailsorter.core.common import PROJECT_NAME, SECRET_PROJECTS_DIR
from googleapiwrapper.common import ServiceType
from googleapiwrapper.gmail_api import GmailWrapper
from googleapiwrapper.google_auth import GoogleApiAuthorizer
from pythoncommons.file_utils import FileUtils
from pythoncommons.os_utils import OsUtils
from pythoncommons.project_utils import ProjectUtils


class EmailSorterContext:
    def __init__(self, use_cache: bool, account_email: str):
        # Set up dirs
        self.output_dir = ProjectUtils.get_output_child_dir(CommandType.EMAIL_SORTER.output_dir_name)
        self.session_dir = ProjectUtils.get_session_dir_under_child_dir(FileUtils.basename(self.output_dir))
        self.email_cache_dir = FileUtils.join_path(self.output_dir, "email_cache")

        self.account_email: str = account_email
        self.full_cmd: str = OsUtils.determine_full_command_filtered(filter_password=True)

        # Set up Gmail API objects
        self.authorizer = GoogleApiAuthorizer(
            ServiceType.GMAIL,
            project_name=PROJECT_NAME,
            secret_basedir=SECRET_PROJECTS_DIR,
            account_email=self.account_email,
        )
        caching_strategy = CachingStrategyType.FILESYSTEM_CACHE_STRATEGY if use_cache else CachingStrategyType.NO_CACHE
        self.gmail_wrapper = GmailWrapper(self.authorizer, cache_strategy_type=caching_strategy, output_basedir=self.email_cache_dir)

    @staticmethod
    def _get_attribute(args, attr_name, default=None):
        val = getattr(args, attr_name)
        if not val:
            return default
        return val

    def __str__(self):
        return (
            f"Full command was: {self.full_cmd}\n"
            f"Account email: {self.account_email}\n"
            f"Email cache dir: {self.email_cache_dir}\n"
            f"Session dir: {self.session_dir}\n"
        )
