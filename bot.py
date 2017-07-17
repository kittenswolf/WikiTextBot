# WikiTextBot made by https://github.com/kittenswolf
# Bot in action: reddit.com/u/WikiTextBot
# reddit.com/u/kittens_from_space

import time
import urllib.parse
import urllib.request

import praw.exceptions
import wikipedia
from bs4 import BeautifulSoup

import messageutil as mu
import persistentlist as pl

from collections import ChainMap

# Settings

msg_cache = pl.PersistentList('cache/msg_cache.txt')
com_cache = pl.PersistentList('cache/com_cache.txt')
user_blacklist = pl.PersistentList('user_blacklist.txt', mapf=str.lower)  # ignore case
bot_blacklist = pl.PersistentList('bot_blacklist.txt', mapf=str.lower)

login_info = {
    'user_agent': 'PRAW bot for /u/WikiTextBot',
    'client_id': '*',
    'client_secret': '*',
    'username': 'WikiTextBot',
    'password': '*'
}

errors_to_not_print = ["received 403 HTTP response"]
errors_to_quit = ["received 401 HTTP response"]

disallowed_strings = ["List of", "Glossary of", "Category:", "File:", "Wikipedia:"]
body_disallowed_strings = [
    "From a modification: This is a redirect from a modification of the target's title "
    "or a closely related title. For example, the words may be rearranged, or "
    "punctuation may be different.",
    "From a miscapitalisation: This is a redirect from a miscapitalisation. The correct "
    "form is given by the target of the redirect.",
    "{\displaystyle"
]


def unique(seq):
    seen = set()
    for value in seq:
        if value not in seen:
            seen.add(value)
            yield value


def get_wikipedia_articles(input_text):
    def get_article(url):
        if url.netloc.endswith('.wikipedia.org'):
            if url.path == '/w/index.php':
                info = urllib.parse.parse_qs(url.query)
                return info['title'][0], url.fragment.replace('_', ' ')
            elif url.path.startswith('/wiki/'):
                return url.path[6:].replace('_', ' '), url.fragment.replace('_', ' ')

        return None

    soup = BeautifulSoup(input_text, "html.parser")
    urls = [urllib.parse.urlparse(a['href']) for a in soup.findAll('a')]

    articles = map(get_article, urls)
    articles = filter(None, articles)
    articles = list(unique(articles))

    return articles


def get_wiki_text(article, section):
    try:
        if any(s.lower() in article.lower() for s in disallowed_strings):
            return 'Error'

        page = wikipedia.page(article)

        if section:
            heading = article + ': ' + section
            text = page.section(section)
        else:
            heading = article
            text = page.summary

        if not text:  # page or section does not exist
            return 'Error'
        if any(s.lower() in text.lower() for s in body_disallowed_strings):
            return 'Error'
        text = text.partition('\n')[0]  # get the first paragraph

        return [heading, text]
    except wikipedia.WikipediaException as e:
        print(repr(e))
        return 'Error'


def generate_comment(articles, subreddit):
    comment = []
    content = []
    done_comment = []

    for article, heading in articles:
        url_content = get_wiki_text(article, heading)

        if url_content != "Error":
            content.append(url_content)

    for chunk in content:
        title, body = chunk

        body = body.replace("\n", "\n\n")

        comment.append("**" + title + "**\n")
        comment.append(body)
        comment.append("\n***\n")

    if not comment:
        return "Error"

    for line in comment:
        done_comment.append(line + "\n")

    done_comment.append(mu.get_footer(subreddit))
    comment = ''.join(done_comment)

    return comment


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='client_id')
    parser.add_argument('-s', dest='client_secret')
    parser.add_argument('-u', dest='username')
    parser.add_argument('-p', dest='password')
    parser.add_argument('--readonly', dest='readonly', nargs='?', type=bool, const=True,
                        default=False)

    args = parser.parse_args()

    read_only = args.readonly

    args = {k: v for k, v in vars(args).items() if v}
    cm = ChainMap(args, login_info)

    print("Logging in..")
    reddit = praw.Reddit(**cm)
    print('logged in to %s.' % reddit.user.me().name)

    def monitor_messages():
        for message in reddit.inbox.messages(limit=100):
            if message.id in msg_cache:
                continue

            msg_cache.append(message.id)

            author = str(message.author)

            if author == login_info['username']:
                continue

            intent = mu.get_intent(message)

            if intent == 'exclude_user':
                if author in user_blacklist:
                    message.reply(mu.get_message('user_exclude_failed'))
                else:
                    print("Excluding the user '" + author + "'")
                    user_blacklist.append(author)
                    if not read_only:
                        message.reply(mu.get_message('user_exclude_success'))
            elif intent == 'include_user':
                if author in user_blacklist:
                    print("Including the user '" + author + "'")
                    user_blacklist.remove(author)
                    if not read_only:
                        message.reply(mu.get_message('user_include_success'))
                else:
                    if not read_only:
                        message.reply(mu.get_message('user_include_failure'))

    def monitor_comments():
        for comment in reddit.subreddit("all").comments(limit=100):
            if comment.id in com_cache:
                continue

            com_cache.append(comment.id)

            if "wikipedia.org/wiki/" not in str(comment.body).lower():
                continue

            if comment.author in user_blacklist or comment.author in bot_blacklist:
                continue

            articles = get_wikipedia_articles(comment.body_html)

            if not articles:
                continue

            comment_text = generate_comment(articles, str(comment.subreddit))

            if comment_text == "Error":
                continue

            word = 'Generated reply' if read_only else 'Replying'
            print('%s to %s in /r/%s %s', (
                word,
                comment.author,
                comment.subreddit,
                comment.link_permalink + comment.id))

            print("=" * 100)
            print(comment_text)
            print("=" * 100)

            if not read_only:
                comment.reply(comment_text)

    while True:
        try:
            monitor_messages()
            monitor_comments()
            time.sleep(.5)
        except praw.exceptions.APIException as e:
            print("rate limit hit, sleeping 100 secs.")
            time.sleep(100)
        except Exception as e:
            # catch-all to keep bot from shutting down.
            if str(e) not in errors_to_not_print:
                print(repr(e))
            if str(e) in errors_to_quit:
                return


if __name__ == '__main__':
    main()
