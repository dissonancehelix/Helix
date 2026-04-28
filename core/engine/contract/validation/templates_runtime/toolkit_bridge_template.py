class ToolkitBridge:
    def run(self, payload):
        result = toolkit.process(payload)
        return result
