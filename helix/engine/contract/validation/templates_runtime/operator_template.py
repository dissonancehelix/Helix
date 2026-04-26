class Operator:
    name = "<OPERATOR_NAME>"
    substrate = "<SUBSTRATE>"

    def run(self, input_payload):
        validated = self.validate(input_payload)
        result = Adapter().execute(validated)
        artifact = ArtifactBuilder().build(result)
        return artifact
    
    def validate(self, payload):
        # Implementation
        return payload
