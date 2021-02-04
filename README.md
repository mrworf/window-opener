# window-opener
TL;DR
Allows for a REST API to control a windows install.

Server which exposes two REST API end-points, one to allow starting and stopping
of "programs" and one which allows lowlevel manipulation.

The second API is intended for use on machines which will be controlled from
the main server. Example of such scenarios is parsec combined with tools on
the remote desktop.

## Why another tool?

Unlike AutoIt and other automation tools, this provides three crucial features (for me anyhow)

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
  remotetoken : some_uniqe_token
  ...

token: your_superawesome_secret_token
```

The `secrets:` header contains all the values you wish to use from the `config.yml` file. Simply list the name you'd
like to use to access it (for example `remotetoken`) and then the value that should replace it (for example `some_uniqe_token`).
You can list as many as you want, just make sure the names are unique.

Once you've defined the ones you need, you can reference them using curly braces in your `config.yml`,
for example: `{remotetoken}` which will be replaced with `some_uniqe_token`.

If you don't need this, simply leave the section blank or omit the `secrets:` part completely.

There's also a key called `token` which HAVE TO be defined, without it, the REST API endpoints will be disabled.
This token is used to validate that the call is coming from a source we trust.

## config.yml

This is the meat of the server. Here we define the different programs that will be exposed as well as define other
instances of window opener which we intend to contact (to use the lowlevel API).

### endpoints

```
endpoints:
  remote:
    url: http://1.2.3.4:8080
    token: {remotetoken}
```

Here we declare a instance of window opener running at port `8080` at `1.2.3.4`, we also define the token to use when talking to it. Please note that it uses the substitution from `security.yml` to avoid having to define the secret inside your config file.

You can use the same token for multiple instances if you'd like, it's entirely up to you. As long as the `token` here matches the `token` in `secrets.yml` of the remote instance, you're golden.

### programs

The section which holds all exposed "programs" which can be accessed via the program end-point

```
programs:
  demo:
    start:
      - method: execute
        arguments:
        - mylocalapp.exe
        - with
        - arguments
      - method: delay
        arguments: 4
      - method: execute
        endpoint: remote
        arguments:
        - remoteappwithnoarguments.exe
    stop:
      - method: close window
        arguments: TitleOfWindow
```

Here we define an program called `demo` and then we describe how this will be started and stopped
(`start` and `stop` respectively).

For both of these sections, we define the actions needed to either start or stop a program.
They take the form of

```
method: <method>
endpoint: <defined endpoint>
arguments: <parameters for the method>
```

`Method` can be one of
- execute
  Will run an application with possible arguments.
  All arguments MUST be broken down into individual lines.
  So `myapp.exe arg1 arg2 "arg 3"` would translate to
  ```
  - myapp.exe
  - arg1
  - arg2
  - arg 3
  ```
- delay
  Delays execution with the number of seconds provided in `arguments`
  This can be a fractional value for sub 1 second delays
- close window
  Closes a specified window (provided by arguments) or if blank,
  will close the current active window
- kill app
  Kills all instances of an application defined by the `arguments`.
  Use task manager (details tab) to locate the name of the application you wish
  to terminate. If multiple instances are found with the same name, ALL of them will
  be terminated.
- kill pid
  Kills a specific pid (program id). This is available for use, but hard to use manually
  since the PID changes with every run.
- sendkeys
  Sends a number of keys to the currently active window. See https://docs.microsoft.com/en-us/dotnet/api/system.windows.forms.sendkeys?view=net-5.0 for details on how this works.
  Please note that to use curly braces, you must type them twice to avoid having the substituion kick in.
  And since the YAML standard allow use of curly braces as well, you must enclose it with quotation marks.
  This means that in order to sennd ENTER (`{ENTER}`) you must write `"{{ENTER}}"` or it will not work.
  You don't have to do `sendkeys` per key, you can have it send entire strings at a time.

`endpoint` specifies where to perform the defined action. If omitted, `local` is assumed,
meaning it will run on the computer which is hosting this service.
Any endpoint you want to use MUST be defined in the `endpoints` section above, with `local` being
the only exception.

`arguments` can either be a single value like `arguments: 5` or `arguments: "some string"`
or a list of arguments, like in the case of `method: execute`

## Special considerations

### execute

Whenever `execute` is used in the start section, window opener will automatically
try to kill the app when stop is run, it does this by keeping track of the PID it
got from executing the program.

This is far from foolproof, many applications will actually simply trigger a service
or main application to run and then quit, which means that the PID doesn't exist anymore
at the time of stop. But for simpler apps like `chrome.exe`, this means you don't need
to define a stop action if all you want is for the app to terminate at the end.

### kill pid/app

Please note that `kill pid`, `kill app` and when `execute` is used, the application
is not closed in the normal sense, it's actually the equivalent to using the task
manager to end a process.

Why is this distinction important?

Some apps may not save the latest state when terminated in this fashion.

### remote end-points

All actions that you normally can run locally will work exactly the same way with
a remote end-point, including the `execute` stop behavior.

# REST API

Window Opener exposes two end-points

## /program

This is the main end-point intended to be used by external callers. It allows you to start/stop programs as
well as listing the available programs and to show if any program is currently active.

### GET /program

```
{
  "active":null,
  "programs":[
    "steam",
    "jitsi"
  ]
}
```
This is the typical output for a configured system. It shows that there are two programs (`steam` and `jitsi`)
and that current active program is `null` (no active program). If you have started a program, `active`
will hold the name of the current active program.

### POST /program

This is how you get it to do things. It requires a JSON payload.

To start a program:
```
{
  "start":"program",
  "token":"your_superawesome_secret_token"
}
```
This will cause window opener to start `program`, should it already be running a different program,
it will first run the stop actions for that program before starting this one.

If `token` doesn't match what you defined in `secrets.yml` this call will fail.

To stop a program:
```
{
  "stop":"program",
  "token":"your_superawesome_secret_token"
}
```
If the program `program` is running, it will be stopped. If it isn't running, nothing happens.
You can close current program by setting `stop` to `null`, like so:
```
{
  "stop":null,
  "token":"your_superawesome_secret_token"
}
```

If `token` doesn't match what you defined in `secrets.yml` this call will fail.

# Command line options

```
usage: server.py [-h] [--port PORT] [--listen LISTEN] [--debug] [--lowlevel {yes,no}] [--program {yes,no}]

WindowOpener - A windows REST API automation tool

optional arguments:
  -h, --help           show this help message and exit
  --port PORT          Port to listen on (default: 8080)
  --listen LISTEN      Address to listen on (default: 0.0.0.0)
  --debug              Enable loads more logging (default: False)
  --lowlevel {yes,no}  Enable lowlevel REST API (default: yes)
  --program {yes,no}   Enable program REST API (default: yes)
```

Most of these are self explainatory, but it's worth mentioning that if you just want to use
the instance as a chained instance to another one, using `--program=no` is recommended.

Likewise, if your main instance won't ever be used by another instance, using `--lowlevel=no`
is also recommended.

`--debug` is typically not needed unless you're debugging an issue.
