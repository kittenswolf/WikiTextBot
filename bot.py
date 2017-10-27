# WikiTextBot made by https://github.com/kittenswolf
# Bot in action: reddit.com/u/WikiTextBot
# reddit.com/u/kittens_from_space

import time
class logger:
    def log(*, type, message):
        print("[" + time.ctime() + "] [" + str(type) + "]: " + str(message))

from bs4 import BeautifulSoup
import urllib.request
import functools
import wikipedia
import sentences
import traceback
import json
import praw
import re

# Settings 

msg_cache_file      = "cache/msg_cache.txt"
cache_file          = "cache/com_cache.txt"
user_blacklist_file = "user_blacklist.txt"

num_sentences = 4

bot_username = "WikiTextBot"

exclude_strings = ["Exclude me", "Exclude from subreddit"]
include = "IncludeMe"

user_already_excluded = "You already seem to be excluded from the bot.\n\nTo be included again, message me '" + include + "'.\n\nHave a nice day!"
user_exclude_done = "Done! If you want to be included again, message me '" + include + "'.\n\nHave a nice day!"
user_include_done = "Done!\n\nHave a nice day!"
user_not_excluded = "It seems you are not excluded from the bot. If you think this is false, [message](https://www.reddit.com/message/compose?to=kittens_from_space) me.\n\nHave a nice day!"

footer_links = [ 
                 ["PM", "https://www.reddit.com/message/compose?to=kittens_from_space"],
                 [exclude_strings[0], "https://reddit.com/message/compose?to=WikiTextBot&message=" + exclude_strings[0].replace(" ", "") + "&subject=" + exclude_strings[0].replace(" ", "")],
                 [exclude_strings[1], "https://np.reddit.com/r/SUBREDDITNAMEHERE/about/banned"],
                 ["FAQ / Information", "https://np.reddit.com/r/WikiTextBot/wiki/index"],
                 ["Source", "https://github.com/kittenswolf/WikiTextBot"],
                 ["Donate", "https://www.reddit.com/r/WikiTextBot/wiki/donate"]
               ]
               
downvote_remove = "^Downvote ^to ^remove"
               
footer_seperator = "^|"

disallowed_strings = ["List of", "Glossary of", "Category:", "File:", "Wikipedia:"]
body_disallowed_strings = ["From a modification: This is a redirect from a modification of the target's title or a closely related title. For example, the words may be rearranged, or punctuation may be different.", "From a miscapitalisation: This is a redirect from a miscapitalisation. The correct form is given by the target of the redirect.", "{\displaystyle"]


errors_to_not_print = ["received 403 HTTP response"]

media_extensions = [".png", ".jpeg", ".jpg", ".bmp", ".svg", ".mp4", ".webm", "gif", ".gifv", ".flv", ".wmv", ".amv"]

intro_wikipedia_link = "https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&explaintext=&exintro=&exsentences=NUMHERE__1&titles="

logger.log(type="INFO", message="Logging in...")
reddit = praw.Reddit(user_agent='*',
                     client_id="*", client_secret="*",
                     username=bot_username, password="*")
logger.log(type="INFO", message="Logged in.")


def replace_right(source, target, replacement, replacements=None):
    return replacement.join(source.rsplit(target, replacements))

def get_cache(file):
    """Gets the cache from $file and clears to len(comment_threshold) if necesarry. Also saves it after."""
    try:
        raw_cache = open(file, "r").read()
    except Exception as e:
        logger.log(type="ERRROR", message="{} doesn't exist?".format(file))
        return []
        
    cache = [id for id in raw_cache.split("\n")]
    return [item for item in cache if not item == '']
    
def input_cache(file, input):
    try:
        with open(file, "a") as f:
            f.write(input + "\n")
    except Exception as e:
        logger.log(type="ERRROR", message="{} doesn't exist?".format(file))
        return

def locateByName(e, name):
    if e.get('name',None) == name:
        return e

    for child in e.get('children',[]):
        result = locateByName(child,name)
        if result is not None:
            return result

    return None

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
                if final_text == []:
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
        logger.log(type="INFO", message="Error '{}' in get_wiki_text() with link {}".format(e, original_link))
        return "Error"
       
       
