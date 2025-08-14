import logging
import os


def pytest_configure(config):
    """
    Configures logging for the entire test suite run.
    This hook runs once before any tests are collected.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    logs_folder = os.path.join(project_root, 'logs')
    os.makedirs(logs_folder, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=os.path.join(logs_folder, 'test_run.log'),
        filemode='w'
    )