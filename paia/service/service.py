from paia import PAIAConfig, PAIALogger

# Service interface / abstract class 
class PAIAService:
    def __init__(self):
        self.config = PAIAConfig()
        self.logger = PAIALogger()

    def process(self, query):
        raise NotImplementedError("Subclasses must implement process method")

