# Gunicorn setting

workers=10
worker_class='gevent'
worker_connections=1000
keep_alive=5


access_logfile='/var/log/access.log'
error_logfile='/var/log/error.log'

reload=False
