import logging
import snowflake_builder.utilities.datetime_utilities as datetime_utilities
import snowflake_builder.utilities.string_utilities as string_utilities
from datetime import datetime


class SnowflakeCICDResult:
    """
    A class that records the execution result of a single CI/CD script executed during a CI/CD run.
    """
    def __init__(self, script_directory: str, script_name: str, start_dt: datetime, end_dt: datetime, success: bool):
        """
        Create an object to record the result of executing a single CI/CD script.

        Parameters
        ----------
        script_directory : str
            The name of the directory containing the script file.
        script_name : str
            The name of the script file.
        start_dt : datetime
            The UTC time that the script execution started.
        end_dt :
            The UTC time that the script execution finished.
        success : bool
            True if the script was executed successfully.
        """
        self.script_directory = script_directory
        self.script_name = script_name
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.duration = end_dt - start_dt
        self.success = success

    def to_summary_list(self) -> list[str]:
        """
        Generate a list containing the internal values for formatting into a presentation table.

        Returns
        -------
        list[str]
            A list containing formatted string values.
        """
        return [
            self.script_directory, self.script_name, self.start_dt.strftime('%H:%M:%S.%f'),
            datetime_utilities.format_timedelta(self.duration), 'OK' if self.success else 'FAILED'
        ]


class SnowflakeCICDTracker:
    """
    A class that records the execution results of a set of CI/CD scripts executed during a CI/CD run.
    """
    def __init__(self):
        """
        Create an object to record the results of executing a set of CI/CD scripts during a CI/CD run.
        """
        self.execution_log = []

    def append_execution(self,
                         script_directory: str, script_name: str, start_dt: datetime, end_dt: datetime, success: bool):
        """
        Append the results of executing a single CI/CD script.

        Parameters
        ----------
        script_directory : str
            The name of the directory containing the script file.
        script_name : str
            The name of the script file.
        start_dt : datetime
            The UTC time that the script execution started.
        end_dt :
            The UTC time that the script execution finished.
        success : bool
            True if the script was executed successfully.

        Returns
        -------
        None
        """
        result = SnowflakeCICDResult(script_directory, script_name, start_dt, end_dt, success)
        self.execution_log.append(result)

    def get_summary(self) -> list[str]:
        """
        Get a tabular version of the execution results for display/presentation purposes.

        Returns
        -------
        list[str]
            A tabular list of execution results where each value in the list is a line of text with a header included.
        """
        rows = []
        titles = ['Directory', 'Script', 'Started', 'Duration', 'Result']
        rows.append(titles)
        for result in self.execution_log:
            row = result.to_summary_list()
            rows.append(row)
        return string_utilities.get_text_table(rows)

    def output_summary(self):
        """
        Print to the console a tabular version of the execution results for display/presentation purposes.

        Returns
        -------
        None
        """
        lines = self.get_summary()
        logging.info('--------------------------------------------------------------------------------')
        logging.info('Summary:')
        for line in lines:
            logging.info(line)
        logging.info('--------------------------------------------------------------------------------')
