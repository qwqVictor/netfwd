import hashlib
import logging
import argparse
import client
import utils
import models

CRITICAL_KEYS = {
    "server": str,
    "token": str,
    "instances": [{
        "mode": int,
        "remote_port": int
    }]
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

    lastcolon = config['server'].rfind(':')
    assert lastcolon != -1, 'port must be set'

    server = config['server'][:lastcolon]
    port = int(config['server'][lastcolon+1:])
    assert port > 0 and port < 65536, 'port must be in range (0, 65535]'

    token = hashlib.md5(config['token'].encode('utf-8')).digest()

    child_list = []

    for instance in config.get('instances', []):
        instance: dict
        try:
            mode = getattr(models.tunnelType, instance['mode'])
        except:
            logging.warn("Config parse warning: instance %s has incorrect mode." % (str(instance)))
            continue

        remote_port = instance.get('remote_port')
        try:
            assert remote_port and remote_port > 0 and remote_port < 65536
        except:
            logging.warn("Config parse warning: instance %s port not be in range (0, 65535]" % (str(instance)))
            continue

        domain = utils.punycode_encode(instance.get('domain', ''))
        if mode == models.tunnelType.http or mode == models.tunnelType.ssl:
            try:
                assert domain != ''
            except:
                logging.warn("Config parse warning: instance %s domain not set while using SLB" % (str(instance)))

        arg_proc = {
            'host': str(instance.get('local_host')),
            'port': int(str('0' if instance.get('local_port') is None else instance.get('local_port'))),
            'remote_port': remote_port,
            'mode': mode,
            'token': token,
            'domain': domain,
            'static': instance.get('static'),
            'bufsize': int(config.get('bufsize', 1024))
        }

        child_list.append(client.new_proc(server, port, token, arg_proc))
    
    logging.info("Netfwd client connecting to server [%s]:%d" % (server, port))
    logging.info("Copyright (C) 2021 Victor Huang <i@qwq.ren>")
    logging.info("")
    logging.info("Added %d child services." % len(child_list))

    while child_list:
        for child in child_list:
            if not child.is_alive():
                child_list.remove(child)

if __name__ == "__main__":
    main(parser.parse_args())