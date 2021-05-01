# Setting Up `Piminder_service`
Piminder_Service is the underlying API and database responsible for being the "brain" of Piminder. From version 1.0 and later, it is fully self-instantiating on the database level and requires only minor operations to deploy.

There are two fundamental ways to deploy the service: **dockerized** and **directly-hosted**. Of the two we strongly recommend taking the dockerized approach provided our guidelines below are followed.

## Dockerized Deployment
The latest release version of Piminder-service is available through dockerub as `ZAdamMac/Piminder-service:latest` or by downloading this repo and building from the Dockerfile in `src/Piminder_service/`. This version can be fully configured in one of two ways:
- via environment variables, which will override;
- mounting your local copy of `Piminder-service.conf` to the container at `/app/Piminder-service.conf`.

Both options have their pros and cons - in particular the config file is especially helpful as it can be mounted using [docker secrets](https://docs.docker.com/engine/swarm/secrets/). As this configuration does contain sensitive information pertaining to the credentials used in the service, that is recommended.

This configuration has a major advantage in that it can be made part of an [nginx reverse proxy service](https://hub.docker.com/r/jwilder/nginx-proxy). While a guide on setting up such a service is forthcoming - and this document will be updated when it is available - a docker-compose file is provided below as an example of such a configuration, at the end of this file.

## Direct Deployment
It is also possible to execute `run.py` within its own directory and run manually, using both configration options set below. When doing so it is strongly recommended that you enable SSL and provide your own certificates, or keep `LISTENHOST` as `localhost` at the bare minimum.

## Configuring Service
For each configuration value there are as many as two possible keys for legacy reasons, with some variables being set under one name as envvars and the other in the config file. Both options are listed below.

There are also two special-case values which can only and must be passed as envvars:
- `Piminder_ADMIN_USER`, which must be passed on every startup of the service, and is used on initial startup to set the username of the first administrative user.
- `Piminder_ADMIN_PASSWORD`, which need be present only on the first startup of the service so that the database initialization utility can create that administrative user. If it is absent on subsequent runs it is ignored.

In addition there are the following flags available:

|ENV|CFG|Action|
|---|---|------|
|Piminder_HOST|LISTENHOST|The hostname or IP which the operator expects Flask to listen against. For dockerized deployment `0.0.0.0` is recommended. For direct deployment, `localhost`.|
|Piminder_PORT|LISTENPORT| A tcp port for the service to listen on. Any value is permitted but using a value other than `80` requires additional configuration for the Nginx service when operating in the dockerized mode.|
|Piminder_DEBUG|DEBUG| Argues the flag to app.run() in flask and controls whether or not the debugger and its interface are exposed as a result. Recomended set to `false` as no additional information is provided by the application itself in the debug state|
|Piminder_DB_HOST|DBHOST| Sets the value of the host argument in DB connections. Direct deployment can use 'localhost' as appropriate. In the dockerized deployment, this should be the service or container name of the `mariadb` container, and a `link` should be declared between the two.|
|Piminder_DB_PASSWORD|PASSPHRASE| This is the pasword of the mariadb user and should be unique to your installation. This user has absolute authority over the `Piminder` database on the target mariadb instance.|
|Piminder_DB_USER|USERNAME| DB username, not to be confused with the admin username or the username of any of the other credentials.\

The following three arguments all default to false if not provided and are the same in both env-vars and in the config file:
- `USE_SSL` configures whether or not Flask will attempt to create its own SSL wrappings. If set to true, the operator must provide `.pem` files for the certificate and key, or the service will fail to start.
- `SSL_CERT` is the path to the public certificate .pem file.
- `SSL_KEY` is the path to the key file.

Passwords are not currently supported for SSL keys and this is one of the many reasons this use case is discouraged.

## First Run
Regardless of how you choose to pass the configuration values to Piminder-service, it is recommended that you run the service well prior to attempting to deploy `helpers` or `monitor`, as neither of them will work without it either way. In the dockerized deployment, consider running this first deployment in an attached mode, so that you can monitor its progress and ensure the database initialization is completed, as it will print various status messages to output if you are attached.

## Creating Service Credentials
After you have started the service and created the Admin user, you can use this user to create other, less powerful credential pairs (in the form of a username and password combination) for your needs. Our recommendation is to use a unique set of credentials for `monitor`, and a unique set of credentials for each host that will be running applications calling in messages. All of these endpoints are accessible only to users with the `admin` or `3` permission level.

For this process, the endpoint at `YOURHOST/api/users/` is provided. This is a REST-like API that exposes the following methods:
- `GET` returns a full listing of all users, their permission level, and a memo field indicating what that account was created for.
- `POST` handles *new user creation* and expects a JSON body described below in order to do so.
- `PATCH` updates an existing user by overwriting its current database entry.
- `DELETE` updates an existing user by setting its permission byte to 0, which is too low to activate any endpoints. This process is reversible by raising the level in a subsequent patch.

For obvious reasons these factors combine to make the admin credentials very powerful. These should be treated accordingly as there is no change control or tracking available for the users table, nor indeed any real access control on the database itself beyond the need for a valid credential.

#### Json body for the POST and PATCH commands
```json
{ 
  "username": "",
  "permissionLevel": "", 
  "memo": "", 
  "password": ""
}
```

Permission level should be one of the following:

|permissionLevel|stored value|rights|
|---|---|---|
|admin|3|add/modify/remove users, add/modify/remove messages|
|monitor|2|post, retrieve, mark read, and delete messages|
|service|1|post new messages to the service, to be used by the actual monitor jobs|

### Example `docker-compose.yaml` for the dockerized deployment
```yaml
version: '3'

services:
  api:
    image: Piminder-service:dev
    restart: always
    expose:
      - 80
    environment:
      NETWORK_ACCESS: internal # with the recommended proxy arrangement, forbids incoming access from the WAN
      VIRTUAL_HOST: something.unexpected.dev
      Piminder_HOST: '0.0.0.0'
      DEBUG: 'true'
      Piminder_DB_HOST: pym-test-db
      Piminder_DB_USER: Piminder
      Piminder_DB_PASSWORD: verystrongpassword
      Piminder_ADMIN_USER: admin
      Piminder_ADMIN_PASSWORD: anothergoodpassword
      USE_SSL: 'False'
      LETSENCRYPT_HOST: something.unexpected.dev
      LETSENCRYPT_EMAIL: webmaster@unexpected.dev
    links:
      - pym-test-db
  pym-test-db:
     image: mariadb
     restart: always
     environment:
       MYSQL_DATABASE: Piminder
       MYSQL_USER: Piminder
       MYSQL_PASSWORD: verystrongpassword
       MYSQL_RANDOM_ROOT_PASSWORD: 'yes'

networks:
  default:
    external:
      name: nginx-proxy  
```