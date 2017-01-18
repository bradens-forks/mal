#!/usr/bin/env python
# coding=utf-8
#
#   Python Script
#
#   Copyright © Manoel Vilela
#
#

# stdlib
import sys
import math
from operator import itemgetter
from datetime import date

# self-package
from mal.api import MyAnimeList
from mal import color


def report_if_fails(response):
    if response != 200:
        print(color.colorize("Failed with HTTP: {}".format(response), 'red'))


def select_item(items):
    """Select a single item from a list of results."""
    item = None
    if len(items) > 1:  # ambigious search results
        print(color.colorize('Multiple results:', 'cyan'))
        # show user the results and make them choose one
        for index, title in enumerate(map(itemgetter('title'), items)):
            print('{index}: {title}'.format_map(locals()))
        index = int(input('Which one? '))
        item = items[index]
    elif len(items) == 1:
        item = items[0]
    else:
        print(color.colorize("No matches in list ᕙ(⇀‸↼‶)ᕗ", 'red'))
        sys.exit(1)

    return item


def start_end(entry, episode, total_episodes):
    """Fill details of anime if user just started it or finished it."""
    if total_episodes == episode:
        entry['status'] = MyAnimeList.status_codes['completed']
        entry['date_finish'] = date.today().strftime('%m%d%Y')
        print(color.colorize('Series completed!', 'green'))
        score = int(input('Enter a score (or 0 for no score): '))
        if score != 0:
            entry['score'] = score
    elif episode == 1:
        entry['status'] = MyAnimeList.status_codes['watching']
        entry['date_start'] = date.today().strftime('%m%d%Y')

    return entry


def remove_completed(items):
    # remove animes that are already completed
    # preserves (rewatching)
    for index, status in enumerate(map(itemgetter('status_name'), items)):
        if status == 'completed':
            del items[index]

    return items


def progress_update(mal, regex, inc):
    items = remove_completed(mal.find(regex))
    item = select_item(items)  # also handles ambigious searches
    episode = item['episode'] + inc
    entry = dict(episode=episode)
    template = {
        'title': color.colorize(item['title'], 'yellow', 'bold'),
        'episode': color.colorize(episode, 'red' if inc < 1 else 'green'),
        'total_episodes': color.colorize(item['total_episodes'], 'cyan'),
        'procedure': color.procedure_color(inc)
    }

    print(('{procedure} progress for {title} to '
           '{episode}/{total_episodes}'.format_map(template)))

    entry = start_end(entry, episode, item['total_episodes'])
    response = mal.update(item['id'], entry)
    report_if_fails(response)


def drop(mal, regex):
    """Drop a anime based a regex expression"""
    items = remove_completed(mal.find(regex))
    item = select_item(items)
    entry = dict(status=mal.status_codes['dropped'])
    old_status = mal.status_names[item['status']]
    template = {
        'title': color.colorize(item['title'], 'yellow', 'bold'),
        'old-status': color.colorize(old_status, 'green', 'bold'),
        'action': color.colorize('Dropping', 'red', 'bold')

    }

    print(('{action} anime {title} from list '
           '{old-status}'.format_map(template)))
    response = mal.update(item['id'], entry)
    report_if_fails(response)


def stats(mal):
    """Print user anime stats."""
    # get all the info
    animes = mal.list(get_stats=True)
    user_info = animes['stats']

    # do the maths needed

    # print info
    for stat in ['watching', 'completed', 'onhold', 'dropped', 'plantowatch']:
        print('{}: {}'.format(stat.capitalize(), user_info[stat]))

def find(mal, regex, filtering='all', extra=False):
    """Find all anime in a certain status given a regex."""
    items = mal.find(regex, extra=extra)
    if len(items) == 0:
        print(color.colorize("No matches in list ᕙ(⇀‸↼‶)ᕗ", 'red'))
        return

    # filter the results if necessary
    if filtering != 'all':
        items = [x for x in items if x['status_name'] == filtering]

    n_items = color.colorize(str(len(items)), 'cyan', 'underline')
    print("Matched {} items:".format(n_items))

    # pretty print all the animes found
    sorted_items = sorted(items, key=itemgetter('status'), reverse=True)
    for index, item in enumerate(sorted_items):
        anime_pprint(index + 1, item, extra=extra)


def anime_pprint(index, item, extra=False):
    """Pretty print an anime's information."""
    padding = int(math.log10(index)) + 3
    remaining_color = ('blue' if item['episode'] < item['total_episodes']
                       else 'green')
    remaining = '{episode}/{total_episodes}'.format_map(item)
    in_rewatching = ('#in-rewatching-{rewatching}'.format_map(item)
                     if item['rewatching'] else '')
    template = {
        'index': index,
        'padding': ' ' * padding,
        'status': MyAnimeList.status_names[item['status']].capitalize(),
        'title': color.colorize(item['title'], 'red', 'bold'),
        'remaining': color.colorize(remaining, remaining_color, 'bold'),
        'score': color.score_color(item['score']),
        'rewatching': (color.colorize(in_rewatching, 'yellow', 'bold'))
    }
    # add formating options for extra info
    if extra:
        template.update({
            'start': item['start_date'] if item['start_date'] != '0000-00-00' else 'NA',
            'finish': item['finish_date'] if item['finish_date'] != '0000-00-00' else 'NA',
            'tags': item['tags']
        })

    message_lines = [
        "{index}: {title}".format_map(template),
        ("{padding}{status} at {remaining} episodes "
         "with score {score} {rewatching}".format_map(template))
    ]

    # the extra information lines
    if extra:
        message_lines.extend([
            "{padding}Started: {start} \t Finished: {finish}".format_map(template),
            "{padding}Tags: {tags}".format_map(template)
        ])

    print('\n'.join(message_lines), "\n")
