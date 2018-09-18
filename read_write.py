import mysql.connector
import details
import discord
import asyncio
import datetime
import time
import giveaway

database = mysql.connector.connect(
    auth_plugin = "mysql_native_password",
    host = "localhost",
    user = "TC",
    passwd = details.password,
    database = "tcgiveaway"
)

def entry_number(user_id):
    sql = "SELECT * FROM entry_multiplier WHERE entrant_id=%s"
    cursor.execute(sql,(str(user_id), ))
    multy = cursor.fetchall()
    if type(multy) != tuple:
        database.commit()
        return 1
    multiple = multy[0][1]
    database.commit()
    if multiple == 0:
        multiple = 1
    return int(multiple)

def add_entry(user_id):
    sql = "SELECT * FROM entry_multiplier WHERE entrant_id=%s"
    cursor.execute(sql,(str(user_id), ))
    entrant = cursor.fetchall()
    if len(entrant) < 1:
        sql = "INSERT INTO entry_multiplier VALUES(%s,%s)"
        values = (str(user_id),str(1))
        cursor.execute(sql,values)
        database.commit()
        return
    number_of_entries  =  int(entrant[0][1]) + 1
    sql = "UPDATE entry_multiplier SET number_of_entries=%s WHERE entrant_id=%s"
    cursor.execute(sql,(str(number_of_entries),str(user_id)))
    database.commit()
    return

def set_multiplier_to_one(user_id):
    sql = "UPDATE entry_multiplier SET number_of_entries=1 WHERE entrant_id=%s"
    cursor.execute(sql,(str(user_id), ))
    database.commit()

    return
def check_recent():
    sql = "SELECT * FROM giveaways"
    cursor.execute(sql)
    giveaway_list = cursor.fetchall()
    database.commit()
    giveaway_id = "-1"
    biggest_date = datetime.datetime(2000,1,1)
    for x in giveaway_list:
        if len(x[6].split(sep = "/")) >=3 and len(x[8].split(sep = ":")) >= 2:
            year = x[6].split(sep = "/")[0]
            month = x[6].split(sep ="/")[1]
            day = x[6].split(sep = "/")[2]
            hour = x[8].split(sep = ":")[0]
            minute = x[8].split(sep = ":")[1]
            date = datetime.datetime(int(year),int(month),int(day),int(hour),int(minute),0)
    #        print (str(date)+" giveaway_id: " + x[0])
            if (biggest_date - date).total_seconds() < 0 and (date-datetime.datetime.utcnow()).total_seconds() <= 10:
                biggest_date = date
                giveaway_id = x[0]
    if (abs(biggest_date - datetime.datetime.utcnow())).total_seconds() > 180:
        print("checked recent but no finished giveaways")
    return giveaway_id



cursor = database.cursor()
def create_giveaway_tables():
    #If the giveaways table does not exist, create it.
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
    
    try:
        cursor.execute("""CREATE TABLE entry_multiplier (
        entrant_id VARCHAR(255),
        number_of_entries VARCHAR(225))""")
        print("created entries table")
    except Exception as e:
        print(e)

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
    insertbool = 0

    if giveaway.replace_winners == 1:
        sql = "DELETE FROM winners WHERE giveaway_id=%s"
        cursor.execute(sql,(giveaway.get_id(), ))
        giveaway.replace_winners = 0

    for x in giveaway.get_winners():
            
        insertbool = 1
        if type(x) != str:
            x = x[0]
            #print (x+ " Is a winner")
        #print (x+ " Is a winner")
        sql = "SELECT winner_id FROM winners WHERE giveaway_id=%s"
        cursor.execute(sql,(giveaway.get_id(), ))        
        winners = cursor.fetchall()
        database.commit()
        if len(winners) != 0:
            for w in winners:
                if w[0] == x:
                    insertbool = 0 
                    break
                if not insertbool:
                    break
        if insertbool:
            sql = "INSERT INTO winners (giveaway_id, winner_id) VALUES (%s, %s)"
            values = (giveaway.get_id(), x)
            cursor.execute(sql, values)
            database.commit()
            print("inserted into winners " + x) 
    insertbool = 0
    for x in giveaway.get_losers():
        insertbool = 1
        if type(x) != str:
            x = x[0]
           # print (x)
        sql = "SELECT loser_id FROM losers WHERE giveaway_id=%s"
        cursor.execute(sql,(giveaway.get_id(), ))
        losers = cursor.fetchall()
        if len(losers) != 0:
            for l in losers:
                if l[0] == x:
                    insertbool = 0 
                    break
                if not insertbool:
                    break
    if insertbool:
        sql = "INSERT INTO losers (giveaway_id, loser_id) VALUES (%s, %s)"
        values = (giveaway.get_id(), x)
        cursor.execute(sql, values)
        database.commit()

    insertbool = 0
    for x in giveaway.get_entrants():
        insertbool = 1
        #print(x)
        if type(x) != str:
            x = x[0]
        sql = "SELECT entrant_id FROM entrants WHERE giveaway_id=%s"
        cursor.execute(sql,(giveaway.get_id(), ))
        entrants = cursor.fetchall()
        if len(entrants) != 0:
            for e in entrants:
                if e[0] == x:
                    insertbool = 0 
                    break
                if not insertbool:
                    break
    if insertbool:
        sql = "INSERT INTO entrants (giveaway_id, entrant_id) VALUES (%s, %s)"
        values = (giveaway.get_id(), x)
        cursor.execute(sql, values)
        print("inserted "+x+" into entrants for giveaway "+ giveaway.get_id())
        database.commit()


    return
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
    new_giveaway = giveaway.giveaway()

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


    sql = "SELECT winner_id FROM winners WHERE giveaway_id=%s"
    sql_2 = (str(giveaway_number), )
    try:
        cursor.execute(sql,sql_2)
        winners = (cursor.fetchall())
    except Exception as e:
  #      print(e)
        winners = []
    new_giveaway.set_winners(winners)

    sql = "SELECT loser_id FROM losers WHERE giveaway_id=%s"
    sql_2 = (str(giveaway_number), )
    try:
        cursor.execute(sql,sql_2)
        losers = (cursor.fetchall())
    except Exception as e:
 #       print(e)
        losers  = []
    new_giveaway.set_losers(losers)

    sql = "SELECT entrant_id FROM entrants WHERE giveaway_id=%s"
    sql_2 = (str(giveaway_number), )
    try:
        cursor.execute(sql,sql_2)
        entrants = (cursor.fetchall())
    except Exception as e:
#        print(e)
        entrants = []
    new_giveaway.set_entrants(entrants)

    return new_giveaway

