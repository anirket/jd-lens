from enum import Enum


class Model(Enum):
    ANTHROPIC = 'anthropic'
    GROQ = 'groq'

all_models = {
    Model.ANTHROPIC: {
       'haiku': {
           'modelId': "claude-haiku-5-5",
           'tokens': {"in": 0.10, "out": 0.50}
       },
       'sonet': {
           'modelId': 'claude-sonnet-5-5',
           'tokens': {"in": 2.00, "out": 10.00}
       },
       'opus': {
           'modelId': 'claude-opus-5-5',
           'tokens': {"in": 4.00, "out": 20.00}
       }
    },
    Model.GROQ: {
        'openai': {
            'modelId': "openai/gpt-oss-20b",
            'tokens': {"in": 0.075, "out": 0.30}
        }
    }
}