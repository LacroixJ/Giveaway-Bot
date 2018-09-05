#Python 3.6

import discord
import asyncio
import time
import mysql.connector
from giveaway import giveaway
import details

database = mysql.connector.connect(
    auth_plugin = "mysql_native_password",
    host = "localhost",
    user = "TC",
    passwd = details.password,
    database = "tcgiveaway"
)

cursor = database.cursor()
#                               If the giveaways table does not exist, create it.
try:
    cursor.execute("""CREATE TABLE giveaways (
    giveaway_id VARCHAR(255),
    header VARCHAR(255),
    description VARCHAR(255),
    image VARCHAR(255),
    number_of_winners VARCHAR(255),
    datestart VARCHAR(255),
    dateend VARCHAR(255),
    timestart VARCHAR(255),
    timeend VARCHAR(255),
    status VARCHAR(255))""")
    print("table created")
except Exception as e:
    print(e)

try:
    cursor.execute("""CREATE TABLE winners (
    giveaway_id VARCHAR(255),
    winner_id VARCHAR(255))""")
    print("created winners table")
except Exception as e:
    print(e)

try:
    cursor.execute("""CREATE TABLE losers (
    giveaway_id VARCHAR(255),
    loser_id VARCHAR(255))""")
    print("created losers table")
except Exception as e:
    print(e)

try:
    cursor.execute("""CREATE TABLE entrants (
    giveaway_id VARCHAR(255),
    entrant_id VARCHAR(255))""")
    print("created entrants table")
except Exception as e:
    print(e)


TOKEN = details.token
client = discord.Client()

print("Discord Version: " + discord.__version__)
#           function takes giveaway id and returns a corresponding giveaway object if it exists
def retrieve_giveaway(giveaway_number):
   # print(giveaway_number)
    sql = "SELECT * FROM giveaways WHERE giveaway_id=%s"
    sql_two = (str(giveaway_number), )
    try:
        cursor.execute(sql, sql_two)
        table  =  cursor.fetchall()
        details = table[0]
    except:
        return "NA" #returns not availible if the id does not exist, this will spagetify other code for now. sorry about that in advance.
    #print (type(details))
    #print (len(details))
    #for x in details:
    #    print("details :" + x)
    new_giveaway = giveaway()

    #load it in
    new_giveaway.set_id(details[0])
    new_giveaway.set_header(details[1])
    new_giveaway.set_description(details[2])
    new_giveaway.set_image(details[3])
    new_giveaway.set_number_of_winners(details[4])
    new_giveaway.timeframe.start = details[5]
    new_giveaway.timeframe.end = details[6]
    new_giveaway.timeframe.starttime = details[7]
    new_giveaway.timeframe.endtime = details[8]
    new_giveaway.set_status(details[9])


    sql = "SELECT winner_id FROM winners WHERE giveaway_id=$s"
    sql_2 = (str(giveaway_number), )
    try:
        cursor.execute(sql,sql_2)
        winners = (cursor.fetchall())
    except Exception as e:
  #      print(e)
        winners = []
    new_giveaway.set_winners(winners)

    sql = "SELECT loser_id FROM losers WHERE giveaway_id=$s"
    sql_2 = (str(giveaway_number), )
    try:
        cursor.execute(sql,sql_2)
        losers = (cursor.fetchall())
    except Exception as e:
 #       print(e)
        losers  = []
    new_giveaway.set_losers(losers)

    sql = "SELECT entrant_id FROM entrants WHERE giveaway_id=$s"
    sql_2 = (str(giveaway_number), )
    try:
        cursor.execute(sql,sql_2)
        entrants = (cursor.fetchall())
    except Exception as e:
#        print(e)
        entrants = []
    new_giveaway.set_entrants(entrants)

    return new_giveaway
#           This function checks if giveaway exists then stores/updates it in sql as required
def store_giveaway(giveaway):
    try:
        cursor.execute("SELECT giveaway_id FROM giveaways")
    except Exception as e:
        print(e)

    ids = cursor.fetchall()
    mode_update = 0
    for x in ids:
        if giveaway.get_id() == x[0]:
            mode_update = 1
            break

    if mode_update == 0:
        sql = """INSERT INTO giveaways (giveaway_id, header, description, image,
        number_of_winners, datestart, dateend, timestart, timeend, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (
                giveaway.get_id(),
                giveaway.get_header(),
                giveaway.get_description(),
                giveaway.get_image(),
                giveaway.get_number_of_winners(),
                giveaway.timeframe.start,
                giveaway.timeframe.end,
                giveaway.timeframe.starttime,
                giveaway.timeframe.endtime,
                giveaway.get_status())
        cursor.execute(sql, values)
        database.commit()
        return
    elif mode_update == 1:
        sql ="""UPDATE giveaways SET
        header=%s, description=%s, image=%s, number_of_winners=%s, datestart=%s,
        dateend=%s, timestart=%s, timeend=%s, status =%s
        WHERE giveaway_id=%s"""
        variables = (giveaway.get_header(), giveaway.get_description(), giveaway.get_image(),
                giveaway.get_number_of_winners(), giveaway.timeframe.start, giveaway.timeframe.end,
                giveaway.timeframe.starttime, giveaway.timeframe.endtime, giveaway.get_status(), giveaway.get_id())
        cursor.execute(sql, variables)
        database.commit()

    else:
        raise ValueError('Error storing giveaway to mysql')


    sql = "SELECT * FROM winners WHERE giveaway_id=%s"
    cursor.execute(sql,(giveaway.get_id(), ))
    winners = cursor.fetchall()

    sql = "SELECT * FROM losers WHERE giveaway_id=%s"
    cursor.execute(sql,(giveaway.get_id(), ))
    losers = cursor.fetchall()

    sql = "SELECT * FROM entrants WHERE giveaway_id=%s"
    cursor.execute(sql,(giveaway.get_id(), ))
    entrants = cursor.fetchall()

    for x in giveaway.get_winners():
        insertbool = 1
        for w in winners:
            if x == w[1]:
                insertbool = 0

        if insertbool == 1:
            sql = "INSERT INTO winners (giveaway_id, winner_id) VALUES (%s, %s)"
            values = (giveaway.get_id(), x)
            cursor.execute(sql, values)
            database.commit()

    for x in giveaway.get_losers():
        insertbool = 1
        for l in losers:
            if x == l[1]:
                insertbool = 0

        if insertbool == 1:
            sql = "INSERT INTO losers (giveaway_id, loser_id) VALUES (%s, %s)"
            values = (giveaway.get_id(), x)
            cursor.execute(sql, values)
            database.commit()

    for x in giveaway.get_entrants():
        insertbool = 1
        for e in entrants:
            if x == e[1]:
                insertbool = 0

        if insertbool == 1:
            sql = "INSERT INTO entrants (giveaway_id, winner_id) VALUES (%s, %s)"
            values = (giveaway.get_id(), x)
            cursor.execute(sql, values)
            database.commit()


    return
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

async def add_entrant(message):
    giveaway_id = (message.content.split(sep = " "))[1]
    giveaway = retrieve_giveaway(giveaway_id)
    entrant_id = "123456789" #temp string while I figure out implementation
    giveaway.entrants.append(entrant_id)
    store_giveaway(giveaway)
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
