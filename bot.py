# WikiTextBot made by https://github.com/kittenswolf
# Bot in action: reddit.com/u/WikiTextBot
# reddit.com/u/kittens_from_space

from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import wikipedia
import random
import time
import praw
import praw.exceptions
import prawcore
import persistentlist as pl

# Settings

msg_cache = pl.PersistentList('cache/msg_cache.txt')
com_cache = pl.PersistentList('cache/com_cache.txt')
user_blacklist = pl.PersistentList('user_blacklist.txt', mapf=str.lower)  # case insensitive comparisons
bot_blacklist = pl.PersistentList('bot_blacklist.txt', mapf=str.lower)

# bd_debug = False

comment_threshold = 500
num_sentences = 4

bot_username = "WikiTextBot"

exclude = ["Exclude me", "Exclude from subreddit"]
include = "IncludeMe"

user_already_excluded = "You already seem to be excluded from the bot.\n\nTo be included again, message me '" + include + "'.\n\nHave a nice day!"
user_exclude_done = "Done! If you want to be included again, message me '" + include + "'.\n\nHave a nice day!"
user_include_done = "Done!\n\nHave a nice day!"
user_not_excluded = "It seems you are not excluded from the bot. If you think this is false, [message](https://www.reddit.com/message/compose?to=kittens_from_space) me.\n\nHave a nice day!"

footer_links = [
    ["PM", "https://www.reddit.com/message/compose?to=kittens_from_space"],
    [exclude[0],
     "https://reddit.com/message/compose?to=WikiTextBot&message=" + exclude[0].replace(" ", "") + "&subject=" + exclude[
         0].replace(" ", "")],
    [exclude[1], "https://np.reddit.com/r/SUBREDDITNAMEHERE/about/banned"],
    ["FAQ / Information", "https://np.reddit.com/r/WikiTextBot/wiki/index"],
    ["Source", "https://github.com/kittenswolf/WikiTextBot"]
]

downvote_remove = "^Downvote ^to ^remove"

footer_seperator = "^|"

disallowed_strings = ["List of", "Glossary of", "Category:", "File:", "Wikipedia:"]
body_disallowed_strings = [
    "From a modification: This is a redirect from a modification of the target's title or a closely related title. For example, the words may be rearranged, or punctuation may be different.",
    "From a miscapitalisation: This is a redirect from a miscapitalisation. The correct form is given by the target of the redirect.",
    "{\displaystyle"]

errors_to_not_print = ["received 403 HTTP response"]


def unique(seq):
    seen = set()
    for value in seq:
        if value not in seen:
            seen.add(value)
            yield value


def replace_right(source, target, replacement, replacements=None):
    return replacement.join(source.rsplit(target, replacements))


def locateByName(e, name):
    if e.get('name', None) == name:
        return e

    for child in e.get('children', []):
        result = locateByName(child, name)
        if result is not None:
            return result

    return None


def get_wikipedia_articles(input_text):
    """Gets en.wikipedia.org link in input_text. If it can't be found, returns []"""

    def get_article(url):
        if url.netloc.endswith('.wikipedia.org'):
            if url.path == '/w/index.php':
                info = urllib.parse.parse_qs(url.query)
                return info['title'][0], ''  # todo: avoid [0] if possible
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


def generate_footer():
    footer = "^[ "

    links = []
    for link in footer_links:
        final_desc = "^" + link[0].replace(" ", " ^")
        final_link = "[" + final_desc + "](" + link[1] + ")"
        links.append(final_link)

    for link in links:
        footer += link
        footer += " " + footer_seperator + " "

    footer += " ^]"
    footer = replace_right(footer, footer_seperator, "", 1)

    footer += "\n" + downvote_remove + " ^| ^v0.24"

    return footer


def generate_comment(articles):
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

    done_comment.append(generate_footer())
    comment = ''.join(done_comment)

    return comment


if __name__ == '__main__':
    print("Logging in..")
    reddit = praw.Reddit(user_agent='*',
                         client_id="*", client_secret="*",
                         username=bot_username, password="*")
    print("Logged in.")


    def monitor_messages():
        for message in reddit.inbox.messages(limit=100):
            if message.id in msg_cache:
                continue

            msg_cache.append(message.id)

            author = str(message.author)

            if author == bot_username:
                continue

            if exclude[0].replace(" ", "").lower() == message.subject.lower():
                if author in user_blacklist:
                    message.reply(user_already_excluded)
                else:
                    print("Excluding the user '" + author + "'")
                    user_blacklist.append(author)
                    message.reply(user_exclude_done)

            if include.lower() == message.subject.lower():
                if author in user_blacklist:
                    print("Including the user '" + author + "'")
                    user_blacklist.remove(author)
                    message.reply(user_include_done)
                else:
                    message.reply(user_not_excluded)


    def monitor_comments():
        for comment in reddit.subreddit('all').comments(limit=100):
            if comment.id in com_cache:
                continue

            com_cache.append(comment.id)

            if 'wikipedia.org/wiki/' not in str(comment.body).lower():
                continue

            if comment.author in user_blacklist or comment.author in bot_blacklist:
                continue

            articles = get_wikipedia_articles(comment.body_html)

            if not articles:
                continue

            # todo move this to footer generation
            comment_text = generate_comment(articles).replace("SUBREDDITNAMEHERE", str(comment.subreddit))

            if comment_text == "Error":
                continue

            print('Replying to ' + str(comment.author) + ' in /r/' + str(
                comment.subreddit) + ": " + comment.link_permalink + comment.id)
            print('=' * 100)
            print(comment_text)
            print('=' * 100)

            comment.reply(comment_text)


    while True:
        try:
            monitor_messages()
            monitor_comments()
            time.sleep(.5)
        except praw.exceptions.APIException as e:
            print('ratelimit hit, sleeping 100 secs.')
            time.sleep(100)
        except Exception as e:
            # catch-all to keep bot from shutting down.
            print(repr(e))
