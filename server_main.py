################################################################################
# TCP socket server main.                                                      #
################################################################################

import sys, os, traceback, logging, logging.handlers
from tcp_server import TcpServer, ClientHandlerFactory
from services.file_join_service import FileJoinService
from tests.raise_error_service import RaiseErrorService

################################################################################
# Constants                                                                    #
################################################################################

################################################################################
# Functions                                                                    #
################################################################################

def init_logger(log_file_name, max_bytes, backup_count):
    log_dir_path = os.path.dirname(log_file_name)
    if not os.path.exists(log_dir_path):
        os.makedirs(log_dir_path)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('<%(asctime)s> <%(levelname)s> <%(filename)s:%(lineno)s> <%(message)s>')

    stream_hander = logging.StreamHandler()
    stream_hander.setFormatter(formatter)
    logger.addHandler(stream_hander)
    
    file_handler = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=max_bytes, backupCount=backup_count)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def print_usage(script_name):
    print(f'Usage: python {script_name} <service_name>')
    print('Available services:')
    for key in service_table.keys():
        print(f'        {key}')
    
################################################################################
# Configuration                                                                #
################################################################################

log_file_name = 'logs/server.log'
log_max_bytes = 10 * 1014 * 1024 # 10 MB
log_backup_count = 10

sw_version = '1.0.0'

port = 50000

service_table = {
        'file-join': FileJoinService(),
        'raise-error': RaiseErrorService()
    }
    
################################################################################
# Main                                                                         #
################################################################################

script_name = os.path.basename(sys.argv[0])

if len(sys.argv) != 2:
    print_usage(script_name)
    sys.exit(-1)

service_name = sys.argv[1]

if service_name not in service_table:
    print_usage(script_name)
    sys.exit(-1)
    
try:
    init_logger(log_file_name, log_max_bytes, log_backup_count)
    logger = logging.getLogger()
    logger.info(f'SW version: {sw_version}')
    
    tcp_server = TcpServer("svc-server")
    tcp_server.run(port, ClientHandlerFactory(service_table[service_name]))
except Exception as ex:
    logger.error(traceback.format_exc())
finally:
    logger.info('Server stopped.')
    logging.shutdown()
