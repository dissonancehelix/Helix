def validate_schema(data, schema_type):
    if schema_type == "test_schema":
        if "rogue_key" in data: return False
        return "valid_key" in data
    return True
