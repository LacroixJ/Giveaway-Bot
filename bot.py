#Python 3.6

import discord
import asyncio
import time
import mysql.connector
import threading
from giveaway import giveaway
import details
import read_write
import datetime
import secrets

EM_COLOUR = 15251015 
EM_FOOTER = "To enter, react to the giveaway posting. Powered by Trade Central"  
database = mysql.connector.connect(
    auth_plugin = "mysql_native_password",
    host = "localhost",
    user = "TC",
    passwd = details.password,
    database = "tcgiveaway"
)

cursor = database.cursor()
Timer = threading.Timer
read_write.create_giveaway_tables()
store_giveaway = read_write.store_giveaway
retrieve_giveaway = read_write.retrieve_giveaway

TOKEN = details.token
client = discord.Client()

async def update_messages(giveaway_id):
    sql = "SELECT * FROM message_cache where giveaway_id=%s"
    cursor.execute(sql,(giveaway_id, ))
    messages = cursor.fetchall()
    message_list = []
    for i in range(len(messages)):
        message_list.append(messages[i])
    for x in message_list:
        message_id = x[1]
        try:
            message = await client.get_message(client.get_channel(x[2]),x[1])
        except:
            donothing = 1
        giveaway = retrieve_giveaway(giveaway_id)
        if giveaway == "NA":
            return
        winning_users = []
        for x in giveaway.get_winners():
            winning_users.append(x)
        if giveaway.get_status() == "active":
            liveswitch = "\** LIVE \**"
        else:
            liveswitch = "\** COMPLETE \**"
        line1_1 = str("**Giveaway #"+giveaway.get_id()+" |** start-"+giveaway.timeframe.start)
        line1_2 = str(" end-"+ giveaway.timeframe.end +" --"+giveaway.get_status()+"--"+" **| "+ giveaway.get_header()+"**              "+liveswitch+"\n")
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

        em = discord.Embed(colour = EM_COLOUR)
        image=(giveaway.get_image())
        em.set_image(url=image)
        em.set_footer(text=EM_FOOTER)
        msg = line1 + line2 + line4 + line3
        await client.edit_message(message,new_content=msg)
        sql = "DELETE FROM message_cache WHERE message_id=%s"
        cursor.execute(sql,(message_id, ))
        database.commit()
    return




def timer_done():
    completed_giveaway = retrieve_giveaway(read_write.check_recent())
    if completed_giveaway == "NA":
        print("No giveaway done")
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

    if expiration_in_seconds < 0:
        return "string to fail test"
    elif expiration_in_seconds > 1000000000:
        return "failed string"
    else:
        print("creating timer to expire in: "+ str(int(expiration_in_seconds)) + " seconds")

    return Timer(int(expiration_in_seconds), timer_done)

def giveaway_done(giveaway):
    giveaway.set_status("archived")
    giveaway.draw_winners(giveaway.get_number_of_winners())
    giveaway.replace_winners = 1
    store_giveaway(giveaway)
    reloaded = retrieve_giveaway(giveaway.get_id())
    winners = ()
    for x in reloaded.get_winners():
        winners = winners + (x[0],)
    donelist.append(reloaded)
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



#function takes giveaway id and returns a corresponding giveaway object if it exists
#call this to redraw. Fails if giveaway not over.
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
        if len(command) == 1:
            await help_message(message)
            return
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
                "date":set_date,
                "datenow":print_current_time,
                "help":help_message}
 
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
async def help_message(message):
    msg ="""All giveaway commands start with !giveaway\n
**1. Create a giveaway**
```!giveaway add```- Creates a new giveaway, id will be given\n
**2. Set End Date for a Giveaway (UTC 24h Format)**
```!giveaway [giveaway_id] date [yyyy/mm/dd hh:mm]```- Sets the end date for the giveaway. Time MUST be in UTC and 24 hour clock\n
**3. Get Present Date and Time**
```!giveaway datenow```- Produces the current date in UTC\n
**4. Set Giveaway Header**
```!giveaway [giveaway_id] header <header>```- Set the header to desired statement\n
**5. Set Giveaway Description**
```!giveaway [giveaway_id] description```- Set the description to the desired statement\n
**6. Set Giveaway Image**
```!giveaway [giveaway_id] image [url]```- Set the giveaway embed image, takes http and https links. No gifs\n
**7. Set the number of winners**
```!giveaway [giveaway_id] winners [number of winners]```- Set how many people can win the giveaway\n
**8. Redraw the Giveaway**
```!giveaway [giveaway_id] redraw```- Redraws winners for the Giveaway, does not work until giveaway is complete or archived\n
**9. Archive Giveaway**
```!giveaway [giveaway_id] archive```- Marks the giveaway as complete\n
**10. Delete Giveaway from Database**
```!giveaway [giveaway_id] delete```- Deletes the giveaway permanently\n
**11. Display or Preview a Giveaway**
```!giveaway [giveaway_id] preview```- Preview the giveaway, can enter the giveaway by reacting to this message.\n
**12. List all Giveaways**
```!giveaway list [active/archived]```- Lists all completed or active giveaways depending on selection\n
**13. Help**
```!giveaway help```- This message\n
            """
    em = discord.Embed(colour=EM_COLOUR, description = msg)
    em.set_footer(text=EM_FOOTER)
    
    await client.send_message(message.channel,embed=em)
    return
