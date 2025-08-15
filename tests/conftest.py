import sys
import os

# This file is automatically discovered by pytest.
# It modifies the Python path to ensure that the test files can find
# the project's source code, specifically the 'utilities' module.

# Determine the project root directory (which is one level up from the 'tests' directory)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
utilities_parent_dir = os.path.join(project_root, 'src', 'intelli_test')
if utilities_parent_dir not in sys.path:
    sys.path.insert(0, utilities_parent_dir)

