# WikiTextBot made by https://github.com/kittenswolf
# Bot in action: reddit.com/u/WikiTextBot
# reddit.com/u/kittens_from_space

import functools
import json
import re
import time
import traceback
import urllib.request

import praw
import wikipedia
from bs4 import BeautifulSoup

import bot_detector
import sentences
from constants import *
from logger import Logger, LogTypes

Logger.log(type=LogTypes.INFO, message="Logging in...")
reddit = praw.Reddit(user_agent='*',
                     client_id="*", client_secret="*",
                     username=bot_username, password="*")
Logger.log(type=LogTypes.INFO, message="Logged in.")

bot_detector.settings(reddit, False)


def replace_right(source, target, replacement, replacements=None):
    return replacement.join(source.rsplit(target, replacements))


def get_cache(file):
    """Gets the cache from $file and clears to len(comment_threshold) if necesarry. Also saves it after."""
    try:
        raw_cache = open(file, "r").read()
    except Exception as e:
        Logger.log(type=LogTypes.ERROR, message="{} doesn't exist?".format(file))
        return []

    cache = [id for id in raw_cache.split("\n")]
    return [item for item in cache if item != '']


def input_cache(file, input):
    try:
        with open(file, "a") as f:
            f.write(input + "\n")
    except Exception as e:
        Logger.log(type=LogTypes.ERROR, message="{} doesn't exist?".format(file))


def locateByName(e, name):
    if e.get('name', None) == name:
        return e

    for child in e.get('children', []):
        result = locateByName(child, name)

        if result is not None:
            return result


def get_wikipedia_links(input_text):
    """Gets en.wikipedia.org link in input_text. If it can't be found, returns []"""

    soup = BeautifulSoup(input_text, "lxml")

    fixed_urls = []
    urls = re.findall(r'(https?://[^\s]+)', input_text)

    for url in soup.findAll('a'):
        try:
            fixed_urls.append(url['href'])
        except Exception:
            pass

    """Deletes duplicates"""
    done_urls = []
    for i in fixed_urls:
        if i not in done_urls:
            done_urls.append(i)

    """Deletes urls that contain a file extension"""
    fixed_urls = []
    for url in done_urls:
        for extension in media_extensions:
            if not extension.lower() in url.lower():
                fixed_urls.append(url)
                break

    done_urls = []
    for url in fixed_urls:
        if "wikipedia.org/wiki/" in url:
            done_urls.append(url)

    soup.decompose()

    return done_urls


def get_wiki_text(original_link):
    wiki_subject = original_link.split("/wiki/")[1]

    if "#" in wiki_subject:
        try:
            # Anchor detected

            # First, get page id
            request_url = intro_wikipedia_link + wiki_subject
            request_url = request_url.replace("NUMHERE__1", str(num_sentences))

            response = urllib.request.urlopen(request_url).read().decode("utf-8")
            json_data = json.loads(response)
            page_id = [key for key in json_data["query"]["pages"]][0]

            ##

            wanted_anchor = wiki_subject.split("#")[1].replace("_", " ")

            wikipedia.set_lang(org_language)
            page = wikipedia.page(pageid=page_id)
            anchor_text = page.section(wanted_anchor)

            list_trimmed_text = sentences.split(anchor_text)[:num_sentences]

            final_text = []
            for sentence in list_trimmed_text:
                if not final_text:
                    final_text.append(sentence)
                else:
                    final_text.append(" " + sentence)

            trimmed_text = ''.join(final_text)

            if trimmed_text == '':
                return "Error"

            for string in disallowed_strings:
                if string.lower() in str(page.title).lower():
                    return "Error"

            for string in body_disallowed_strings:
                if string.lower() in trimmed_text.lower():
                    return "Error"

            return [page.title + ": " + wanted_anchor, trimmed_text]

        except Exception as e:
            return "Error"

    request_url = intro_wikipedia_link + wiki_subject
    request_url = request_url.replace("NUMHERE__1", str(num_sentences))

    try:
        response = urllib.request.urlopen(request_url).read().decode("utf-8")
        json_data = json.loads(response)
        page_key = [key for key in json_data["query"]["pages"]][0]

        title = json_data["query"]["pages"][page_key]["title"]
        body = json_data["query"]["pages"][page_key]["extract"]

        if body == '':
            return "Error"

        for string in disallowed_strings:
            if string.lower() in title.lower():
                return "Error"

        for string in body_disallowed_strings:
            if string.lower() in body.lower():
                return "Error"

        return [title, body]
    except Exception as e:
        Logger.log(type=LogTypes.INFO, message="Error '{}' in get_wiki_text() with link {}".format(e, original_link))
        return "Error"


