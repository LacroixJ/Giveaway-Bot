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
import sys
#TODO: giveaway delete fully deletes
#TODO: countdown timer, fix time setting exception
PERMS = 1
EM_COLOUR = 15251015 
EM_FOOTER = "Powered by Trade Central :tc:"  
database = mysql.connector.connect(
    auth_plugin = "mysql_native_password",
    host = "localhost",
    user = "TC",
    passwd = details.password,
    database = "tcgiveaway"
)
whitelist_roles = ["Server Owner","Community Manager","Admin","Developer"]
whitelist_users = ["133491626680123392","140204931528392705","118531063285940227"]
cursor = database.cursor()
Timer = threading.Timer
read_write.create_giveaway_tables()
store_giveaway = read_write.store_giveaway
retrieve_giveaway = read_write.retrieve_giveaway

TOKEN = details.token
client = discord.Client()

async def update_giveaways():
    sql = "SELECT * FROM message_cache "
    cursor.execute(sql)
    messages = cursor.fetchall()
    message_list = []
    for i in range(len(messages)):
        message_list.append(messages[i])
    for x in message_list:
        giveaway_id = x[0]
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
        try:
            await client.edit_message(message,new_content=msg)
        except:
            donothing = 1
            #yeah sorry this hurts me too
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
donelist = []
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
 
    if PERMS:
        server = message.server
        if server==None:
            await client.send_message(message.channel,"Not accesible via PM")
            return
        server_roles  = server.roles
        global whitelist_roles
        global whitelist_users
        author_roles = message.author.roles
       #for i in range(len(server_roles)):
       #     print(str(i)+" "+ str(server_roles[i]))
        lethimthrough = 0
        for i in whitelist_roles:
            for x in author_roles:
                if str(x) == str(i) or str(message.author.id) in whitelist_users:
                    lethimthrough=1
            if lethimthrough:
                break
        if not(lethimthrough):
            return

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
                "poweroff":shut_down,
                "dev":dev_message,
                "help":help_message
                }
 
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

async def shut_down(message):
    print("shutdown called")
    print("logging out....")
    time.sleep(2)
    try:
        await client.logout()
        sys.exit(0)
    except:
        print("killed timers")

async def dev_message(message):
    user = await client.get_user_info(140204931528392705) 
    await client.send_message(message.channel, user.mention  + "Giveaway bot ping")
    return

async def help_message(message):
    msg ="""
**1. Create Giveaway**
`!giveaway add`\n-bot returns giveaway id
**2. Archive/Delete Giveaway**
`!giveaway [giveaway_id] [archive/delete]`\n-Marks the giveaway as complete
**3. Timeframe**
`!giveaway [giveaway_id] date [yyyy/mm/dd hh:mm]`\n-Timezone is UTC
**4. Header**
`!giveaway [giveaway_id] header <header>`
**5. Description**
`!giveaway [giveaway_id] description <description>`
**6. Image**
`!giveaway [giveaway_id] image [url]`\n- The image will appear after the description
**7. Number of Winners**
`!giveaway [giveaway_id] winners [number of winners]`
**8. Preview Giveaway**
`!giveaway [giveaway_id] preview`
**9. Redraw Winners**
`!giveaway [giveaway_id] redraw`\n-Does not work until giveaway is complete or archived
**10. List Giveaways**
`!giveaway list [active/archived]`\n-Lists preview of all active or archived giveaways
**11.  Get Date and Time in UTC**
`!giveaway datenow`
**12. Shutdown. **
`!giveaway poweroff`\n- forcefully shutdown the bot
**13. Help**
`!giveaway help` or `!giveaway`
            """
    em = discord.Embed(colour=EM_COLOUR, description = msg)
    em.set_footer(text="!giveaway dev to ping dev for help")
    
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

async def looping(): 
    global donelist
    if(len(donelist) > 0):
        x = donelist[0]
        await winner_pm(x)
        await loser_pm(x)
        donelist.pop()
    await update_giveaways()
    await asyncio.sleep(15)
    await looping()
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
    await looping()


client.run(TOKEN)
