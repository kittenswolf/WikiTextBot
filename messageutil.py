import re
import urllib.parse

exclude_user_text = 'Exclude Me'
exclude_sub_text = 'Exclude From Subreddit'
include_user_text = 'Include Me'

exclude_user_flag = exclude_user_text.lower().replace(' ', '')
include_user_flag = include_user_text.lower().replace(' ', '')

# %value indicates url-quoted version of normal value
# if exclude_user is 'Exclude me' then %exclude_user is 'Exclude%20me'
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

# todo proper documentation of how value formatting works
# get_footer also gives the 'subreddit' key for the current subreddit
footer_items = [
    ('PM', '{pm_link}'),
    ('{exclude_user}', '{exclude_link}'),
    ('{exclude_sub}', 'https://np.reddit.com/r/{subreddit}/about/banned'),
    ('FAQ / Information', 'https://np.reddit.com/r/WikiTextBot/wiki/index'),
    ('Source', 'https://github.com/kittenswolf/WikiTextBot'),
    'Downvote to remove',
    'v0.24'
]

disallowed_strings = ["List of", "Glossary of", "Category:", "File:", "Wikipedia:"]
body_disallowed_strings = [
    "From a modification: This is a redirect from a modification of the target's title "
    "or a closely related title. For example, the words may be rearranged, or "
    "punctuation may be different.",
    "From a miscapitalisation: This is a redirect from a miscapitalisation. The correct "
    "form is given by the target of the redirect.",
    "{\displaystyle"
]


def expand_format(fmt_str, keys=None, max_depth=3):
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
    return expand_format(messages.get(message_id, ''))
