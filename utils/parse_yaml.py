import yaml

def parse_yaml(filename: str, critical_keys: "dict[str, any]"={}):
    config = None
    try:
        with open(filename, 'r') as ymlFile:
            config = yaml.load(ymlFile, Loader=yaml.FullLoader)
            for key in critical_keys:
                if key not in config:
                    return None
            
        return config
    except Exception as e:
        raise e