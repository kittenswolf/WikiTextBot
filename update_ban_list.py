# -*- coding: utf-8 -*-

import praw
import subprocess

home_sub = "WikiTextBot"
start_signal = "^^^^^^^^^^^^^^^^Start"

print("Logging in..")
reddit = praw.Reddit(user_agent='*',
                     client_id="*", client_secret="*",
                     username="*", password="*")
print("Logged in.")

def get_all_banned():
    """Gets list of the subreddits the bot is currently banned in. Fresh data: pulls it from inbox"""

    banned_list = []
    for message in reddit.inbox.messages(limit=350):
        if "banned" in str(message.subject).lower():
            sub = str(message.subject).split("r/")[1]
            banned_list.append(sub)
            
    done_bans = []
    for i in banned_list:
        if i not in done_bans:
            done_bans.append(i)
            
    return done_bans

def get_current_bans(wiki_page):
    """Gets list of the subreddits the bot is currently banned from. Pulls data from the banned wikipage in $homesub"""
    page = reddit.subreddit(home_sub).wiki[wiki_page].content_md
    list = page.split(start_signal)[1]
    list = list.split("|-|")[1]
    
    list_bans = [item.replace("|", "").replace("\r", "") for item in list.split("\n")]
    
    list = []
    for item in list_bans:
        if not item == '':
            list.append(item)
    
    return list
    
def enter_sub(wiki_page, input_sub):
    current_bans = get_current_bans(wiki_page)
    
    if input_sub in current_bans:
        return

    try:
        test = [comment for comment in reddit.subreddit(input_sub).comments(limit=1)]
    except Exception as e:
        return
        
    print("Adding " + input_sub)

    current_bans = current_bans + [input_sub]

    wikipage = reddit.subreddit(home_sub).wiki[wiki_page].content_md
    only_header = wikipage.split(start_signal)[0]
    
    new_list = ["|Subreddit|\n", "|-|\n"]
    
    for sub in current_bans:
        new_list.append("|" + sub + "|\n")
        
    list_part = ''.join(new_list)
    
    final_wikipage = only_header + start_signal + "\n\n" + list_part
    
    reddit.subreddit(home_sub).wiki[wiki_page].edit(final_wikipage)

def check_bans():
    bans = get_all_banned()
    
    for sub in bans:
        enter_sub("banned", sub)

check_bans()

