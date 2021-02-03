# window-opener
TL;DR
Allows for a REST API to control a windows install.

Server which exposes two REST API end-points, one to allow starting and stopping
of "programs" and one which allows lowlevel manipulation.

The second API is intended for use on machines which will be controlled from
the main server. Example of such scenarios is parsec combined with tools on
the remote desktop.

## Why another tool?

Unlike AutoIt and other automation tools, this provides two crucial features (for me anyhow)

1. REST API
   To be able to trigger the automation using REST API is crucial to make it work with my existing
   AV control system.
2. Programs concept
   By defining a program which consists of different actions to take, both locally and remotely (by
   chaining the server), we can easily handle starting of various things on a PC and cleaning up.
   In other words, if you want to start steam, you ask to start the steam program. If you decide you'd
   rather run skype, you ask to start program skype. But since you were running a program already, it will
   first be stopped before the next program is started. Perfect for exposing various parts of windows as
   `scenes` or `apps` to your AV control system.
3. Chaining
   The PC you control might not be capable to do what you want, so you use it as a remote display (parsec)
   or you need more than one PC to do something when you start a program. By having a lowlevel end-point,
   any local action can now be forwarded to another instance for execution.

# Requirements
- Python 3.8 (may work with lower, not tested)
- Windows 10 (may work with lower, not tested)

- Flask
- Requests
- psutil
- pywin32
- pyyaml

# Configuration

## secrets.yml

This file holds anything dear to you. This is a great place to put passwords and tokens.
The values in this file can be accessed using curly braces in the main configuration file.
By splitting it up, you can have sensitive settings local only while keeping your config file
checked into git.

The format of the file is as follows:

```
secrets:
  login : somepassword
  ...

token: your_superawesome_secret_token
```

The `secrets:` header contains all the values you wish to use from the `config.yml` file. Simply list the name you'd
like to use to access it (for example `login`) and then the value that should replace it (for example `somepassword`).
You can list as many as you want, just make sure the names are unique.

Once you've defined the ones you need, you can reference them using curly braces in your `config.yml`,
for example: `{login}` which will be replaced with `somepassword`.

If you don't need this, simply leave the section blank or omit the `secrets:` part completely.

There's also a key called `token` which HAVE TO be defined, without it, the REST API endpoints will be disabled.
This token is used to validate that the call is coming from a source we trust.

## config.yml

This is the meat of the server. Here we define the different programs that will be exposed.

To be continued...