async def list_giveaways(message):
    text = message.content.split(sep = " ")
    sql = "SELECT * FROM giveaways WHERE status=%s"
    sql_2 = "active"
    if len(text) == 2:
        await client.send_message(message.channel, "Usage: !giveaway list [active/archived]")
        return
    if text[2] == "active":
        sql_2 = ("active", )
    elif text[2] == "archived":
        sql_2 = ("archived", )
    else:
        await client.send_message(message.channel, "Usage: !giveaway list [active/archived]")
        return
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
    return 

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

    if giveaway.get_status() == "active":
        liveswitch = "\** LIVE \**"
    else:
        liveswitch = "\** COMPLETE \**"
    line1_1 = str("**Giveaway #"+giveaway.get_id()+" |** start-"+giveaway.timeframe.start)
    line1_2 = str(" end-"+ giveaway.timeframe.end +" --"+giveaway.get_status()+"--"+" **| "+ giveaway.get_header()+"**              "+liveswitch+"\n")
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

    em = discord.Embed(colour = EM_COLOUR)
    image=(giveaway.get_image())
    em.set_image(url=image)
    em.set_footer(text=EM_FOOTER)
    msg = line1 + line2 + line4 + line3


    message_to_cache = await client.send_message(message.channel,content=msg,embed=em)
    sql = "INSERT INTO message_cache VALUES (%s,%s, %s)"
    values = (giveaway_id, message_to_cache.id, message_to_cache.channel.id)
    cursor.execute(sql,values)
    database.commit()
    return
async def print_current_time(message):
    msg = datetime.datetime.utcnow()
    await client.send_message(message.channel,str(msg))
    return
async def enter_pm(user_id, giveaway):
    line1 = "You have been entered for giveaway "+ giveaway.get_id() +"\n"
    line2 = "Description: " + giveaway.get_description() + "\n"
    line3 = "End date: " + giveaway.timeframe.end +"\n"
    line4 = "If you win, you will be notified by the bot and a TC staff member. Good luck! \n"
    
    em = discord.Embed(colour = EM_COLOUR)
    em.set_image(url=giveaway.get_image())
    em.set_footer(text=EM_FOOTER)
    msg = line1 + line2 + line3 + line4
    user = await client.get_user_info(user_id)
    try:
        await client.send_message(user,content=msg,embed=em)
    except:
        print("User "+ user.name +" Has messages from other server members disabled!") 
    return
async def loser_pm(giveaway):
    losers_tuple = giveaway.get_entrants()
    losers_list = []
    for x in losers_tuple:
        losers_list.append(x)
    winners = giveaway.get_winners()
    winners_list = []
    for x in winners:
        winners_list.append(x)
    for x in losers_list:
        if x in winners_list:
            losers_list.remove(x)
    for user_id in losers_list:
        read_write.add_entry(user_id[0])
        user = await client.get_user_info(user_id[0])
        line1 = "Better Luck Next Time.\n"
        line2 = "Yikes "+user.mention+" You didin't win giveaway "+giveaway.get_id()+"\n"
        line3 = "Since you are a winner in our book, we are awarding you an extra entry in future giveaways until you win one. Good Luck!\n"
        em = discord.Embed(colour=EM_COLOUR)    
        em.set_image(url=giveaway.get_image())
        em.set_footer(text=EM_FOOTER)
        msg = line1+line2+line3
        await client.send_message(user,content=msg,embed=em)
    return
