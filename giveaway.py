import discord
import hashlib
import mysql.connector
import secrets

database = mysql.connector.connect(
        auth_plugin = "mysql_native_password",
        host = "localhost",
        user = "TC",
        passwd = "tcbotpass",
        database = "tcgiveaway"
)
cursor = database.cursor()

#ordered id gen
def id_generator(message):
    sql = "SELECT *  FROM giveaways"
    cursor.execute(sql)
    data  = cursor.fetchall()
 #   for x in data:
 #       print (x)
    x = 0
    for i in data:
        if x == int(i[0]):
            x += 1
    database.commit()
    return str(x)

# random id gen
#def id_generator(message):
#    encrypt = str(message.timestamp)
#    sha256 =int( hashlib.sha256(encrypt.encode()).hexdigest(),16) % 10**8
#    return str(sha256)

#Timeframe as helper object
class Timeframe:
    def __init__(self, start, end, starttime,endtime):
        self.start = start
        self.end = end
        self.starttime = starttime
        self.endtime = endtime


class giveaway:

   #list of giveaway attributes, used to c++ so I declared them for clarity
    giveaway_id = ""
    header = ""
    description = ""
    image= ""#link to image
    number_of_winners = "1"
    winners = []  # list of the winner discord IDs
    losers = []
    entrants = []
    status = "active"


    def __init__(self, message=None):
        if not(message is None):
            self.giveaway_id = id_generator(message)

        self.header = "default header"
        self.description = "default description"
        self.image = "https://cdn-images-1.medium.com/max/800/1*TTOJz35-lJmjWGj59786GA.png"#default pulled right from discord site
        self.number_of_winners = "1"
        self.timeframe = Timeframe("xxx","xxx","xxx","xxx")
        self.winners = []
        self.losers = []
        self.entrants = []
        self.status = "active"
        self.number_of_winners = "1"
        #constructor
        return
    def draw_winners(self, winnercount):
        x = 0
        entrants = self.entrants
        self.winners = []
        while (x<int(winnercount)):
            self.winners = [secrets.choice(entrants)] + self.winners
            x += 1
            for i in entrants: #to stop people from wining the same giveaway twice
                for j in self.winners:
                    if i == j:
                        entrants.remove(i)
        return self.winners


                        #gets and sets
###############################################################################
    def set_winners(self,tuple_of_winners):
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
            entrant_tuple = entrant_tuple + (x,) 
        return entrant_tuple

    def add_entrant(self,entrant_id):
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
    def set_timeframe(self,start_end, date, time):
        if (start_end == "start"):
            self.timeframe.start = date
            self.timeframe.starttime = time
            return
        elif (start_end == "end"):
            self.timeframe.end = date
            self.timeframe.endtime = time
            return
        else:
            raise ValueError('There was an error with the timeframe for giveaway:' + self.id)
            return

    def set_header(self,header):
        self.header = header
        return

    def get_header(self):
        return self.header

    def set_description(self,description):
        self.description = description
        return

    def get_description(self):
        return self.description

    def set_image(self,image):
        self.image = image
        return
        
    def get_image(self):
        return self.image
