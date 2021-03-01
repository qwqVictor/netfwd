import hashlib
import logging
import argparse
import server
import utils

CRITICAL_KEYS = {
    "port": int,
}

parser = argparse.ArgumentParser(description="netfwd client")
parser.add_argument('-c', '--config', help='specify config path', default='config.yml')

def main(args):

    config = utils.parse_yaml(args.config)
    assert config, 'without config I cannot do anything!'

    if config.get('debug'):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    port = int(config['port'])
    assert port > 0 and port < 65536, 'port must be in range (0, 65535]'

    host: str
    host = config.get('host', '0.0.0.0')

    tokens: "list[str]"
    tokens = config.get('tokens', [])

    valid_tokens: "list[bytes]"
    valid_tokens = []
    for token in tokens:
        data = hashlib.md5(token.encode('utf-8')).digest()
        valid_tokens.append(data)

    loopserver = server.LoopServer(port, host, valid_tokens=valid_tokens, bufsize=config.get('bufsize', 1024))
    loopserver.run()

if __name__ == "__main__":
    main(parser.parse_args())
