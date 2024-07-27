import sys

def logIntoFile(path) -> None:
    """
    Logs all output to a file.

    Args:
        path (str): The path to the log file.
    """
    sys.stdout = open(path, 'a')
    sys.stderr = sys.stdout
