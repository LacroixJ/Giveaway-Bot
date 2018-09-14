#Python 3.6

import discord
import asyncio
import time
import mysql.connector
from threading import Timer
from giveaway import giveaway
import details
import read_write
import datetime


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



def timer_done():
    completed_giveaway = retrieve_giveaway(read_write.check_recent())
    if completed_giveaway == "NA":
        print("TIMER ERROR")
        return
    print("giveaway "+ completed_giveaway.get_id() +" is complete")
    giveaway_done(completed_giveaway)
    return 

#expiration array should be [<year>, <month>, <day>, <hour=?>,<minute=?>,<second=0>]
def start_timer(expiration_array):
    expiry_date = datetime.datetime(int(expiration_array[0]),int(expiration_array[1]), int(expiration_array[2]), int(expiration_array[3]), int(expiration_array[4]),int(expiration_array[5]))
    present_date = datetime.datetime.utcnow()

    difference = expiry_date - present_date 
    expiration_in_seconds = difference.total_seconds()

    print(expiry_date)
    print(present_date)
    print(difference)
    print(str(int(expiration_in_seconds))+ " in seconds")

    if expiration_in_seconds < 0:
        print("invalid date!(for testing)")
        return "string to fail test"
    if expiration_in_seconds > 1000000000:
        return "failed string"
    else:
        print("creating timer to expire in: "+ str(int(expiration_in_seconds)) + " seconds")

    return Timer(int(expiration_in_seconds), timer_done)

def giveaway_done(giveaway):
    giveaway.set_status("archived")
    giveaway.draw_winners(giveaway.get_number_of_winners())
    giveaway.replace_winners = 1
    store_giveaway(giveaway)
    print("giveaway" + giveaway.get_id() + " complete")
    return

def date_parser(date, time): # yyyy/mm/dd hh:mm
    date_array = date.split(sep="/")
    year = date_array[0]
    month = date_array[1]
    day = date_array[2]

    time_array = time.split(sep=":")
    hour = time_array[0]
    minute = time_array[1]

    return [year,month,day,hour,minute,0]
timerlist = [] 
def load_timers():
    sql = "SELECT * FROM giveaways"
    cursor.execute(sql)
    giveaway_list = cursor.fetchall()
    database.commit()
    for x in giveaway_list:
        date = date_parser(x[6],x[8])
        timerlist.append(start_timer(date))
    for x in timerlist:
        if type(x) != str:
            x.start()
    return



print("Discord Version: " + discord.__version__)
#           function takes giveaway id and returns a corresponding giveaway object if it exists
#call this to redraw. If called mnually, fails if givaway not over.
async def redraw_winners(message):
    text = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(text[1])
    if giveaway == "NA":
        client.send_message(message.channel, "Invalid ID")
        return
    if giveaway.get_status() != "archived":
        await client.send_message(message.channel, "This giveaway is not complete! Unable to redraw!")
        return
    giveaway.draw_winners(giveaway.get_number_of_winners())
    giveaway.replace_winners = 1
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
                "redraw":redraw_winners,
                "preview":preview_giveaway,
                "archive":archive_giveaway,
                "delete":delete_giveaway,
                "header":set_header,
                "description":set_description,
                "image":set_image,
                "winners":set_winners,
                "add":create_giveaway,
                "list":list_giveaways,
                "date":set_date}

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
    sql_2 = "active"
    if text[2] == "active":
        sql_2 = ("active", )
    elif text[2] == "archived":
        sql_2 = ("archived", )
    cursor.execute(sql, sql_2)
    data  =  cursor.fetchall()
    giveaway_count = 0
    giveaways = []
    for x in data:
        giveaways.append(retrieve_giveaway(x[0]))
        giveaway_count += 1
    for x in giveaways:
        await preview_giveaway(message, x.get_id())
    database.commit()
    return #leaving it at this for now

