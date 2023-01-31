# connect_from_win_to_chkp

Script runs Checkpoint Endpoint Security client from the Windows CLI.    
Command line utility "trac"  is used for calling client with required arguments.  
The script returns JSON for transmission to Zabbix Monitoring system.  
The main purpose is emulate user connect for monitoring.  

# It is necessary to fill in config.ini.

- site: _The name of the Checkpoint site._
- path: _C:\Program Files (x86)\CheckPoint\Endpoint Connect\ The path where the client is installed_
- username : _Username_
- password : _Password_
- otp_hash : _OTP hash for 2FA authentication_
