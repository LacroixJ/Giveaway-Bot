#Python 3.6

import discord
import asyncio
import time
import mysql.connector
from giveaway import giveaway
import details
import read_write

database = mysql.connector.connect(
    auth_plugin = "mysql_native_password",
    host = "localhost",
    user = "TC",
    passwd = details.password,
    database = "tcgiveaway"
)

cursor = database.cursor()

read_write.create_giveaway_tables()
store_giveaway = read_write.store_giveaway
retrieve_giveaway = read_write.retrieve_giveaway

TOKEN = details.token
client = discord.Client()

print("Discord Version: " + discord.__version__)
#           function takes giveaway id and returns a corresponding giveaway object if it exists
#call this when the giveaway ends, or to redraw. sending message to winners will be in seperate function
async def draw_winners(message):
    text = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(text[1])
    if giveaway == "NA":
        client.send_message(message.channel, "Invalid ID")
        return
    giveaway.draw_winners(giveaway.get_number_of_winners())
    store_giveaway(giveaway)

    msg = "Winners have been picked randomly for giveaway '" + giveaway.get_id() + "'"
    await client.send_message(message.channel,msg)
    return
async def delete_giveaway(message):
    text = message.content.split(sep = " ")
    giveaway_id = text[1]


    for x in ["giveaways","winners","losers","entrants"]:
        sql = "DELETE FROM "+x+" WHERE giveaway_id ="+giveaway_id 
        cursor.execute(sql)
        database.commit()
    await client.send_message(message.channel, "deleted giveaway "+ giveaway_id)

async def switchME(message):
    x = message.content

    if x.startswith("!giveaway"):
        command = x.split(sep = " ")

        dictionary = {
                "redraw":draw_winners,
                "preview":preview_giveaway,
                "archive":archive_giveaway,
                "delete":delete_giveaway,
                "header":set_header,
                "description":set_description,
                "image":set_image,
                "winners":set_winners,
                "add":create_giveaway,
                "list":list_giveaways}

        if dictionary.get(command[1]) != None:
            await dictionary.get(command[1])(message)
        elif len(command) > 2:
            if dictionary.get(command[2]) != None:
                await dictionary.get(command[2])(message)
            else:
                await client.send_message(message.channel,"Invalid command! use !giveaway help for the list of commands")

        else:
            await client.send_message(message.channel,"Invalid command! use !giveaway help for the list of commands")

    return
#               provide a list of giveaways with images #TODO wait for that scrolly thing
async def list_giveaways(message):
    text = message.content.split(sep = " ")
    sql = "SELECT * FROM giveaways WHERE status=%s"
    if text[2] == "active":
        sql_2 = ("active", )
    elif text[2] == "archive":
        sql_2 = ("archive", )
    cursor.execute(sql, sql_2)
    data  =  cursor.fetchall()
    giveaway_count = 0
    giveaways = []
    for x in data:
        giveaways.append(retrieve_giveaway(x[0]))
        giveaway_count += 1
    database.commit()
    msg = "test"
    return #leaving it at this for now

async def preview_giveaway(message):
    giveaway_id = (message.content.split(sep = " "))[1]
    giveaway = retrieve_giveaway(giveaway_id)
    if giveaway == "NA":
        await client.send_message(message.channel, "Invalid ID!")
        return
    winning_users = []
    for x in giveaway.get_winners():
        winning_users.append(client.get_user_info(x).mention())

    line1_1 = str("**Giveaway #"+giveaway.get_id()+" |** start-"+giveaway.timeframe.start)
    line1_2 = str(" end-"+ giveaway.timeframe.end +" --"+giveaway.get_status()+"--"+" **| "+ giveaway.get_header()+"**\n")
    line1 = line1_1 + line1_2
    line2 = giveaway.get_description() + "\n"
    line3 = "**Winners("+giveaway.get_number_of_winners()+"):**"

    if len(winning_users) == 0:
        line3 = line3 + " Not Drawn \n"
    else:
        for i in winning_users:
            line3 = line3 + i + " "
        line3 = line3 + "**|** Congradulations! Winners will recieve a DM \n"

    em = discord.Embed()
    image=(giveaway.get_image())
    em.set_image(url=image)
    msg = line1 + line2 + line3


    await client.send_message(message.channel,content=msg,embed=em)
#create an empty giveaway and asign a new id
async def create_giveaway(message):
    new_giveaway = giveaway(message)
    msg = str('Giveaway ID: ' + new_giveaway.get_id())

    store_giveaway(new_giveaway)

    await client.send_message(message.channel,msg)
#updates header for from giveaway id
async def set_header(message):
    text = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(text[1])
    if giveaway == "NA": #means there was an error in the read function
        await client.send_message(message.channel,"Invalid giveaway id!")
        return
    giveaway.set_header(text[3])
    store_giveaway(giveaway)
    msg =  ("The new header for giveaway '" + giveaway.get_id() + "' is '" + giveaway.get_header()+ "'")
    await client.send_message(message.channel,msg)


async def set_description(message):
    text = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(text[1])
    if giveaway == "NA": #means there was an error in the read function
        await client.send_message(message.channel,"Invalid giveaway id!")
        return
    giveaway.set_description(text[3])
    store_giveaway(giveaway)
    msg =  ("The new description for giveaway '" + giveaway.get_id() + "' is '" + giveaway.get_description()+ "'")
    await client.send_message(message.channel,msg)

async def set_image(message):
    text = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(text[1])
    if giveaway == "NA": #means there was an error in the read function
        await client.send_message(message.channel,"Invalid giveaway id!")
        return
    giveaway.set_image(text[3])
    store_giveaway(giveaway)
    msg =  ("Image has been updated for giveaway '" + giveaway.get_id() + "' Use ```!giveaway [id] preview``` to preview the giveaway")
    await client.send_message(message.channel,msg)

async def set_winners(message):
    text = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(text[1])
    if giveaway == "NA": #means there was an error in the read function
        await client.send_message(message.channel,"Invalid giveaway id!")
        return
    giveaway.set_number_of_winners(text[3])
    store_giveaway(giveaway)
    msg =  ("There are now "+ giveaway.get_number_of_winners() +" Winners for giveway '" + giveaway.get_id()+"'" )
    await client.send_message(message.channel,msg)  

async def archive_giveaway(message):
    text = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(text[1])
    if giveaway == "NA": #means there was an error in the read function
        await client.send_message(message.channel,"Invalid giveaway id!")
        return
    giveaway.set_status("archived")
    store_giveaway(giveaway)
    msg = "giveaway " + giveaway.get_id() + " has been archived"
    await client.send_message(message.channel, msg)

async def add_entrant(user, message):
    giveaway_id = []
    content = message.content
    for x in range(30):
        if (content[x] == '#' and content[x+4] == '|'):
            giveaway_id = content[x+1] + content[x+2]
    giveaway = retrieve_giveaway(giveaway_id)
    entrant_id = user.id
    giveaway.entrants.append(entrant_id)
    store_giveaway(giveaway)
    return

@client.event
async def on_reaction_add(reaction,user):
    message = reaction.message
    await add_entrant(user,message)
    print("reaction detected")
    return
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await switchME(message)

async def Hello(message):

    msg = 'Hello {0.author.mention}'.format(message)
    await client.send_message(message.channel, msg)



@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


client.run(TOKEN)
