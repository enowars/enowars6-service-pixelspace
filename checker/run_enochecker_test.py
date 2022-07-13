import os

os.environ['ENOCHECKER_TEST_CHECKER_ADDRESS']="localhost"
os.environ['ENOCHECKER_TEST_CHECKER_PORT']="8000"
os.environ['ENOCHECKER_TEST_SERVICE_ADDRESS']="10.1.1.1"
os.system("enochecker_test")