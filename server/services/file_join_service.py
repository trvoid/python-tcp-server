################################################################################
# Service implementations                                                      #
################################################################################

import sys, traceback, logging

################################################################################
# Constants                                                                    #
################################################################################

################################################################################
# Functions                                                                    #
################################################################################

def parse_request_body(request):
    file_a_length = int.from_bytes(request.body_data[0:4], byteorder='little')
    file_b_length = int.from_bytes(request.body_data[4:8], byteorder='little')
    
    start = 8
    end = start + file_a_length
    file_a_data_arr = request.body_data[start:end]
    file_a_text = file_a_data_arr.decode('utf-8')
    
    start = end
    end = start + file_b_length
    file_b_data_arr = request.body_data[start:end]
    file_b_text = file_b_data_arr.decode('utf-8')
    
    return file_a_text, file_b_text

def build_response_body(text_list):
    result = '^.^'.join(text_list)
    result_data = result.encode('utf-8')
       
    return result_data
        
################################################################################
# Classes                                                                      #
################################################################################

class FileJoinService:
    def __init__(self):
        self.logger = logging.getLogger()
        self.service_counter = 0
    
    def process(self, request):
        self.service_counter += 1
        
        result_data = None
        
        try:
            result_data = self.process_request_message(request, self.service_counter)
        except Exception as ex:
            self.logger.error(f'[request({request.request_id})] Exception occurred.')
            self.logger.error(traceback.format_exc())
            
            text_list = []
            result_data = build_response_body(text_list)
            
        return result_data
        
    def process_request_message(self, request, service_counter):
        text_list = parse_request_body(request)
        
        body_data = build_response_body(text_list)
        
        return body_data
