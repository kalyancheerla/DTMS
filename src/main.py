#!/usr/bin/env python3
import discord
import qbittorrentapi
import json
import shlex
from datetime import datetime

OTHER_CATEGORY = 'other'
MIN_UNWANTED_BYTES_LEN = 3

def init(configfile):
    with open(configfile, 'r') as f:
        return json.load(f)

configs = init('config/settings.json')
qb_config = configs['qbittorrent']
qbt_client = qbittorrentapi.Client(host=qb_config['HOST'],
                                   port=qb_config['PORT'],
                                   username=qb_config['USER'],
                                   password=qb_config['PASS'])

def get_torrents_list():
    data = ''
    for torrent in qbt_client.torrents_info():
        torrentname = torrent.name
        if len(torrentname) > 60: # 100bytes for each torrent
            torrentname = torrent.name[:60] + '...'
        data += f'{torrent.hash[:7]}: {torrentname} ' + \
                f'({torrent.category}/{torrent.state})\n'
    return data

def get_torrent_info(shorthash):
    data = 'INVALID SHORT HASH!'
    tzinfo = str(datetime.now().astimezone().tzinfo)
    # Maybe we can add more things to report here
    for torrent in qbt_client.torrents_info():
        if torrent.hash[:7] == shorthash:
            #print(json.dumps(torrent, sort_keys=True, indent=4))
            data = f'Name: {torrent.name}\n'
            data += f'Hash: {torrent.hash}\n'
            data += f'Category: {torrent.category}\n'
            data += f'State: {torrent.state}\n'
            data += f'Size: {torrent.total_size/(10**9):.2f}GB\n'
            timestamp = datetime.fromtimestamp(torrent.added_on) \
                        .strftime('%Y-%m-%d, %I:%M:%S %p ') + tzinfo
            data += f'Added On: {timestamp}\n'
            if torrent.completion_on < 0:
                data += f'Completed On:\n'
            else:
                timestamp = datetime.fromtimestamp(torrent.completion_on) \
                            .strftime('%Y-%m-%d, %I:%M:%S %p ') + tzinfo
                data += f'Completed On: {timestamp}\n'
            break
    return data

def add_torrent_link(magnetlink):
    data = qbt_client.torrents_add(urls=magnetlink,
                                   category=OTHER_CATEGORY,
                                   use_auto_torrent_management=True)
    return data

def delete_torrent(hashval):
    qbt_client.torrents_delete(delete_files=True,
                               torrent_hashes=hashval)
    return 'Ok.'

def pause_torrent(hashval):
    qbt_client.torrents_pause(torrent_hashes=hashval)
    return 'Ok.'

def resume_torrent(hashval):
    qbt_client.torrents_resume(torrent_hashes=hashval)
    return 'Ok.'

def rename_torrent(hashval, newname):
    try:
        qbt_client.torrents_rename(torrent_hash=hashval,
                                   new_torrent_name=newname)
        return 'Ok.'
    except:
        return 'INVALID HASH!'

def change_category(category, hashval):
    try:
        qbt_client.torrents_set_category(category=category,
                                         torrent_hashes=hashval)
        return 'Ok.'
    except:
        return 'INVALID CATEGORY'

def get_torrent_file_info(hashval):
    data = ''
    try:
        for fileobj in qbt_client.torrents_files(torrent_hash=hashval):
            data += f'{fileobj.name} ({fileobj.size/(10**9):.2f}GB)'
            data += f' ({fileobj.progress:.3f})\n'
    except:
        data = 'INVALID HASH'
    return data

def rename_torrent_file(hashval, oldname, newname):
    try:
        qbt_client.torrents_rename_file(torrent_hash=hashval,
                                        old_path=oldname,
                                        new_path=newname)
    except:
        return 'INVALID HASH/NO SUCH FILE'
    return 'Ok.'

def strip_unwanted_names(hashval, unwanted):
    try:
        for fileobj in qbt_client.torrents_files(torrent_hash=hashval):
            newname = fileobj.name.replace(unwanted, '')
            qbt_client.torrents_rename_file(torrent_hash=hashval,
                                            old_path=fileobj.name,
                                            new_path=newname)
        return 'Ok.'
    except:
        return 'INVALID HASH'

bot = discord.Client()

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # split the message.content
    try:
        msglist = shlex.split(message.content)
    except ValueError:
        msglist = message.content.split()

    # assign response
    response = ''

    # simple hello message
    if msglist[0] == '$hello' and len(msglist) == 1:
        response = "Hey!\nI'm a BOT & I'm very happy to serve you."

    # list all torrents
    elif msglist[0] == '$list' and len(msglist) == 1:
        response = get_torrents_list()

    # info of a torrent
    elif msglist[0] == '$info' and len(msglist) == 2:
        response = get_torrent_info(msglist[1])

    # add torrent/torrents (magnet links only) (default category: other)
    # ['URL'] or ['URL2', 'URL2', ...]
    elif msglist[0] == '$add' and len(msglist) >= 2:
        response = add_torrent_link(msglist[1:])

    # delete torrent/torrents (using hashes)
    # ['all'] or ['hash'] or ['hash1', 'hash2', ...]
    elif msglist[0] == '$del' and len(msglist) >= 2:
        response = delete_torrent(msglist[1:])

    # pause torrent/torrents (using hashes)
    # ['all'] or ['hash'] or ['hashe1', 'hash2', ...]
    elif msglist[0] == '$pause' and len(msglist) >= 2:
        response = pause_torrent(msglist[1:])

    # resume torrent/torrents (using hashes)
    # ['all'] or ['hash'] or ['hashe1', 'hash2', ...]
    elif msglist[0] == '$resume' and len(msglist) >= 2:
        response = resume_torrent(msglist[1:])

    # info on files of a torrent
    elif msglist[0] == '$fileinfo' and len(msglist) == 2:
        response = get_torrent_file_info(msglist[1])

    # ['$changecategory', 'category', 'hash1', 'hash2', ...]
    elif msglist[0] == '$changecategory' and len(msglist) >= 3:
        response = change_category(msglist[1], msglist[2:])

    # Send the file name in qoutes
    # ['$rename', 'hash', 'newname part1', 'part2', ...]
    elif msglist[0] == '$rename' and len(msglist) >= 3:
        response = rename_torrent(msglist[1], ' '.join(msglist[2:]))

    # Send the file names in qoutes
    # ['$renamefile', 'hash', 'oldname', 'newname']
    elif msglist[0] == '$renamefile' and len(msglist) == 4:
        response = rename_torrent_file(msglist[1], msglist[2], msglist[3])

    # strip common unwanted bytes from file names
    # min length of unwanted bytes is MIN_UNWANTED_BYTES_LEN
    elif msglist[0] == '$strip' and len(msglist) == 3 and
         len(msglist[2]) >= MIN_UNWANTED_BYTES_LEN:
        response = strip_unwanted_names(msglist[1], msglist[2])

    # Send the response
    for i in range(0, len(response), 2000):
        shortrsp = response[i:i+2000]
        await message.channel.send(shortrsp)

bot.run(configs['TOKEN'])
