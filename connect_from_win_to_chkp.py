# -*- coding: utf-8 -*-

import pyotp
#pip install pyotp # lib for 2FA auth
import json
from subprocess import run, STDOUT, PIPE, CalledProcessError 
import time
import configparser

class CheckPointConnect():

    def __init__(self, site_info):
        # Cred and otp hash
        self.user = checkpoint_args['username']
        self.password = checkpoint_args['password']
        self.otp_hash = checkpoint_args['otp_hash']
        # Checkpoint site information
        self.site_name = checkpoint_args['site']
        self.path_to_client = checkpoint_args['path']

    @staticmethod        
    # get totp value from hash for 2FA
    def get_totp_value_from_otp_hash(otp_hash):
        totp = pyotp.TOTP(otp_hash)
        return totp.now()

    @staticmethod        
    # convert info status in dict
    def convert_info_status_to_dict(output):
        summury = []
        data = output.strip().split('\n')
        for line in data:
            if line.strip().startswith('status'):
                status, val = line.strip().split(':')
                info = dict([(status.strip(), val.strip())])
                return info
            elif len(line) == 0:
                data.remove(line)
            else:
                summury.append(line)
        x = ', '.join(summury)
        info = dict([('status', x)])
        return info

    @staticmethod        
    # convert connection status in dict
    def convert_connection_status_to_dict(output):
        data = output.strip().split('\n')
        for line in data:
            if line.startswith('Connection was successfully established'):
                info = dict([('connection_check', line.strip())])
                return info
            elif line.startswith('Connection could not be established'):
                try:
                    _, con_error = line.strip().split(':')
                    info = dict([('connection_check', con_error.strip())])
                    return info
                except ValueError as error:
                    info = dict([('connection_check', line)])
                    return info
        return {'connection_check': 'Unknow error'}

    # run connect with  checkpoint client
    def connect_to_checkpoint_site(self):
        try:
            # Get totp value for auth
            totp_value = self.get_totp_value_from_otp_hash(self.otp_hash)
            # Create 2fa password for checkpoint
            full_password = self.password + totp_value
            # run connection to site
            connect = run(
                'trac connect -s "{}"  -u {} -p "{}"'.format(self.site_name, 
                                                                self.user, 
                                                                full_password),
                cwd=self.path_to_client, 
                capture_output=True,
                text=True, 
                shell=True,
                check=True,
                encoding='cp866')
            # check error in returncode
            if connect.returncode == 0:
                connect_status = self.convert_connection_status_to_dict(connect.stdout)
                return connect_status
            # for unix only
            elif connect.returncode < 0:
                info_status = dict([('status', 
                                    'Child was terminated by signal')])
                return info_status
            else:
                return connect
        # exception for worng path
        except OSError as error:
            text_info = self.convert_connection_status_to_dict(str(error))
            text_info.update({'status': str(error)})
            return text_info
        # exception for returncode > 1
        except CalledProcessError as error:
            text_info = self.convert_connection_status_to_dict(str(error))
            text_info.update({'status': str(error)})
            return text_info

    # create string to info about checkpoint connection
    def info_about_connect_to_checkpoint(self):
        try:
            info = run(
                'trac info -s {}'.format(self.site_name),
                cwd=self.path_to_client, 
                capture_output=True,
                text=True, 
                shell=True,
                check=True,
                encoding='cp866')
            # check error in returncode
            if info.returncode == 0:
                info_status = self.convert_info_status_to_dict(info.stdout)
                return info_status
            # for unix only
            elif info.returncode < 0:
                info_status = dict([('status', 
                                    'Child was terminated by signal')])
                return info_status
            else:
                info_status = self.convert_info_status_to_dict(info.stderr)
                return info_status
        # exception for worng path
        except OSError as error:
            text = dict([('status',str(error))])
            return text
        # exception for returncode > 1
        except CalledProcessError as error:
            text = dict([('status',str(error))])
            return text

    # disconnect checkpoint connection
    def disconnect_from_checkpoint_site(self):
        try:
            disc = run(
                'trac disconnect',
                cwd=self.path_to_client, 
                capture_output=True,
                text=True, 
                shell=True,
                check=True,
                encoding='cp866')
            # check error in returncode
            if disc.returncode == 0:
                disc_status = disc.stdout
                disc_info = dict([('status',str(disc_status.strip()))])
                return disc_info
            elif disc.returncode < 0:
                disc_info = dict([('status', 
                                'Child was terminated by signal')])
                return disc_info
        # exception for worng path
        except OSError as error:
            text = dict([('status',str(error))])
            return text
        # exception for returncode > 1
        except CalledProcessError as error:
            text = dict([('status',str(error))])
            return text

class Timer:
    timers = {}

    def __init__(self, name='time'):
        self._start_time = None
        self.name = name
        # Add new named timers to dictionary of timers
        if name:
            self.timers.setdefault(name, 0)
    
    # start a new timer
    def start(self):
        self._start_time = time.perf_counter()
    
    # Stop the timer, and report the elapsed time
    def stop(self):
        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        if self.name:
            self.timers[self.name] += elapsed_time
        return elapsed_time

def main():
    # start count time
    t = Timer()
    t.start()
    # create class object
    checkpoint = CheckPointConnect(checkpoint_args)
    # get information about current connection status
    info = checkpoint.info_about_connect_to_checkpoint()
    #print(info)
    if info['status'] == 'Connected' or info['status'] == 'Connecting':
        # disconnect from site
        disc_info = checkpoint.disconnect_from_checkpoint_site()
        # connect to site
        connect_to_site = checkpoint.connect_to_checkpoint_site()
    elif info['status'] == 'Idle':
        # connect to site
        connect_to_site = checkpoint.connect_to_checkpoint_site()  
    else:
        # connect to site
        connect_to_site = checkpoint.connect_to_checkpoint_site()
    # stop count time
    t.stop()
    # update dict with timer
    connect_to_site.update(Timer.timers)
    json_data = json.dumps(connect_to_site, 
                            ensure_ascii=False)
    return json_data

if __name__ == '__main__':

    # Information about checkpoint site and client
    config = configparser.ConfigParser()
    config.read('config.ini')
    checkpoint_args = {
            'username': config.get('checkpoint_args', 'username'),
            'password': config.get('checkpoint_args', 'password'),
            'otp_hash': config.get('checkpoint_args', 'otp_hash'),
            'site': config.get('checkpoint_args', 'site'),
            'path': config.get('checkpoint_args', 'path')
            }
            
    print(main())