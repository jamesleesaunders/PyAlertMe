import logging
 
def initialize_logger():
    logger = logging.getLogger('pihive')
    logger.setLevel(logging.DEBUG)
    
    # Speficy log message format     
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s: %(message)s')

    # create console handler and set level to info
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
 
    # create debug file handler and set level to debug
    fh = logging.FileHandler("debug.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
