def enum(**enums):
    return type('Enum', (), enums)

MODES=enum()