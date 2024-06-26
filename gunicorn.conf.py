bind = "0.0.0.0:8000"
workers = 3
# Access log - records incoming HTTP requests
accesslog = "/root/vpn_site/log/gunicorn.access.log"
# Error log - records Gunicorn server goings-on
errorlog = "/root/vpn_site/log/gunicorn.error.log"
# Whether to send Django output to the error log 
capture_output = True
# How verbose the Gunicorn error logs should be 
loglevel = "info"