import mysql.connector
from giveaway import giveaway
import details
import discord
import asyncio

database = mysql.connector.connect(
    auth_plugin = "mysql_native_password",
    host = "localhost",
    user = "TC",
    passwd = details.password,
    database = "tcgiveaway"
)

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
            sql = "INSERT INTO entrants (giveaway_id, entrant_id) VALUES (%s, %s)"
            values = (giveaway.get_id(), x)
            cursor.execute(sql, values)
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

