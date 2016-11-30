
import ftplib
import socket
import ConfigParser
import time
import os
from multiprocessing import Process

cf = ConfigParser.ConfigParser()
cf.read('client.conf')
ftp_put_path = cf.get('path', 'ftp_put_path')
ftp_get_path = cf.get('path', 'ftp_get_path')
ftp_root_path = cf.get('path', 'ftp_root_path')
local_root_path = cf.get('path', 'local_root_path')
local_put_path = cf.get('path', 'local_put_path')
local_get_path = cf.get('path', 'local_get_path')
host = cf.get('address', 'ftp_host')
port = cf.getint('address', 'ftp_port')
reconnect_interval = cf.getint('time', 'reconnect_interval')
send_receive_interval = cf.getint('time', 'send_receive_interval')
timeout = cf.getint('time', 'ftp_timeout')
username = cf.get('account', 'username')
password = cf.get('account', 'password')

if not os.path.exists(local_root_path):
    os.mkdir(local_root_path)
if not os.path.exists(local_get_path):
    os.mkdir(local_get_path)
if not os.path.exists(local_put_path):
    os.mkdir(local_put_path)

def get_dir_images(outputDir):
    files = []
    if os.path.exists(outputDir):
        fs = os.listdir(outputDir)
        for item in fs:
            fullpath = os.path.join(outputDir, item)
            if os.path.isfile(fullpath):
                files.append(fullpath)
    return files

def deletefile(filename):
    if os.path.exists(filename):
        os.remove(filename)

def sendfile(ftpObj, filepath):
    result = False
    if not os.path.isfile(filepath):
        return result

    errormsg = 'send ' + filepath + ' failed. '

    try:
        with open(filepath, 'rb') as fhandle:
            ftpObj.storbinary('STOR %s' % os.path.basename(filepath), fhandle)
            result = True
    except socket.error, e:
        print errormsg + 'socket.error:', e
        result = False
    except IOError, e:
        print errormsg + 'IOError:', e
        result = False
    except ftplib.Error, e:
        print errormsg + 'ftplib.Error:', e
        result = False
    except EOFError:
        print errormsg + 'EOFError.'
        result = False

    return result

def send_all_files(ftpObj, fromDir):
    result = True
    files = get_dir_images(fromDir)
    for item in files:
        sendfile_result = sendfile(ftpObj, item)
        if sendfile_result:
            deletefile(item)
        else:
            result = False
            break

    return result

def receive_all_files(ftpObj, saveDir):
    result = True
    files = ftpObj.nlst()
    for item in files:
        local_file_path = os.path.join(saveDir, item)
        errormsg = 'retr ' + item + ' failed. '
        try:
            with open(local_file_path, 'wb') as fhandle:
                ftpObj.retrbinary('RETR %s' % os.path.basename(item), fhandle.write)
                ftpObj.delete(item)
        except socket.error, e:
            print (errormsg + 'socket.error:'), e
            deletefile(local_file_path)
            result = False
            break
        except IOError, e:
            print (errormsg + 'IOError:'), e
            deletefile(local_file_path)
            result = False
            break
        except ftplib.Error, e:
            print (errormsg + 'ftplib.Error:'), e
            deletefile(local_file_path)
            result = False
            break
        except EOFError:
            print (errormsg + 'EOFError.')
            deletefile(local_file_path)
            result = False
            break

    return result

def do_send(filepath):
    first_running = True
    ftp = ftplib.FTP()
    while True:
        if not first_running:
            time.sleep(reconnect_interval)
            first_running = False
        print 'start ftp for sending.'
        try:
            ftp.connect(host, port, timeout)
            print 'Successful to connect for sending.'
        except (socket.error, socket.gaierror), e:
            print 'Failed to connect for sending:', e
            continue
        try:
            ftp.login(username, password)
        except ftplib.error_perm, e:
            print 'Username or password is invalid:', e
            break

        while True:
            time.sleep(send_receive_interval)
            try:
                ftp.cwd(ftp_get_path)
            except (ftplib.error_perm, socket.error, EOFError), e:
                print 'Failed to change get dir:', e
                break

            sendfiles_result = send_all_files(ftp, filepath)
            if not sendfiles_result:
                print 'send_all_files failed.'
                break

    ftp.quit()

def do_receive(ftppath):
    first_running = True
    ftp = ftplib.FTP()
    while True:
        if not first_running:
            time.sleep(reconnect_interval)
            first_running = False
        print 'start ftp for receiving'
        try:
            ftp.connect(host, port, timeout)
            print 'Successful to connect for receiving'
        except (socket.error, socket.gaierror), e:
            print 'Failed to connect  for receiving:', e
            continue
        try:
            ftp.login(username, password)
        except ftplib.error_perm, e:
            print 'Username or password is invalid:', e
            break

        while True:
            time.sleep(send_receive_interval)
            try:
                ftp.cwd(ftp_put_path)
            except (ftplib.error_perm, socket.error, EOFError), e:
                print 'Failed to change put dir:', e
                break

            recv_result = receive_all_files(ftp, ftppath)
            if not recv_result:
                print 'recerve_all_files failed!!!'
                break

    ftp.quit()

def multiprocess_run():
    process_send = Process(target=do_send, args=(local_put_path,))
    process_receive = Process(target=do_receive, args=(local_get_path, ))

    process_send.start()
    process_receive.start()

    process_send.join()
    process_receive.join()

def single_thread_run():
    while True:
        ftp = ftplib.FTP()
        time.sleep(reconnect_interval)
        print 'start ftp'
        try:
            ftp.connect(host, port, timeout)
            print 'Successful to connect'
        except (socket.error, socket.gaierror), e:
            print 'Failed to connect:', e
            continue
        try:
            ftp.login(username, password)
        except ftplib.error_perm, e:
            print 'Username or password is invalid:', e
            break

        while True:
            time.sleep(send_receive_interval)
            # send files
            try:
                ftp.cwd(ftp_get_path)
            except (ftplib.error_perm, socket.error, EOFError), e:
                print 'Failed to change get dir:', e
                break

            sendfiles_result = send_all_files(ftp, local_put_path)
            if not sendfiles_result:
                print 'send_all_files failed.'
                break

            # receive files
            try:
                ftp.cwd(ftp_put_path)
            except (ftplib.error_perm, socket.error, EOFError), e:
                print 'Failed to change put dir:', e
                break

            recv_result = receive_all_files(ftp, local_get_path)
            if not recv_result:
                print 'recerve_all_files failed!!!'
                break

    ftp.quit()


if __name__ == '__main__':
    print 'runing'
    multiprocess_run()  # multi processing
#    single_thread_run()  # single threading




