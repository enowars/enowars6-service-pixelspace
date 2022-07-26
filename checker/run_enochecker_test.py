import os

os.environ['ENOCHECKER_TEST_CHECKER_ADDRESS']="localhost"
os.environ['ENOCHECKER_TEST_CHECKER_PORT']="8000"
os.environ['ENOCHECKER_TEST_SERVICE_ADDRESS']="192.168.229.128"
os.system("enochecker_test")