async def winner_pm(giveaway):
    users_tuple = giveaway.get_winners()
    winners = []
    for x in users_tuple:
        winners.append(x)
    for user_id in winners:
        read_write.add_entry(user_id[0])
        read_write.set_multiplier_to_one(user_id[0])
        try:
            user = await client.get_user_info(user_id[0])
        except:
            print(user_id +"is unable to receive msges fron this bot")
            user = client.user
        line1 = "Winner winner Chicken Dinner!\n"
        line2 = "Congratulations "+user.mention+" You have won giveaway "+giveaway.get_id()+"\n"
        line3 = "A Community Manager will contact you shortly.\n"
        date = date_parser(giveaway.timeframe.end, giveaway.timeframe.endtime)
        date[2] = str(int(date[2]) + 7)
        line4 = "You will have until "+ date[0]+"/"+date[1]+"/"+date[2]  +" to collect your prize.\n"
        em = discord.Embed(colour=EM_COLOUR)    
        em.set_image(url=giveaway.get_image())
        em.set_footer(text=EM_FOOTER)
        msg = line1+line2+line3+line4
        await client.send_message(user,content=msg,embed=em)
    return
#create an empty giveaway and asign a new id
async def create_giveaway(message):
    new_giveaway = giveaway(message)
    msg = str('Giveaway ID: ' + new_giveaway.get_id())
    current_date = datetime.datetime.utcnow()
    formatstring = str(current_date.year) +"/"+str(current_date.month)+"/"+str(current_date.day)
    formatstring1 = str(current_date.hour)+":"+str(current_date.minute)
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
    header = ""
    for x in range(3,len(text)):
        header = header + text[x] + " "
    giveaway.set_header(header)
    store_giveaway(giveaway)
    msg =  ("The new header for giveaway '" + giveaway.get_id() + "' is '" + giveaway.get_header()+ "'")
    await client.send_message(message.channel,msg)


async def set_description(message):
    text = message.content.split(sep = " ")
    giveaway = retrieve_giveaway(text[1])
    if giveaway == "NA": #means there was an error in the read function
        await client.send_message(message.channel,"Invalid giveaway id!")
        return
    description = ""
    for x in range(3,len(text)):
        description = description + text[x] + " "
    giveaway.set_description(description)
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
    if giveaway == "NA" or len(text) < 4: #means there was an error in the read function
        await client.send_message(message.channel,"Invalid giveaway id, or not enough parameters passed!!")
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
        await client.send_message(message.channel, "Invalid time!")
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
        if ((content[x] == '#' and content[x+4] == '|') or (content[x] == '#' and content[x+3] == '|')):
            giveaway_id = content[x+1] + content[x+2]
    giveaway = retrieve_giveaway(giveaway_id)
    if giveaway == "NA":
        return
    entrant_id = user.id
    already_entered = 0
    for x in giveaway.get_entrants():
        if entrant_id == x[0]:
            already_entered = 1

    if already_entered == 0:
        giveaway.add_entrant(entrant_id)
        await enter_pm(entrant_id, giveaway)

    store_giveaway(giveaway)
    return

donelist = []
active = 0

@client.event                 # This is how I got around not being able to mix threads with coroutines
async def on_member_update(var1,var2): #checks a global variable for complete giveaways and then sends various pms
    global active                       #activates whenenver a profile updates somehow.
    global donelist
    time.sleep(secrets.randbelow(1000)/100)#magic
    if active == 0:
        active = 1
        if len(donelist) == 0:
            active = 0
            return
        popvalues =[]
        await update_messages(donelist[0].get_id())
        for i in range(len(donelist)):
            for j in range(len(donelist)):
                if donelist[i] == donelist[j] and i!=j:
                    popvalues.append(i)
        for x in popvalues:
            donelist.pop(x)
        for i in range(len(donelist)):
            await winner_pm(donelist[0])
            time.sleep(1)
            await loser_pm(donelist[0])
            donelist.pop(0)
            time.sleep(1)
    active = 0
    return

@client.event
async def on_reaction_add(reaction,user):
    message = reaction.message
    if message.author != client.user:
        return
    await add_entrant(user,message)
    return


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    await switchME(message)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print("Discord Version: " + discord.__version__)
    print('------')
    load_timers()


client.run(TOKEN)
