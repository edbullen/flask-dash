
# Python-Flask Dashboards for Databricks

Based on the following:  
[Flask](https://github.com/pallets/flask) - license: https://github.com/pallets/flask-website/blob/master/LICENSE
and  
[Flask Dance](https://github.com/singingwolfboy/flask-dance-google) - Documentation: https://flask-dance.readthedocs.io/en/v0.8.3/quickstarts/google.html  

Developed and tested with Python 3.9.11  

## Code Structure

```
 app/ 
   |--static/
   |--templates/
   | __init__.py
   | forms.py
   | models.py
   | routes.py
   | utils.py
   
 logs/
 migrations/
 sqllite/
 flask-dash.py
 useradmin.py    
```

## Install Notes

Ubuntu Library dependencies

Ubuntu 18

sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev

### User Mixin Integration Reference

https://flask-dance.readthedocs.io/en/v1.0.0/quickstarts/sqla-multiuser.html

# Roles 

If no other registered users are in the `admin` role, the next user logging in is added to role `admin`. 


# Setup - Google OAUTH Client Configuration

Google Cloud Console -> APIs and Services -> Credentials -> *"Create Credentials"* (in top menu)
  
Create a new `OAuth 2.0 Client ID`  

+ Authorized Javascript Origins -> set this to `https://127.0.0.1:5000`
+ Authorized redirect URIs -> set this to `https://127.0.0.1:5000/login/google/authorized`

The above URIs can be used for local development.

For running in a shared test / production cloud environment add additional configuration as necessary: 

+ Authorized Javascript Origins - `https://<mydnsalias>`
+ Authorized redirect URIs -> set this to `https://<mydnsalias>/login/google/authorized`


API credential providers for OAuth are listed under  
*Cloud Console -> APIs and Services -> Credentials*  
in the `OAuth 2.0 Client IDs` section (a new provider configuration should appear there when it is created)

# Setup - Database

Set `FLASK_APP` to the name of the python file that instantiates the Flask app.
```
export FLASK_APP=flask-dash.py
export FLASK_LOG_DIR=./logs
```

Create a new migrate version scripts folder (`./migrations/versions`) :
```
flask db init
```
Ignore the message *"Please edit configuration/connection/logging settings in '/Users/ed.bullen/src/flask-dash/migrations/alembic.ini' before proceeding."*  
Usually it makes sense to check the contents of `./migrations` into the git repo.  

Create the scripts that build the schema (these are stored in `./migrations/versions`:
```commandline
flask db migrate -m "initialise database" 
```

Run the scripts to build the schema:
```commandline
flask db upgrade
```

# Run

### Configure

Configure / set the following environment variables.  
Logging:  
```
export FLASK_LOG_DIR=<path to logs>
```
OAUTH client for Google (see also "Other Notes" below)
```
export GOOGLE_OAUTH_CLIENT_ID=<Google Oauth API ID>
export GOOGLE_OAUTH_CLIENT_SECRET=<Google Oauth API Secret>
```


### Start
Run on port 5000
```commandline
flask run
```
Run on port 80
```commandline
flask run --host 0.0.0.0 --port 80
```

Configure to run on port *443* (SSL encrypted) with **NGINX and GUNICORN**: [./GUNICORN_NGINX.md](./GUNICORN_NGINX.md)

### Manage Users and Roles outside the web application
Roles can be added and removed and users can be added to / removed from roles by using the `useradmin` tool.  This is a command-line utility that has to be run locally to the server environment.

- List roles: `./useradmin -lr`  
- Add a role: `./useradmin -a -r general`  
- Delete a role `./useradmin -d -r general`  
- Add a user to a role called *user* `./useradmin -a -e my.user@mail.com -r user`
- Remove a user from a role called *user* `./useradmin -d -e my.user@mail.com -r user`


### Add Roles

Roles are managed in the `role` and `user_roles` tables.  

By default, two roles exist: `user` and `admin`.    

Pages / routes can be protected with the decorator `access_required()`. Example  
```python
# example of page where session has to be logged in to see and the user has to be a member of group "admin"
@app.route("/admin")
@login_required
@access_required(role="admin")
def admin():
    
    return render_template("admin.html")
```



# Other notes

## Google OAUTH Notes
From the quick start:
   
*When you run this code locally, set the OAUTHLIB_INSECURE_TRANSPORT environment variable for it to work without HTTPS.   
You also must set the OAUTHLIB_RELAX_TOKEN_SCOPE environment variable to account for Google changing the requested OAuth scopes on you. 
For example, if you put this code in a file named google.py, you could run:*   
```commandline
$ export OAUTHLIB_INSECURE_TRANSPORT=1
$ export OAUTHLIB_RELAX_TOKEN_SCOPE=1
```


# Tests

 


