# utils.py

# 20/10/2023a
# 21/10/2023a
# 22/10/2023a
# 04/11/2023
# 16/11/2023a
# 19/11/2023
# 23/11/2023
# 25/11/2023g on put_item and update_item changed **query to kv=query
# 29/11/2023a

import base64
import datetime
import json
import secrets
import urllib.request

import boto3
import botocore


class DataEncoder(json.JSONEncoder):
   def default(self, object):
        if isinstance(object, decimal.Decimal):   # -> integer
            return int(object)

        else:
            return object


class AttributeDict(dict):
    __slots__ = () 
    __setattr__ = dict.__setitem__

    def __getattr__(self, name):
        if name in dict(self):
            return dict(self)[name]

        return None


class Datastore:
    def __init__(self, url=None, token=None):
        self.url     = url
        self.token   = token
        self.result  = None
        self.message = None
        self.stats   = None
        self.data    = {}
        
    
    def error(self):
        if self.result is None:
            return True
 
        return self.result != 'ok'

    
    def error_text(self):
        return f'Error ({self.result}) — {self.message}'

    
    def error_json(self):
        return dict(result=self.result, message=self.message)

    
    def stats(self, stat=None):
        return dict(result=self.data.get('stats', {}).get(stat))
        
    
    def put_item(self, collection, item, kv=None):
        self.result  = None
        self.message = None
        
        if kv is None:
            self.result  = 'datastore-missing-query'
            self.message = 'Missing query for datastore request (put-item)'
            return None

        url = f'{self.url}/put-item/{self.token}/{collection}/{item}' + '?' + urllib.parse.urlencode(kv)
            
        print(f'utils:datastore:update-item {url=}')
    
        response = urllib.request.urlopen(url)
        
        if response.status != 200:
            self.result  = 'datastore-http-error'
            self.message = 'Datastore request (put-item) HTTP error ({response.status}) — {response.reason}'
            return None

        text         = response.read()
        self.data    = json.loads(text)
 
        self.result  = self.data.get('result')
        self.message = self.data.get('message')
        self.stats   = self.data.get('stats')
       
        return self.data.get('content')
        
    
    def update_item(self, collection, item, kv=None):
        self.result  = None
        self.message = None
        
        if kv is None:
            self.result  = 'datastore-missing-query'
            self.message = 'Missing query for datastore request (update-item)'
            return None

        url = f'{self.url}/update-item/{self.token}/{collection}/{item}' + '?' + urllib.parse.urlencode(kv)
            
        print(f'utils:datastore:update-item {url=}')
    
        response = urllib.request.urlopen(url)
        
        if response.status != 200:
            self.result  = 'datastore-http-error'
            self.message = 'Datastore request (update-item) HTTP error ({response.status}) — {response.reason}'
            return None

        text         = response.read()
        self.data    = json.loads(text)
 
        self.result  = self.data.get('result')
        self.message = self.data.get('message')
        self.stats   = self.data.get('stats')
       
        return self.data.get('content')
        
    
    def function(self, function_name, query=None, deleted=False):
        self.result  = None
        self.message = None

        if query is None:
            url = f'{self.url}/function/{self.token}/{function_name}?deleted={deleted}'
    
        else:
            url = f'{self.url}/function/{self.token}/{function_name}' + '?' + urllib.parse.urlencode(query)
            
        print(f'utils:datastore:function {url=}')
    
        response = urllib.request.urlopen(url)
        
        if response.status != 200:
            self.result  = 'datastore-http-error'
            self.message = 'Datastore request (function) HTTP error ({response.status}) — {response.reason}'

        text      = response.read()
        self.data = json.loads(text)
 
        self.result  = self.data.get('result')
        self.message = self.data.get('message')
        self.stats   = self.data.get('stats')
       
        return self.data.get('content', {})
        
    
    def query(self, first=None, rest=None, query=None, deleted=False):
        if rest is None:
            url = f'{self.url}/{first}/{self.token}'
 
        else:
            url = f'{self.url}/{first}/{self.token}/{rest}'
            
        if query is not None:
            url += '?' + query
 
        print(f'utils:datastore:data {url=}')
    
        try:
            response = urllib.request.urlopen(url)
            
        except Exception as e:
            self.result  = 'datastore-open-error'
            self.message = f'Datastore data URL {str(e)} {url=}'
            return None
        
        if response.status != 200:
            self.result  = 'datastore-http-error'
            self.message = 'Datastore data HTTP error ({response.status}) — {response.reason}'

        text      = response.read()
        self.data = json.loads(text)
 
        self.result  = self.data.get('result')
        self.message = self.data.get('message')
        self.stats   = self.data.get('stats')
       
        return self.data.get('content', {})
        
    
    def documentation(self):
        url = f'{self.url}/documentation-source/{self.token}'
 
        print(f'utils:datastore:documentation {url=}')
    
        response = urllib.request.urlopen(url)
        
        if response.status == 200:
            return response.read().decode('utf-8')
        
        else:
            return f'Datastore request (documentation) HTTP error ({response.status}) — {response.reason}'


def redirect(url, headers={}):
    headers['Location'] = url

    return dict(statusCode=302, headers=headers)

    
def send_email(region=None, source=None, destination=None, 
        subject=None, text=None, html=None, reply_tos=None):
    """
    Sends an email.

    Note: If your account is in the Amazon SES  sandbox, the source and
    destination email accounts must both be verified.

    :param source: The source email account.
    :param destination: The destination email account.
    :param subject: The subject of the email.
    :param text: The plain text version of the body of the email.
    :param html: The HTML version of the body of the email.
    :param reply_tos: Email accounts that will receive a reply if the recipient
                      replies to the message.
    :return: The ID of the message, assigned by Amazon SES.

    https://docs.aws.amazon.com/ses/latest/dg/example_ses_SendEmail_section.html
    """

    ses_client = boto3.client("ses", region_name=region)

    send_args = {
        'Source': source,
        'Destination': {'ToAddresses': [destination,]},
        'Message': {
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': text}, 'Html': {'Data': html}}}}

    if reply_tos is not None:
        send_args['ReplyToAddresses'] = reply_tos

    try:
        response = ses_client.send_email(**send_args)
        message_id = response['MessageId']
        print(f'utils:send_email {message_id=} {source=} {destination=}')

    except botocore.exceptions.ClientError:
        print(f'utils:send_email:error {source=} {destination=}')
        return None

    else:
        return message_id


def generate_token(bits=64):
    # Generate a random base32 token with the specified number of bits
    # - examples 64='pmwvubshcl7nc' 128='g2xcgnsrbi3g4sb4e47yivcksa'
    # - idea from https://docs.crunchybridge.com/api-concepts/eid/
    
    return base64.b32encode(secrets.token_bytes(int(bits / 8))).decode('utf-8').lower().replace('=', '')


def timestamp():
    return str(datetime.datetime.utcnow().isoformat())


def sort(d):
    return dict(sorted(d.items()))


def get_value(data, key):
    if key is None or len(key) == 0:
        return ''

    if data is None:
        return ''

    if key in data:
        value = data.get(key)
        
        if value is None:
            return ''
            
        else:
            return value
        
    else:
        return ''