class generate_comment:
       
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

    def generate_comment(input_urls, comment_text=None):
        comment      = []
        content      = []
        done_comment = []

        for url in input_urls:
            url_content = get_wiki_text(url)
        
            if not url_content == "Error":
                content.append(url_content)
            
            if url_content[1].split(".")[0] in comment_text:
                return "Error"

        for chunk in content:
            title = chunk[0]
            body  = chunk[1]
        
            body = body.replace("\n", "\n\n")

            comment.append("**" + title + "**\n")
            comment.append(body)
            comment.append("\n***\n")

        if comment == []:
            return "Error"

        for line in comment:
            done_comment.append(line + "\n")

        done_comment.append(generate_comment.generate_footer())
        comment = ''.join(done_comment)

        return comment
        
        
class exclude:
    def check_excluded(file, input_user):
        try:
            raw_file = open(file, "r").read()
        except Exception as e:
            logger.log(type="ERRROR", message="{} doesn't exist?".format(file))
            return
        
        current_excluded = [user.lower() for user in raw_file.split("\n")]
    
        if input_user.lower() in current_excluded:
            return True
        else:
            return False
        
    def excludeUser(file, input_user):
        try:
            raw_file = open(file, "r").read()
        except Exception as e:
            logger.log(type="ERRROR", message="{} doesn't exist?".format(file))
            return
        
        current_excluded = [user.lower() for user in raw_file.split("\n") if not user.replace(" ", "") == ""]
        current_excluded.append(input_user)
    
        with open(file, "w") as f:
            for user in current_excluded:
                f.write(user + "\n")
            
    def includeUser(file, input_user):
        try:
            raw_file = open(file, "r").read()
        except Exception as e:
            logger.log(type="ERRROR", message="{} doesn't exist?".format(file))
            return
        
        try:
            current_excluded = [user.lower() for user in raw_file.split("\n")]
            current_excluded.remove(input_user)
        except Exception:
            pass
    
        with open(file, "w") as f:
            for user in current_excluded:
                f.write(user + "\n")
            


def monitorMessages():
    """Monitors the newest 100 messages and excludes/includes users requesting it."""

    for message in reddit.inbox.messages(limit=100):
        current_msg_cache = get_cache(msg_cache_file)
        
        if not message.id in current_msg_cache:
            author = str(message.author)
    
            if not author == bot_username:
            
                if exclude_strings[0].replace(" ", "").lower() == message.subject.lower():
                    already_excluded = exclude.check_excluded(user_blacklist_file, author) 

                    if already_excluded == True:
                        message.reply(user_already_excluded)
                    else:
                        logger.log(type="INFO", message="Excluding user {}".format(author))
                        exclude.excludeUser(user_blacklist_file, author)
                        message.reply(user_exclude_done)
                
                if include.lower() == message.subject.lower():
                    already_excluded = exclude.check_excluded(user_blacklist_file, author)
            
                    if already_excluded == True:
                        logger.log(type="INFO", message="Including user {}".format(author))
                        exclude.includeUser(user_blacklist_file, author)
                        message.reply(user_include_done)
                    else:
                        message.reply(user_not_excluded)
                
                
            input_cache(msg_cache_file, message.id)
            
            
def parse_comment(comment):
    if not any(item in str(comment.body).lower() for item in ["en.wikipedia.org/wiki/", "en.m.wikipedia.org/wiki/"]):
        return
        
    if exclude.check_excluded(user_blacklist_file, str(comment.author)) == True:
        return
        
    if comment.id in get_cache(cache_file):
        return
        
    urls = get_wikipedia_links(comment.body_html)
    
    if not urls == []:
        comment_text = generate_comment.generate_comment(urls, comment_text=str(comment.body))
        comment_text = comment_text.replace("SUBREDDITNAMEHERE", str(comment.subreddit))

        if not comment_text == "Error":
            logger.log(type="INFO", message="Replying to user {} in subreddit /r/{}".format(comment.author, comment.subreddit))
            comment.reply(comment_text)
            
    input_cache(cache_file, comment.id)
            
            

def main():
    monitorMessages()
    for comment in reddit.subreddit('all').comments(limit=100):
        parse_comment(comment)


while True:
    try:
        main()
    except Exception as e:
        if e == praw.exceptions.APIException:
            logger.log(type="ERRROR", message="Ratelimit hit, sleeping 100 secs")
            time.sleep(100)
            
        if not str(e) in errors_to_not_print:
            logger.log(type="ERRROR", message=e)

            traceback.print_exc()
        
        
        time.sleep(0.5)
