class Adapter:
    toolkit = "<TOOLKIT_NAME>"
    substrate = "<SUBSTRATE>"

    def execute(self, payload):
        toolkit_result = ToolkitBridge().run(payload)
        normalized = self.normalize(toolkit_result)
        return normalized
        
    def normalize(self, result):
        # Implementation
        return result
