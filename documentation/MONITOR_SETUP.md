# Setup of Pyminder Monitor
Deploying the pyminder monitor is actually the easiest component of the system, consisting broadly of three setups: 
1. `pip3 install pyminder`
2. Creating the config file && setting environment variables
3. `python3 -m pyminder_monitor /path/to/config.file &`

For an optional fourth bonus point, pyminder monitor could be set up as a service or
as a cron job to allow it to survive reboots of the host pi.

# Configuring Pyminder Monitor.

Pyminder monitor expects a file similar to the config file in `src/pyminder_monitor/monitor.conf`, the path to which is provided as its only launch argument.

That file contains the following configuration flags:

|Flag|Description|
|----|-----------|
|color_resting| A `#NNNNNN` RGB color code to set the colour and brightness of the screen when it is displaying the "waiting for messages" text.|
|major_error_color| A `#NNNNNN` code, sets colour used for messages with the `major` severity.
|minor_error_color| A `#NNNNNN` code, sets colour used for messages with the `minor` severity.
|info_color| A `#NNNNNN` code, sets colour used for messages with the `info` severity.
|service_host| A resolvable name or address for the host where the pyminder service is operating.
|service_port| The tcp port upon which the service is listening at `service_host`
|allow_self-signed_certs| Provided for development reasons only, and should be set to `false` for best security. Enabling this effectively disables hostname validation during the TLS handshake, meaning the monitor does not confirm which host it is drawing messages from.
|trusted_cert|A path to a custom `.pem` certificate, if used.
|custom_cert| If `true`, monitor will use the cert at `trusted_cert` to perform host vaidation for the service.|

Monitor will prompt for a username and password, which should be a `monitor` credential for Pyminder, which you configured as part of the directions in `SERVICE_SETUP.md`.

If you wish to bypass this prompt (say, for automatic start of the program as a service or cron job) you will need to set the `MONITOR_UID` and `MONITOR_PASSWORD` environment variables. (n.b., for cron these need to be set in the crontab)