# pip install pyftpdlib
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import ThreadedFTPServer
import os
import ConfigParser

cf = ConfigParser.ConfigParser()
cf.read('server.conf')
root_path = cf.get('path', 'root_path')
server_get_path = cf.get('path', 'server_get_path')
server_put_path = cf.get('path', 'server_put_path')
host = cf.get('address', 'host')
port = cf.getint('address', 'port')
username = cf.get('account', 'username')
password = cf.get('account', 'password')

if not os.path.exists(root_path):
    os.mkdir(root_path)
if not os.path.exists(server_get_path):
    os.mkdir(server_get_path)
if not os.path.exists(server_put_path):
    os.mkdir(server_put_path)

def main():
    authorizer = DummyAuthorizer()
    authorizer.add_user(username, password, root_path, perm='elradfmwM')
    authorizer.add_anonymous(os.getcwd())

    handler = FTPHandler
    handler.authorizer = authorizer

    handler.banner = "welcom to ftp"

    address = (host, port)
    server = ThreadedFTPServer(address, handler)

    server.max_cons = 256
    server.max_cons_per_ip = 5

    server.serve_forever()

if __name__ == '__main__':
    main()
