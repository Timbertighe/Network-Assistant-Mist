"""
Provides supporting functions to the Mist webhooks
Authenticates incoming webhook messages
Parses incoming webhooks, filters, and sends to teams

Usage:
    import 'misthandler' into the application
    Create an object based on the MistHandler class

Restrictions:
    Needs access to the 'teamschat' module

To Do:
    None

Author:
    Luke Robertson - February 2023
"""

from core import teamschat
from core import plugin
from datetime import datetime
import termcolor


LOCATION = 'plugins\\mist\\mist-config.yaml'


# Create a class to handle Mist webhooks
class MistHandler(plugin.PluginTemplate):
    def __init__(self):
        super().__init__(LOCATION)
        self.table = self.config['config']['sql_table']

    # Each alert has a different priority, which admins assign
    # These priorities are defined in mist-config.yaml
    def alert_priority(self, event):
        '''Takes given events, and adds a priority level'''
        match event['event']:
            case 'device_event':
                if event['type'] in self.config['device_event']:
                    # Check if this alert has a subpriority
                    # (the 'default' keyword must be there)
                    if 'default' in str(self.config['device_event']
                                        [event['type']]):
                        # Set the default priority
                        event['level'] = (self.config['device_event']
                                          [event['type']]['default'])

                        # Check if there is a more specific priority
                        for entry in (self.config['device_event']
                                                 [event['type']]):
                            if entry == 'default':
                                break
                            if entry in event['text']:
                                event['level'] = (self.config
                                                  ['device_event']
                                                  [event['type']][entry])

                    # An alert with no sub priority
                    else:
                        event['level'] = (self.config['device_event']
                                          [event['type']])
                else:
                    event['level'] = 1

            case 'audit':
                # Some audit events don't have an 'admin' (user) field,
                # so we will inject one
                if 'admin' not in event:
                    event['admin'] = 'system'

                # Some audit events don't have an 'site' field,
                # so we will inject one
                if 'site' not in event:
                    event['site'] = 'global'

                # Split the 'task' field, to just read the part before the
                # description; This matches the entry in the YAML file
                if event['task'].split(' "')[0] in self.config['audit']:
                    event['level'] = (self.config['audit']
                                      [event['task'].split(' "')[0]])
                else:
                    event['level'] = 1

            case 'alarm':
                if event['type'] in self.config['alarm']:
                    event['level'] = (self.config['alarm']
                                      [event['type']])
                else:
                    event['level'] = 1

            case 'updown':
                if event['err_type'] in self.config['updown']:
                    event['level'] = (self.config['updown']
                                      [event['err_type']])
                else:
                    event['level'] = 1

            case 'default':
                event['level'] = 1

    # Parse the alerts into a standard dictionary format that we can use
    # If fields are missing, add them in
    def alert_parse(self, raw_response):
        '''
        Takes a raw event from Mist,
        and parses it into something we can use
        '''
        details = {}
        match raw_response['topic']:
            case 'device-events':
                for event in raw_response['events']:
                    details['event'] = 'device_event'
                    details['name'] = event['device_name']
                    details['type'] = event['device_type']
                    details['mac'] = event['mac']
                    if 'site_name' in event:
                        details['site'] = event['site_name']
                    else:
                        details['site'] = 'No site listed'
                    details['type'] = event['type']
                    if 'text' in event:
                        details['text'] = event['text']
                    else:
                        details['text'] = 'no additional details available'

            case 'alarms':
                for event in raw_response['events']:
                    details['event'] = 'alarm'
                    details['count'] = event['count']
                    details['site'] = event['site_name']
                    details['type'] = event['type']
                    if 'hostnames' in event:
                        details['devices'] = event['hostnames']
                    else:
                        details['devices'] = 'No device listed'

            case 'audits':
                for event in raw_response['events']:
                    details['event'] = 'audit'
                    details['task'] = event['message']

                    if 'before' in event:
                        details['before'] = event['before']

                    if 'after' in event:
                        details['after'] = event['after']
                    else:
                        details['after'] = "No details available"

                    if 'admin_name' in event:
                        details['admin'] = event['admin_name']

                    if 'site_name' in event:
                        details['site'] = event['site_name']

            case 'device-updowns':
                for event in raw_response['events']:
                    details['event'] = 'updown'
                    details['name'] = event['device_name']
                    details['device'] = event['device_type']
                    details['mac'] = event['mac']
                    details['site'] = event['site_name']
                    details['err_type'] = event['type']

            case _:
                topic = raw_response['topic']
                for event in raw_response['events']:
                    details['event'] = topic
                    details['data'] = event
                    print(raw_response)

        return details

    # Handle an event, whatever it may be
    # Takes the event, which needs parsing
    def handle_event(self, raw_response, src):
        '''
        takes a raw event from Mist, and handles it as appropriate
        This includes parsing the event, assigning a priority,
        and possibly sending it to teams
        '''

        # Parse the message
        event = self.alert_parse(raw_response)

        # Filter events
        # These are just keywords that we want to avoid
        for item in self.config['filter']:
            if item in str(event):
                print('filtering out an event')
                return

        # Add the event level (1-4) to the 'event'
        self.alert_priority(event)

        # Add the source IP to the event
        event['src_ip'] = src

        # Handle device events
        message = ''
        if event['event'] == 'device_event':
            match event['level']:
                case 1:
                    message = f"<b><span style=\"color:Yellow\"> \
                        {event['name']} \
                        </span></b> in the <span style=\"color:Lime\"><b> \
                        {event['site']}</b></span> site had a <b> \
                        <span style=\"color:Orange\">{event['type']} \
                        </span></b> event. <br> {event['text']}"
                    print('Level 1 event:', event)

                case 2:
                    message = f"<b><span style=\"color:Yellow\"> \
                        {event['name']} \
                        </span></b> in the <span style=\"color:Lime\"><b> \
                        {event['site']}</b></span> site had a <b> \
                        <span style=\"color:Orange\">{event['type']} \
                        </span></b> event"
                    print('Level 2 event:', event)

                case 3:
                    print('Level 3 event:', event)

        # Handle audit events
        elif event['event'] == 'audit':
            match event['level']:
                case 1:
                    if 'before' in event:
                        # Find the difference
                        old_config = []
                        for line in str(event['before']).split(", "):
                            if line not in str(event['after']).split(", "):
                                old_config.append(line)

                        new_config = []
                        for line in str(event['after']).split(", "):
                            if line not in str(event['before']).split(", "):
                                new_config.append(line)

                        message = f"<b><span style=\"color:Yellow\"> \
                            {event['admin']}</span></b> just worked on the \
                            <span style=\"color:Lime\"><b>{event['site']}</b> \
                            </span> site<br> The completed task was: <b> \
                            <span style=\"color:Orange\">{event['task']} \
                            </span></b>.<br> New config: <br>{new_config} \
                            <br> <br>Old config: <br>{old_config}"
                    else:
                        message = f"<b><span style=\"color:Yellow\"> \
                        {event['admin']}</span></b> worked on to the  \
                        <span style=\"color:Lime\"><b>{event['site']}</b> \
                        </span> site.<br> The completed task was: <b> \
                        <span style=\"color:Orange\">{event['task']} \
                        </span></b>"
                    print('Level 1 event:', event)

                case 2:
                    message = f"<b><span style=\"color:Yellow\"> \
                        {event['admin']}</span></b> worked on to the \
                        <span style=\"color:Lime\"><b>{event['site']}</b> \
                        </span> site."
                    print('Level 2 event:', event)

                case 3:
                    print('Level 3 event:', event)

        # Handle alarms
        elif event['event'] == 'alarm':
            match event['level']:
                case 1:
                    message = f"{str(event['count'])} devices in the \
                        <span style=\"color:Lime\"><b>{event['site']}</b> \
                        </span> site have raised an alarm<br> devices \
                        {str(event['devices'])} have the status <b> \
                        <span style=\"color:Orange\">{event['type']} \
                        </span></b>"
                    print('Level 1 event:', event)

                case 2:
                    message = f"One or more devices in the \
                        <span style=\"color:Lime\"><b>{event['site']}</b> \
                        </span> site have raised non-critical alarms (<b> \
                        <span style=\"color:Orange\">{event['type']} \
                        </span></b>)"
                    print('Level 2 event:', event)

                case 3:
                    print('Level 3 event:', event)

        # Handle device up/down events
        elif event['event'] == 'updown':
            match event['level']:
                case 1:
                    message = f"A/An <b><span style=\"color:Yellow\"> \
                        {event['device']}</span></b> in the \
                        <span style=\"color:Lime\"><b>{event['site']}</b> \
                        </span> site ({event['name']}) has changed status<br> \
                        New status: <b><span style=\"color:Orange\"> \
                        {event['err_type']}</span></b>"
                    print('Level 1 event:', event)

                case 2:
                    message = f"A/An <b><span style=\"color:Yellow\"> \
                        {event['device']}</span></b> in the \
                        <span style=\"color:Lime\"><b>{event['site']}</b> \
                        </span> site has changed status"
                    print('Level 2 event:', event)

                case 3:
                    print('Level 3 event:', event)

        # Handle anything unexpected
        else:
            message = event
            print(termcolor.colored(event), "red")

        # Write the entry to the database
        if event['level'] != 4:
            self.log(message, event)

    # Send a message to teams, and write to SQL
    def log(self, message, event):
        """
        Send a message to Teams, and log to the SQL server
        """
        date = datetime.now().date()
        time = datetime.now().time().strftime("%H:%M:%S")
        ip_decimal = self.ip2integer(event['src_ip'])

        # Different event types have different fields
        # Some need to be handled a little differently
        if event['event'] == 'device_event':
            device = event['name']
            description = event['text']
            type = event['type']

        elif event['event'] == 'alarm':
            device = ''
            for mist_device in event['devices']:
                device += ', ' + mist_device
            description = ''
            type = event['type']

        elif event['event'] == 'audit':
            device = ''
            description = event['task'].replace("[", "").replace("]", "") \
                .replace("'", "")
            type = event['task'].split(" ", 1)[0]

        elif event['event'] == 'updown':
            device = event['name']
            type = event['err_type']
            description = ''

        # Print to the terminal
        print(event)

        # Send the message to teams
        chat_id = ''
        if message:
            chat_id = teamschat.send_chat(
                message,
                self.config['config']['chat_id']
            )['id']

        # Log to SQL
        fields = {
            'device': f"'{device}'",
            'site': f"'{event['site']}'",
            'event': f"'{type}'",
            'description': f"'{description}'",
            'logdate': f"'{date}'",
            'logtime': f"'{time}'",
            'source': f"{ip_decimal}",  # IP address needs to be decimal
            'message': f"'{chat_id}'"
        }

        self.sql_write(
            database=self.config['config']['sql_table'],
            fields=fields
        )
