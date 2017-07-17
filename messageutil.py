import re
import urllib.parse

"""
Provides utilities for managing message strings and responding to reddit messages.
Includes in-code formatting features.
"""

__author__ = "github.com/allemangD"
__status__ = "Development"

messages = {
    'exclude_user': 'Exclude Me',
    'exclude_sub': 'Exclude From Subreddit',
    'include_user': 'Include Me',

    'pm_link': 'https://www.reddit.com/message/compose?to=kittens_from_space',
    'exclude_link': 'https://reddit.com/message/compose?'
                    'to=WikiTextBot&message={%exclude_user}&subject={%exclude_user}',

    'user_exclude_success': "You are now excluded form the bot.\n\n"
                            "To be included again, message me '{include_user}'.\n\n"
                            "Have a nice day!",
    'user_exclude_failure': "You already seem to be excluded from the bot.\n\n"
                            "To be included again, message me '{include_user}'.\n\n"
                            "Have a nice day!",
    'user_include_success': "You are included in the bot again!\n\n"
                            "Have a nice day!",
    'user_include_failure': "You don't seem to be excluded from the bot. If you think "
                            "this is false, [message]({pm_link}) me.\n\n"
                            "Have a nice day!"
}
"""The contents of messages are accessed with get_message(message_id). To include 
message A in the text of message B, include message B's ID in curly braces: 

    'salutation': 'Hello',
    'target': 'World',
    'greeting': '{salutation}, {target}'
    
In the above example, get_message('greeting') would return 'Hello, World!'

Messages are also formatted recursively to a maximum depth, by default 3. This means 
that messages can easily be composed from each other: 

    'link': 'https://google.com/',
    'title': 'Google',
    'search_engine': '[{title}]({link})',
    'text': 'I prefer {search_engine}.'

"""

intents = [
    'exclude_user', 'include_user'
]
"""Certain messages can be marked as message intents to be acted on by the bot. A 
message's intent is retrieved with get_intent(message) which performs a naive fuzzy 
search on the contents of the message. The message is compared with the message 
associated with each message id in the intents list. 

For example:

if the contents of messages are:

    'respond': 'Please respond',
    'ignore': 'Ignore me',
    
and the contents of intent are:

    'ignore', 'respond'
    
Then any message containing some variation on the phrase "please respond" will give the 
intent 'respond', while any message containing the phrase 'ignore me' will give the 
intent 'ignore'. If a message contains both, then the first intent in the list will be 
given, in this case 'ignore' 

"""

footer_items = [
    ('PM', '{pm_link}'),
    ('{exclude_user}', '{exclude_link}'),
    ('{exclude_sub}', 'https://np.reddit.com/r/{subreddit}/about/banned'),
    ('FAQ / Information', 'https://np.reddit.com/r/WikiTextBot/wiki/index'),
    ('Source', 'https://github.com/kittenswolf/WikiTextBot'),
    'Downvote to remove',
    'v0.24'
]
"""The footer text is retrieved with get_footer(subreddit). The footer is built of a 
list of strings and 2-tuples of strings. Strings are treated as normal messages, 
which means that all {id} formatting is applied, with the addition of the 'subreddit' 
message, which is received as a parameter to get_footer. 
 
Tuples are converted to markdown links. The first element of a tuple is the text for 
the link, while the second is the URL. The entire footer is also converted to 
superscript. 

The contents of lists are surrounded by brackets [ ] and delimited by pipes | .

As an example, the footer:

    'footer',
    ('google', 'https://google.com/'),
    '/r/{subreddit}'
    'end footer'
    
Results in the markdown:

    '^[ ^footer ^| [^google](https://google.com/) ^| ^/r/CurrentSub ^| ^end ^footer ^]

"""


def expand_format(fmt_str, keys=None, max_depth=3):
    """Recursively formats the string until the format operation does nothing or
    max_depth is reached """
    if not keys:
        keys = messages

    keys = dict(keys)  # don't mutate original
    keys.update({'%' + k: urllib.parse.quote(v) for k, v in keys.items()})

    for i in range(max_depth):
        new_str = fmt_str.format(**keys)
        if fmt_str == new_str:
            break
        fmt_str = new_str
    return fmt_str


def get_footer(subreddit):
    """Gets the formatted footer as specified by footer_items"""
    values = {'subreddit': subreddit}
    values.update(messages)

    def super_script(content):
        if isinstance(content, str):
            return re.sub('(^\s*|\s+)(\S)', '\\1^\\2', expand_format(content, values))

        if isinstance(content, list):
            return super_script('[ ') + super_script(' | ').join(
                super_script(item) for item in content) + super_script(' ]')

        if isinstance(content, tuple):
            text, link = content
            return '[%s](%s)' % (super_script(text), expand_format(link, values))

    return super_script(footer_items)


def get_message(message_id):
    """Gets the associated message as specified in messages"""
    return expand_format(messages.get(message_id, ''))


def get_intent(message):
    """Gets the relevant intent, a member of intents, or None if no intent is found.
    Uses a very naive fuzzy search, which is case, punctuation, and space insensitive. """
    content = message.subject + message.body
    letters = re.sub('\W', '', content).lower()
    for intent in intents:
        flag = re.sub('\W', '', get_message(intent)).lower()
        if flag in letters:
            return intent
    return None
