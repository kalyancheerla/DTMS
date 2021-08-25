#!/usr/bin/env python3
import discord
import json
import qbittorrentapi
from datetime import datetime
#import pprint
import shlex

OTHER_CATEGORY = 'other'

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
    #pp.pprint(val)
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

    msg = message.content

    if msg.startswith('$hello'):
        await message.channel.send("Hey!\nI'm a BOT & I'm very "
                                   "happy to serve you.")

    if msg.startswith('$list'):
        response = get_torrents_list()
        await message.channel.send(response)

    if msg.startswith('$info '):
        response = get_torrent_info(msg.split()[1])
        await message.channel.send(response)

    # ['URL'] or ['URL1', 'URL2', ...]
    if msg.startswith('$add '):
        response = add_torrent_link(msg.split()[1:])
        await message.channel.send(response)

    # ['all'] or ['hash'] or ['hashe1', 'hash2', ...]
    if msg.startswith('$del '):
        response = delete_torrent(msg.split()[1:])
        await message.channel.send(response)

#    if msg.startswith('$pauseall'):
#        response = pause_torrent('all')
#        await message.channel.send(response)
#
#    if msg.startswith('$resumeall'):
#        response = resume_torrent('all')
#        await message.channel.send(response)

    # ['all'] or ['hash'] or ['hashe1', 'hash2', ...]
    if msg.startswith('$pause '):
        response = pause_torrent(msg.split()[1:])
        await message.channel.send(response)

    # ['all'] or ['hash'] or ['hashe1', 'hash2', ...]
    if msg.startswith('$resume '):
        response = resume_torrent(msg.split()[1:])
        await message.channel.send(response)

    # ['$rename', 'hash', 'newname part1', 'part2', ...]
    if msg.startswith('$rename '):
        msgsplit = msg.split()
        if len(msgsplit) >= 3:
            response = rename_torrent(msgsplit[1], ' '.join(msgsplit[2:]))
            await message.channel.send(response)

    # ['$changecategory', 'category', 'hash1', 'hash2', ...]
    if msg.startswith('$changecategory '):
        msgsplit = msg.split()
        if len(msgsplit) >= 3:
            response = change_category(msgsplit[1], msgsplit[2:])
            await message.channel.send(response)

    if msg.startswith('$fileinfo '):
        response = get_torrent_file_info(msg.split()[1])
        for i in range(0, len(response), 2000):
            shortrsp = response[i:i+2000]
            await message.channel.send(shortrsp)

    if msg.startswith('$renamefile '):
        msgsplit = shlex.split(msg)
        if len(msgsplit) == 4:
            response = rename_torrent_file(msgsplit[1], msgsplit[2],
                                           msgsplit[3])
            await message.channel.send(response)

    if msg.startswith('$strip '):
        msgsplit = shlex.split(msg)
        if len(msgsplit) == 3:
            response = strip_unwanted_names(msgsplit[1], msgsplit[2])
            await message.channel.send(response)

bot.run(configs['TOKEN'])