async def preview_giveaway(message, listmode=0):
    if listmode != 0:
        giveaway_id = listmode 
    else:
        giveaway_id = (message.content.split(sep = " "))[1]
    giveaway = retrieve_giveaway(giveaway_id)
    if giveaway == "NA":
        await client.send_message(message.channel, "Invalid ID!")
        return
    winning_users = []
    for x in giveaway.get_winners():
        winning_users.append(x)

    line1_1 = str("**Giveaway #"+giveaway.get_id()+" |** start-"+giveaway.timeframe.start)
    line1_2 = str(" end-"+ giveaway.timeframe.end +" --"+giveaway.get_status()+"--"+" **| "+ giveaway.get_header()+"**\n")
    line1 = line1_1 + line1_2
    line2 = giveaway.get_description() + "\n"
    line3 = "**Winners("+giveaway.get_number_of_winners()+"):**"
    line4 = "Number of entrants: **" + str(len(giveaway.entrants))+"** \n"
    if len(winning_users) == 0:
        line3 = line3 + " Not Drawn \n"
    else:
        for i in winning_users:
            user = await client.get_user_info(i[0])
            userstring = user.mention
            line3 = line3 + userstring + " "
        line3 = line3 + "**|** Congratulations! Winners will recieve a DM \n"

    em = discord.Embed()
    image=(giveaway.get_image())
    em.set_image(url=image)
    msg = line1 + line2 + line4 + line3


    await client.send_message(message.channel,content=msg,embed=em)
    return


async def enter_pm(user, giveaway):
    line1 = "You have been entered for giveaway "+ giveaway.get_id() +"\n"
    line2 = "Description: " + giveaway.get_description() + "\n"
    line3 = "End date: " + giveaway.timeframe.end +"\n"
    line4 = "If you win, you will be notified by the bot and a TC staff member. Good luck! \n"
    
    em = discord.Embed()
    em.set_image(url=giveaway.get_image())
    msg = line1 + line2 + line3 + line4
    try:
        await client.send_message(await client.get_user_info(user),content=msg,embed=em)
    except:
        print("User "+ user +" Has messages from other server members disabled!") 
    return
    

#create an empty giveaway and asign a new id
async def create_giveaway(message):
    new_giveaway = giveaway(message)
    msg = str('Giveaway ID: ' + new_giveaway.get_id())
    current_date = datetime.datetime.utcnow()
    formatstring = str(current_date.year) +"/"+str(current_date.month)+"/"+str(current_date.day)
    formatstring1 = str(current_date.hour)+":"+str(current_date.minute)
    print(formatstring)
    print(formatstring1)
    new_giveaway.timeframe.start = formatstring
    new_giveaway.timeframe.starttime = formatstring1
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
    msg =  ("There are now "+ giveaway.get_number_of_winners() +" winners for giveway '" + giveaway.get_id()+"'" )
    await client.send_message(message.channel,msg) 

async def set_date(message):
    content = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(content[1])
    if giveaway == "NA":
        await client.send_message(message.channel, "Invalid ID!")
        return
    #should be yyyy/mm/dd hh:mm
    try:
        giveaway.timeframe.end = str(content[3])
        giveaway.timeframe.endtime = str(content[4])
    except:
        await client.send_message(message.channel, "Invalid formatting! Should be yyyy/mm/dd hh:mm")
        return
    date = giveaway.timeframe.end.split(sep = "/")
    
    year = date[0]
    month = date[1]
    day = date[2]
    
    time = giveaway.timeframe.endtime.split(sep = ":")

    hour = time[0]
    minute = time[1]
    
    #print(year +" " + month + " " + day + " " + hour + " " +minute)
    timer = start_timer([int(year),int(month),int(day),int(hour),int(minute),0])
    if(type(timer) == str):
        print("ivalid nidnwi")
        print(timer)
        return
    timer.start()

    store_giveaway(giveaway)
    await client.send_message(message.channel, "Giveaway **#"+giveaway.get_id()+"** will end on "+ giveaway.timeframe.end+ " at "+ giveaway.timeframe.endtime)
    return
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
    giveaway_id = "-1"
    content = message.content
    for x in range(11, 15):#area where we identify the giveaway id.
        print (content[x])
        if ((content[x] == '#' and content[x+4] == '|') or (content[x] == '#' and content[x+3] == '|')):
            giveaway_id = content[x+1] + content[x+2]
    print("retrived it: "+giveaway_id)
    giveaway = retrieve_giveaway(giveaway_id)
    if giveaway == "NA":
        return
    entrant_id = user.id
    giveaway.add_entrant(entrant_id)
    print(giveaway_id)
    print(giveaway.entrants)
    await enter_pm(entrant_id, giveaway)
    store_giveaway(giveaway)
    return




    return
@client.event
async def on_reaction_add(reaction,user):
    message = reaction.message
    if message.author != client.user:
        return
    await add_entrant(user,message)
    print("reaction detected")
    return

#@client.event
#async def on_raw_reaction_add(payload):
#    message = await client.get_message(payload.message_id)
#    user = client.get_user_info(payload.user_id)
#    await add_entrant(user,message)
#    print("reaction detected")
#    return

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
    load_timers()


client.run(TOKEN)
