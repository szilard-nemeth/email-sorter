import os

from pythoncommons.constants import ExecutionMode
from pythoncommons.logging_setup import SimpleLoggingSetupConfig, SimpleLoggingSetup
from pythoncommons.os_utils import OsUtils
from pythoncommons.project_utils import ProjectRootDeterminationStrategy, ProjectUtils

import logging

from emailsorter.core.constants import EMAIL_SORTER_MODULE_NAME
from emailsorter.core.common import EmailSorterEnvVar

LOG = logging.getLogger(__name__)


class Initializer:
    @staticmethod
    def configure_logging(debug_enabled=False, trace_enabled=False):
        logging_config: SimpleLoggingSetupConfig = SimpleLoggingSetup.init_logger(
            project_name=EMAIL_SORTER_MODULE_NAME,
            logger_name_prefix=EMAIL_SORTER_MODULE_NAME,
            execution_mode=ExecutionMode.PRODUCTION,
            console_debug=debug_enabled,
            trace=trace_enabled,
            verbose_git_log=False,
            with_trace_level=True,
        )
        LOG.info("Logging to files: %s", logging_config.log_file_paths)
        return logging_config

    @staticmethod
    def configure_loggers(args):
        googleapiwrapper_level = getattr(args, "logging_level_googleapiwrapper", None)
        pythoncommons_level = getattr(args, "logging_level_pythoncommons", None)

        if googleapiwrapper_level:
            logging.getLogger("googleapiwrapper").setLevel(googleapiwrapper_level)
        if pythoncommons_level:
            logging.getLogger("pythoncommons").setLevel(pythoncommons_level)

    @staticmethod
    def setup_dirs(execution_mode: ExecutionMode = ExecutionMode.PRODUCTION):
        # TODO move this method to pythoncommons?
        strategy = None
        if execution_mode == ExecutionMode.PRODUCTION:
            strategy = ProjectRootDeterminationStrategy.SYS_PATH
        elif execution_mode == ExecutionMode.TEST:
            strategy = ProjectRootDeterminationStrategy.COMMON_FILE
        if EmailSorterEnvVar.PROJECT_DETERMINATION_STRATEGY.value in os.environ:
            env_value = OsUtils.get_env_value(EmailSorterEnvVar.PROJECT_DETERMINATION_STRATEGY.value)
            LOG.info("Found specified project root determination strategy from env var: %s", env_value)
            strategy = ProjectRootDeterminationStrategy[env_value.upper()]
        if not strategy:
            raise ValueError("Unknown project root determination strategy!")
        LOG.info("Project root determination strategy is: %s", strategy)
        ProjectUtils.project_root_determine_strategy = strategy
        EmailSorterConfig.PROJECT_OUT_ROOT = ProjectUtils.get_output_basedir(
            EMAIL_SORTER_MODULE_NAME, project_name_hint=EMAIL_SORTER_MODULE_NAME
        )