class GenerateComment:
    @staticmethod
    @functools.lru_cache(maxsize=10)
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

        footer += "\n" + downvote_remove + " ^| ^v0.28"

        return footer

    @staticmethod
    def generate_comment(input_urls, comment_text=None):
        comment = []
        content = []
        done_comment = []

        for url in input_urls:
            url_content = get_wiki_text(url)

            if url_content != "Error":
                content.append(url_content)

            if url_content[1].split(".")[0] in comment_text:
                return "Error"

        for chunk in content:
            title = chunk[0]
            body = chunk[1]

            body = body.replace("\n", "\n\n")

            comment.append("**" + title + "**\n")
            comment.append(body)
            comment.append("\n***\n")

        if not comment:
            return "Error"

        for line in comment:
            done_comment.append(line + "\n")

        done_comment.append(GenerateComment.generate_footer())
        comment = ''.join(done_comment)

        return comment


class Exclude:
    @staticmethod
    def check_excluded(file, input_user):
        try:
            raw_file = open(file, "r").read()
        except Exception as e:
            Logger.log(type=LogTypes.ERROR, message="{} doesn't exist?".format(file))
            return

        current_excluded = [user.lower() for user in raw_file.split("\n")]

        return input_user.lower() in current_excluded

    @staticmethod
    def excludeUser(file, input_user):
        try:
            raw_file = open(file, "r").read()
        except Exception as e:
            Logger.log(type=LogTypes.ERROR, message="{} doesn't exist?".format(file))
            return

        current_excluded = [user.lower() for user in raw_file.split("\n") if not user.replace(" ", "") == ""]
        current_excluded.append(input_user)

        with open(file, "w") as f:
            for user in current_excluded:
                f.write(user + "\n")

    @staticmethod
    def include_user(file, input_user):
        try:
            raw_file = open(file, "r").read()
        except Exception as e:
            Logger.log(type=LogTypes.ERROR, message="{} doesn't exist?".format(file))
            return

        try:
            current_excluded = [user.lower() for user in raw_file.split("\n")]
            current_excluded.remove(input_user)

            with open(file, "w") as f:
                for user in current_excluded:
                    f.write(user + "\n")

        except Exception:
            return


def monitor_messages():
    """Monitors the newest 100 messages and excludes/includes users requesting it."""

    for message in reddit.inbox.messages(limit=100):
        current_msg_cache = get_cache(msg_cache_file)

        if not message.id in current_msg_cache:
            author = str(message.author)

            if author != bot_username:
                if exclude_strings[0].replace(" ", "").lower() == message.subject.lower():
                    already_excluded = Exclude.check_excluded(user_blacklist_file, author)

                    if already_excluded:
                        message.reply(user_already_excluded)
                    else:
                        Logger.log(type=LogTypes.INFO, message="Excluding user {}".format(author))
                        Exclude.excludeUser(user_blacklist_file, author)
                        message.reply(user_exclude_done)

                if include.lower() == message.subject.lower():
                    already_excluded = Exclude.check_excluded(user_blacklist_file, author)

                    if already_excluded:
                        Logger.log(type=LogTypes.INFO, message="Including user {}".format(author))
                        Exclude.include_user(user_blacklist_file, author)
                        message.reply(user_include_done)
                    else:
                        message.reply(user_not_excluded)

            input_cache(msg_cache_file, message.id)


def parse_comment(comment):
    if not any(item in str(comment.body).lower() for item in ["en.wikipedia.org/wiki/", "en.m.wikipedia.org/wiki/"]):
        return

    if Exclude.check_excluded(user_blacklist_file, str(comment.author)):
        return

    if comment.id in get_cache(cache_file):
        return

    # Emergency fix
    if comment.author.name in ["AutoModerator", "HelperBot_"]:
        return

    bot_score = bot_detector.calc_bot_score(comment.author.name)
    if bot_score > 34:
        Logger.log(type=LogTypes.INFO,
                   message="{} seems to be a bot (score: {}) Not responding.".format(comment.author.name, bot_score))
        return
    else:
        Logger.log(type=LogTypes.INFO,
                   message="{} has a score of {}, responding.".format(comment.author.name, bot_score))

    urls = get_wikipedia_links(comment.body_html)

    if urls:
        comment_text = GenerateComment.generate_comment(urls, comment_text=str(comment.body))
        comment_text = comment_text.replace("SUBREDDITNAMEHERE", str(comment.subreddit))

        if comment_text != "Error":
            Logger.log(type=LogTypes.INFO,
                       message="Replying to user {} in subreddit /r/{}".format(comment.author, comment.subreddit))
            comment.reply(comment_text)

    input_cache(cache_file, comment.id)


def main():
    monitor_messages()
    for comment in reddit.subreddit('all').comments(limit=100):
        parse_comment(comment)


while True:
    try:
        main()
    except Exception as e:
        if e == praw.exceptions.APIException:
            Logger.log(type=LogTypes.ERROR, message="Ratelimit hit, sleeping 100 secs")
            time.sleep(100)

        if not str(e) in errors_to_not_print:
            Logger.log(type=LogTypes.ERROR, message=e)

            traceback.print_exc()

        time.sleep(0.5)
