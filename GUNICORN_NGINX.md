# Configuration for Production Internet-Facing Web Service #

Install and configure [Gunicorn](https://docs.gunicorn.org/en/stable/) (Python WSGI HTTP Server for UNIX) to cater for multiple concurrent web-processes and worker processes running against the base Flask python web-app.
  
The Gunicorn HTTP service is fronted by NGINX.  
  
Supervisor can be used to monitor and control Gunicorn processes.  

<img style="float: left;" src="./doc/gunicorn_nginx.png">


These notes are tested on 
+ Ubuntu 18.04  
+ Python version 3.9.11
+ gunicorn-20.1.0  

## Gunicorn ##

Python WSGI HTTP Server for UNIX.  Allows multiple worker-threads and a standard web-framework interface for integration with NGINX
 
As the Flask application user (not root), install Gunicorn: 

+ set the Python environment.  
 
```
pip install gunicorn --upgrade
```

**Optional**: Run Gunicorn on port 8000 for testing 
 + use the `--preload` option to get log information for any errors
 + Set the necessary environment variables in advance - EG `export FLASK_LOG_DIR=./logs`


```
gunicorn -b localhost:8000 -w 4 app:app --preload
```

### Configure SYSTEMD Service for Gunicorn ###

Configure Gunicorn so that it is started and managed by the Linux Systemd service.

As `root` user create the following file:

```
/etc/systemd/system/flaskapp.service
```

and add the following contents:

```
[Unit]
Description=Gunicorn instance to serve Flask Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/flask-dash
Environment="PATH=/home/ubuntu/flask_app_env/bin"
Environment="FLASK_APP=flask-dash.py"

#Environment="POSTGRES_HOST=localhost"
#Environment="POSTGRES_PORT=5432"
#Environment="POSTGRES_DB=dbname"
#Environment="POSTGRES_USER=dbname_user"

Environment="FLASK_LOG_DIR=/home/ubuntu/flask-dash/logs"
Environment="GOOGLE_OAUTH_CLIENT_ID=<client-id>.apps.googleusercontent.com"
Environment="GOOGLE_OAUTH_CLIENT_SECRET=<Google API secret token>"

#Environment="MAIL_SERVER=smtp.googlemail.com"
#Environment="MAIL_PORT=587"
#Environment="MAIL_USE_TLS=1"

ExecStart=/home/ubuntu/flask_app_env/bin/gunicorn --workers 4 --bind unix:flask-dash.sock -m 007 flask-dash:app

[Install]
WantedBy=multi-user.target

```

Change the paths, port etc as appropriate.  
The "flask-dash" term in `flask-dash:app` and `unix:flask-dash.sock` relates to the
name of the Base flask-app name - i.e. `flask-dash.py` in the root of the application tree heirarchy.


### Set SystemD Startup Options ###

Stop NGINX if it is running
```
sudo systemctl stop nginx
```

Start  Gunicorn:
```
sudo systemctl start flaskapp
```

Set Gunicorn to start automatically at server boot:
```
sudo systemctl enable flaskapp
```

## NGINX ##

Configure Nginx to pass web requests to the Gunicorn socket file `flask-dash.sock` by making some additions to the Nginx configuration file.
  
As `root` user, create a configuration file `flaskapp` in the Nginx sites config directory
```
/etc/nginx/sites-available/flaskapp
```
with contents

```
server {
    listen 80;
    server_name <hostname>.com www.<hostname>.com;
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/flask-dash/flask-dash.sock;
    }
}

```
Link the `flaskapp` Nginx configuration to the `sites-enabled` directory

```
ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled
```


#### Test Nginx Configuration ####

```
sudo nginx -t
```
Expected output:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Restart Nginx to add configuration ###


```commandline
sudo systemctl restart flaskapp
```

```
sudo systemctl restart nginx
```

The flask application should be available on Port 80, if the firewall rules allow it.
  
Check status:
```
sudo systemctl status nginx
```

```
sudo systemctl status flaskapp
```


## SSL - install self-signed certificates

These instructions are taken from Step 6 in the following:
[https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04]()

### 1. Install Certbot

```
sudo apt install certbot python3-certbot-nginx
```

Certbot needs to be able to find the correct server block in your Nginx configuration for it to be able to automatically configure SSL.
This is done by checking `server_name` in the NGINX `sites-available` configuration.

### 2. Configure SSL 

From *"Securing the Application"* in the web-tutorial

```python
sudo certbot --nginx -d your_domain -d www.your_domain
```

### 3. Restart NGINX and test

```
sudo systemctl restart nginx
```

Check that the https URL for the website is available (make sure the https port 443 is open on the firewall)

### 4. Redirect port 80 to port 443

Edit the default NGINX web configuration to redirect all port 80 traffic to port 443.

Edit `/etc/nginx/sites-enabled/default` and change as follows:

```
server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;
        return 302 https://$host$request_uri;
       }
```

+ usually it is only necessary to add the `return 302 https://$host$request_uri;` entru after the `server_name` statement.

where `mydomain.com` is an example domain to redirect target traffic for (replace as appropriate)

Use `sudo nginx -t` to check the config then restart NGINX