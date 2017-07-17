exclude_user_text = 'Exclude Me'
exclude_sub_text = 'Exclude From Subreddit'
include_user_text = 'Include Me'

exclude_user_flag = exclude_user_text.lower().replace(' ', '')
include_user_flag = include_user_text.lower().replace(' ', '')

user_already_excluded = "You already seem to be excluded from the bot.\n\nTo be included again, message me '" + include_user_text + "'.\n\nHave a nice day!"
user_exclude_done = "Done! If you want to be included again, message me '" + include_user_text + "'.\n\nHave a nice day!"
user_include_done = "Done!\n\nHave a nice day!"
user_not_excluded = "It seems you are not excluded from the bot. If you think this is false, [message](https://www.reddit.com/message/compose?to=kittens_from_space) me.\n\nHave a nice day!"

footer_links = [
    ["PM", "https://www.reddit.com/message/compose?to=kittens_from_space"],
    ["{excludeuser}",
     "https://reddit.com/message/compose?to=WikiTextBot&message={excludeuser}&subject={excludeuser}"],
    ["{excludesub}", "https://np.reddit.com/r/{subreddit}/about/banned"],
    ["FAQ / Information", "https://np.reddit.com/r/WikiTextBot/wiki/index"],
    ["Source", "https://github.com/kittenswolf/WikiTextBot"]
]

downvote_remove = "^Downvote ^to ^remove"

footer_seperator = "^|"

disallowed_strings = ["List of", "Glossary of", "Category:", "File:", "Wikipedia:"]
body_disallowed_strings = [
    "From a modification: This is a redirect from a modification of the target's title "
    "or a closely related title. For example, the words may be rearranged, or "
    "punctuation may be different.",
    "From a miscapitalisation: This is a redirect from a miscapitalisation. The correct "
    "form is given by the target of the redirect.",
    "{\displaystyle"
]


def replace_right(source, target, replacement, replacements=None):
    return replacement.join(source.rsplit(target, replacements))


def generate_footer(subreddit):
    footer = "^[ "

    vals = {
        'excludeuser': exclude_user_text,
        'excludesub': exclude_sub_text,
        'subreddit': str(subreddit)
    }

    links = []
    for text, url in footer_links:
        text = text.format(**vals)
        url = url.format(**vals)
        final_desc = "^" + text.format(**vals).replace(" ", " ^")
        final_link = "[" + final_desc + "](" + url.format(**vals) + ")"
        links.append(final_link)

    for link in links:
        footer += link
        footer += " " + footer_seperator + " "

    footer += " ^]"
    footer = replace_right(footer, footer_seperator, "", 1)

    footer += "\n" + downvote_remove + " ^| ^v0.24"

    return footer
