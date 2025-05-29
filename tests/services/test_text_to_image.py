import pytest
import sys
import os
import json 
from ai.microservice.base_service import load_services, get_service  # Assumed function
from ai import PAIALogger, PAIAConfig

PAIAConfig().update(PAIAConfig().base_dir+'/config.json')
PAIALogger().update({"level":"DEBUG"})

class MockRequest():
    def __init__(self, data:json = None):
        self.mockData = data

    def get(self, name, default:str = None):
        return self.mockData.get(name,default)

load_services()


def mock_query(mock_data:json,mock_service:str):    
    service = get_service(mock_service)  
    mock_request_image = MockRequest(mock_data)
    
    yield lambda: result
    result =  yield from service.process(mock_request_image)
    assert result["type"] == "image"

def test_text_to_image(tmp_path):
    log_dir = tmp_path / "logs"
    os.mkdir(str(log_dir))
    with open(os.path.join(str(log_dir),"app.log"), 'w', encoding='utf-8') as f:
        f.write("kunda")
    mock_query(mock_data={"text":"Test mock","height":"256","width":"256","output_path":str(log_dir),"stream":False},mock_service="text-to-image")

def test_text_to_image_empty_input():
    mock_query({"text": "","stream":False},mock_service="text-to-image")

def test_text_to_image_invalid_image_size():
    mock_query({"text": "Test","stream":False,"height":"asdasd"},mock_service="text-to-image")
