msg_cache_file = "cache/msg_cache.txt"
cache_file = "cache/com_cache.txt"
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
    [exclude_strings[0],
     "https://reddit.com/message/compose?to=WikiTextBot&message=" + exclude_strings[0].replace(" ", "") + "&subject=" +
     exclude_strings[0].replace(" ", "")],
    [exclude_strings[1], "https://np.reddit.com/r/SUBREDDITNAMEHERE/about/banned"],
    ["FAQ / Information", "https://np.reddit.com/r/WikiTextBot/wiki/index"],
    ["Source", "https://github.com/kittenswolf/WikiTextBot"],
    ["Donate", "https://www.reddit.com/r/WikiTextBot/wiki/donate"]
]

downvote_remove = "^Downvote ^to ^remove"

footer_seperator = "^|"

disallowed_strings = ["List of", "Glossary of", "Category:", "File:", "Wikipedia:"]
body_disallowed_strings = [
    "From a modification: This is a redirect from a modification of the target's title or a closely related title. For example, the words may be rearranged, or punctuation may be different.",
    "From a miscapitalisation: This is a redirect from a miscapitalisation. The correct form is given by the target of the redirect.",
    "{\displaystyle"]

errors_to_not_print = ["received 403 HTTP response"]

media_extensions = [".png", ".jpeg", ".jpg", ".bmp", ".svg", ".mp4", ".webm", "gif", ".gifv", ".flv", ".wmv", ".amv"]

intro_wikipedia_link = "https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&explaintext=&exintro=&exsentences=NUMHERE__1&titles="
