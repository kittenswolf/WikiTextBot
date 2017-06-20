# WikiTextBot made by https://github.com/kittenswolf
# Bot in action: reddit.com/u/WikiTextBot
# reddit.com/u/kittens_from_space

import praw

delete_threshold = -1

bot_username = "WikiTextBot"
print("Logging in...")
reddit = praw.Reddit(user_agent='*',
                     client_id="*", client_secret="*",
                     username=bot_username, password="*")
print("Logged in.")

print("Checking comments..")
                     
for comment in reddit.redditor(bot_username).comments.controversial('all', limit=None):
    if comment.score <= delete_threshold:
        comment.delete()
        print(str(comment.score) + " got removed")
        
print("Done!")
              
