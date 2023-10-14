
import pprint
import logging

import opts

 
# Create and configure logger
logging.basicConfig(filename=opts.log_file_path,
                    # format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                    format='[%(asctime)s] - %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filemode='w')
 
# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)

def log(msg):
    # logger.debug(pprint.pformat(msg))
    logger.debug(msg)

