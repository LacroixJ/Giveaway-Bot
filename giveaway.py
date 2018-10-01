import discord
import hashlib
import mysql.connector
import secrets
import asyncio
import read_write
import config as details
database = mysql.connector.connect(
    auth_plugin="mysql_native_password",
    host=details.hostname,
    user=details.username,
    passwd=details.password,
    database=details.database)
cursor = database.cursor()


#ordered id gen
def id_generator(message):
    sql = "SELECT *  FROM giveaways"
    cursor.execute(sql)
    data = cursor.fetchall()
    value_not_found = 1
    value = 0
    taken = 0
    while (value_not_found):
        for x in data:
            if x[0] == str(value):
                taken = 1
        if taken == 1:
            value += 1
            taken = 0
        else:
            database.commit()
            return str(value)


# random id gen
#def id_generator(message):
#    encrypt = str(message.timestamp)
#    sha256 =int( hashlib.sha256(encrypt.encode()).hexdigest(),16) % 10**8
#    return str(sha256)


#Timeframe as helper object
class Timeframe:
    def __init__(self, start, end, starttime, endtime):
        self.start = start
        self.end = end
        self.starttime = starttime
        self.endtime = endtime


class giveaway:

    #list of giveaway attributes, used to c++ so I declared them for clarity
    giveaway_id = ""
    header = ""
    description = ""
    image = ""  #link to image
    number_of_winners = "1"
    winners = []  # list of the winner discord IDs
    losers = []
    entrants = []
    status = "active"

    def __init__(self, message=None):
        if not (message is None):
            self.giveaway_id = id_generator(message)

        self.header = "default header"
        self.description = "default description"
        self.image = "https://cdn-images-1.medium.com/max/800/1*TTOJz35-lJmjWGj59786GA.png"  #default pulled right from discord site
        self.number_of_winners = "1"
        self.timeframe = Timeframe("2000/01/01", "3000/01/01", "12:00",
                                   "12:00")
        self.winners = []
        self.losers = []
        self.entrants = []
        self.status = "active"
        self.number_of_winners = "1"
        self.replace_winners = 0
        #constructor
        return

    def draw_winners(self, winnercount):
        count = 0
        entrants = []
        for x in self.entrants:
            for i in range(read_write.entry_number(x)):
                entrants.append(str(x[0]))
                print("appending " + str(x[0]))
        self.winners = []
        if int(winnercount) > len(entrants):
            winnercount = len(entrants)
        while (count < int(winnercount)):
            self.winners = [secrets.choice(entrants)] + self.winners
            count += 1
            for i in entrants:  #to stop people from wining the same giveaway twice
                for j in self.winners:
                    if i == j:
                        entrants.remove(i)
                        break
        return self.winners

        #gets and sets


###############################################################################

    def set_winners(self, tuple_of_winners):
        self.winners = tuple_of_winners
        return

    def get_winners(self):
        return self.winners

    def set_losers(self, tuple_of_losers):
        self.losers = tuple_of_losers
        return

    def get_losers(self):
        return self.losers

    def get_entrants(self):
        entrant_tuple = ()
        for x in self.entrants:
            entrant_tuple = entrant_tuple + (x, )
        return entrant_tuple

    def add_entrant(self, entrant_id):
        self.entrants.append(entrant_id)
        return

    def set_entrants(self, tuple_of_entrants):
        self.entrants = tuple_of_entrants
        return

    def get_status(self):
        return self.status

    def set_status(self, status):
        self.status = status
        return

    def get_id(self):
        return self.giveaway_id

    def set_id(self, giveaway_id):
        self.giveaway_id = giveaway_id
        return

    def get_number_of_winners(self):
        return self.number_of_winners

    def set_number_of_winners(self, integer):
        self.number_of_winners = integer
        return

    def set_header(self, header):
        self.header = header
        return

    def get_header(self):
        return self.header

    def set_description(self, description):
        self.description = description
        return

    def get_description(self):
        return self.description

    def set_image(self, image):
        self.image = image
        return

    def get_image(self):
        return self.image
