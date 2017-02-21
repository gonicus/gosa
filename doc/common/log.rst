Logging
=======

Logging is handled by the default python logging module. To configure
logging for Clacks, you can add the following infomration to your main
Clacks configuration file, or - at your choice - create a new file for
logging inside the config.d directory.

Here's an example:

	[loggers]
	keys=root,clacks
	
	[handlers]
	keys=syslog,console,file
	
	[formatters]
	keys=syslog,console
	
	
	[logger_root]
	level=CRITICAL
	handlers=console
	
	[logger_clacks]
	level=INFO
	handlers=console
	qualname=clacks
	propagate=0
	
	[handler_console]
	class=StreamHandler
	formatter=console
	args=(sys.stderr,)
	
	[handler_syslog]
	class=logging.handlers.SysLogHandler
	formatter=syslog
	args=('/dev/log',)
	
	[handler_file]
	class=logging.handlers.TimedRotatingFileHandler
	formatter=syslog
	args=('/var/log/clacks/agent.log', 'w0', 1, 4)
	
	[formatter_syslog]
	class=logging.Formatter
	format=%(asctime)s %(name)s: %(levelname)s %(message)s
	datefmt=%b %e %H:%M:%S
	class=logging.Formatter
	
	[formatter_console]
	format=%(asctime)s %(levelname)s: %(module)s - %(message)s
	datefmt=
	class=logging.Formatter
	
