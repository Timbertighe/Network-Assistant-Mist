# Mist plugin
Handles webhooks from the Juniper Mist cloud

# Using the plugin
### Enabling Webhooks
    Webhooks need to be enabled in the Mist platform. This can be done for the entire Org, or per site
        NOTE: Enabling per org and per site will result in duplicate webhooks
    Set the URL (the IP or name of the chatbot with the route)
    Set a secret, for authentication
    
#### Global Settings
  In Organization > Settings > Webhooks, tick the 'Enable' box  
  Add a Name (anything is fine)  
  Set the URL to your App URL (eg, http://mydomain.com/mist)  
  Set the secret  
  Enable the events you need  

#### Site Settings
  In Organization > Site Settings, select the site you want to enable webhooks for  
  Under 'Webhooks', tick the 'Enable'box  
  Set the Name, URL, and Secret (as described above)  
  Enable the events you want to monitor  

### Authentication
    By default, webhooks are sent unauthenticated  
    Mist supports including a secret, which this app requires  
    Mist will hash the body of the webhook message, with the secret, and attach it as the 'X-Mist-Signature-V2' header  
    Authenticating these messages is achieved by running the same algorithm (HMAC-SHA256), and comparing the hash with the header  
    
### Event Types
  Mist support several event types. Webhooks can be configured to send only a subset of these as needed  
  This app currently supports:  
    - Alerts  
    - Audits  
    - Device Status  
    - Device Events  

### Configuration
    Plugin configuration is in the 'mist-config.yaml' file
    
#### Global Config
    Set 'debug' to True to log events to a text file
    Set 'webhook_secret' to the secret, as set in the Mist webhook configuration
    Set the 'auth_header' to X-Mist-Signature-V2; This is how the main program knows which header to check for authentication

#### Event Filtering
    Mist supports lots of different event types. Currently supported events are 'device_event', 'audit', 'alarm', and 'updown'
    Each of these categories contain many different events.
    The configuration file has a list of these (although the list may not be exhaustive), and priority levels
      * level-1: A critical alert, all details on teams
      * level-2: An important alert, send a summary on teams
      * level-3: Not so important alert, log only, no teams
      * level-4: Ignore completely
    Each of these can have optional sub-priorities, assigned based on additional keywords found in the event
    There is also a 'filter' section to completely filter certain events out, if they contain given keywords
    

- - - -
## Files
### sql_create.py
    Standalone script that connects to the SQL server (as globally defined in the app)
    Creates the table and required fields

### misthandler.py
    The main class of the plugin (MistHandler)
    
#### __init__()
    Loads the configuration file
    Sets up the framework for webhook authentication
    
#### alert_priority()
    Takes an event, and adds an alert level, based on the configuration file
    Default is level 1, unless a specific entry exists

#### alert_parse()
    Takes the events, and puts them into a standard dictionary for better handling
    Events, alerts, up/down, etc, can have slightly different fields, so this normalizes them to prevent errors

#### handle_event()
    The function that the main program calls when a webhook is received
    This uses other methods to parse, filter, and normalize events
    It creates a human readable message, which is sent to the user over teams
    It writes events to SQL
    
#### refresh()
       Reads the config file again
       This allows config to be updated without restarting Flask

## mist-config.yaml
A YAML formatted file used to configure the Mist plugin and filter events received from  
Configuration contains a field called 'debug
* This can be set to True or False
* If true, entries are logged to mist_debug-<date>.log
  
### Filtering
There are two ways events can be filtered:  
* A text string filter: Filters out any string that matches  
* Priority levels: Assigns levels to different events, so they can be handled in different ways  
Events can have a subpriority assigned
* For example, the SW_DOT1XD_USR_AUTHENTICATED may have a level of 3; However, there may be a sub priority of 1 assigned to 'vlan 10'
* This means that if the text 'vlan 10' exists in this event, it will get assigned to level 1

&nbsp;<br>
### Event Levels
  - Level 1 has all details sent to teams  
  - Level 2 has a summary sent to teams  
  - Level 3 logs to terminal only  
  - Level 4 is ignored completely  
  - Any event not listed is implicitly considered to be level 1  
  
&nbsp;<br>
### Assigning Levels
  The YAML file has heading for the supported event types  
  - device_event  
  - audit  
  - alarm  
  - updown  
  
  Under each of these are the event names. The field within the raw webhook that contains the even name varies depending on the event type  
  Each event name is paired with a value from 1 to 4, which represents the priority level  
  
&nbsp;<br>
### Filtering Strings
  The 'filter' heading is a list, with each member item being a string  
  Any string listed here is filtered out, regardless of the event level  
  This is useful to prevent the chatbot from sending certain events to Teams, so you don't get drowned in events  
  At this time, there is no support for regex. It's just a simple string  
  
