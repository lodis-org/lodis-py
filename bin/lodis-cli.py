import sys
import os
import argparse

from lodis import Lodis


def parse_config(config):
    d = {}
    with open(config) as f:
        for line in f.readlines():
            if not line:
                continue

            key, value = [i.strip() for i in line.split('=', 1)]
            d[key.lower()] = value

    return d['ip'], d['port']


def parse_args():
    p = argparse.ArgumentParser(description='lodis command client')

    p.add_argument('xxx', type=str, nargs='*', help='cmd key_name param1 param2 ...')
    p.add_argument(
        '-c', '--config', action='store', default='server.config', type=str, help='config path'
    )
    p.add_argument('-h', '--host', action='store', default=None, type=str, help='host')
    p.add_argument('-p', '--port', action='store', default=None, type=str, help='port')
    args = p.parse_args(sys.argv[1:])

    if not args.host and args.config:
        if not (isinstance(args.config, str) and os.path.exists(args.config)):
            raise TypeError(f'config must be path string - {args.config}')
        host, port = parse_config(args.config)
        args.host = host
        args.port = port

    return args


def main():
    args = parse_args()
    cmd = args.xxx[0]
    key_name = args.xxx[1]
    params = args.xxx[2:]

    lodis = Lodis(key_name, args.host, args.port)
    resp = getattr(lodis, cmd)(*params)
    value = resp.value
    print(value)


if __name__ == '__main__':
    main()
