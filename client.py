import socket, time, os, json, curses
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #socket objesi
cdir = os.path.dirname(os.path.realpath(__file__))+"/"


class logger(object):
    def __init__(self, logtype):
        logname = "clientlog" + " "+time.ctime()
        logdir = "{}logs/".format(cdir)
        self.logtype = logtype
        if not os.path.exists(logdir):
            os.makedirs(logdir)

    def write(self, data):
        if not os.path.exists(logdir+logname):#her logdan once dosya acmayi engellemek icin
            logfile = open(logdir+logname, "w")

        logfile.write(time.ctime().split(" ")[3] + ">>"+ " ["+self.logtype+"] "+data)
        logfile.flush()
        os.fsync(logfile.fileno())#dosyayi kapatmadan verileri yazmak icin


class client(object):
    def __init__(self, ip, port):
        self.connect(ip, port)
        self.ip = ip
        self.port = port
        self.log = logger("client")

    def connect(self, ip, port):
        s.connect((ip, port))

    def listener(self):#serverdan gelen tum veriyi manupule eden kod blogu
        while 1:
            try:
                message = s.recv(1024**2).decode("utf-8")
            except socket.error:
                print("baglanti koptu")
                self.log.write("baglanti koptu")

                #TODO: bildirim gonder

            try:
                package = json.loads(message)

            except Exception as e:#hata adi sistemden sisteme farklilk gosteriyor.
                self.log.write("veri islenemedi: "+message)

        
    def send(self, data):
        try:
            s.send(bytes(json.dumps(data), "utf-8"))

        except json.decoder.JSONDecodeError:
            self.log.write("gonderilecek veri islenemedi:" +data)

        except socket.error:
            self.log.write("sockette meydana gelen hatadan dolayi paket gonderilemedi: "+data)


class gui(object):

    def __init__(self, max_x, max_y, tb_height = 5, tb_width = 30):
        self.max_x = max_x
        self.max_y = max_y
        self.screen = curses.initscr()
        curses.start_color()
        curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(11, curses.COLOR_YELLOW,curses.COLOR_BLACK)
        self.yellow = curses.color_pair(11)
        self.green = curses.color_pair(10)
        self.bold = curses.A_BOLD
        self.tb = toolbar(tb_height, tb_width, max_y)
        self.cursor_x = 1
        self.cursor_y = 1
        self.location_index = 0
        self.selected = {"x":0, "y":0}

    def linecache(self, line):
        self.ycache = []
        for location in self.map:
            if location["y"] == line:
                self.ycache.append(location)

    def getline(self, x):

        if self.ycache == []:
            return "_"

        else:
            for location in self.ycache:
                if x == location["x"]:
                    return location["marker"]
                else:
                    return "_"
                    
    def is_showed(self, location):
        x = location["x"]
        y = location["y"]
        if y<=self.cur_y+self.max_y:
            if y >= self.cur_y:
                if x<=self.cur_x + self.max_x:
                    if x>= self.cur_x:
                        return True
        return False
                    
        
    def select(self, direction):
        ycache2 = []
        self.cache = []
        for location in self.map:
            if location["y"] <= self.cur_y + self.max_y:
                if location["y"] >= self.cur_y:
                    ycache2.append(location)

        if not ycache2 == []:
            for location in ycache2:
                if location["x"] <= self.cur_x+self.max_x:
                    if location["x"] >= self.cur_x:
                        self.cache.append(location)

        if direction == "next":
            if not self.cache == []:
                self.location_index += 1
                try:
                    self.selected = self.cache[self.location_index]
                except IndexError:
                    self.location_index = 0
                    self.selected = self.cache[0]

            else:
                self.selected = {"x":0, "y":0}

        if direction == "back":
            if not self.cache == []:
                self.location_index = self.location_index - 1
                try:
                    self.selected = self.cache[self.location_index]

                except IndexError:
                    self.location_index = 0
                    self.selected = self.cache[0]

    def minimenu(self, data):
        width = 20
        count = 5
        if data["x"] - self.cur_x > self.cur_x+self.max_x-data["x"]:
            x = data["x"] -self.cur_x- width -1
        else:
            x = data["x"]-self.cur_x +2
        
        if data["y"]-self.cur_y >  self.cur_y + self.max_y - data["y"]:
            y = data["y"] -self.cur_y - int(count/2)
        else: 
            y = data["y"]-self.cur_y 
        menu = curses.newwin(count, width,y,x)
        menu.border(0)
        ndx = 1
        for info in data["quickinfo"]:
            menu.addstr(ndx,1,info)
            ndx +=1
        menu.refresh()      
        self.tb.quick_info_tb()
        while 1:
            curses.noecho()
            self.screen.keypad(True)
            getkey = self.screen.getkey(self.max_y+1,1)
            curses.echo()
            self.screen.keypad(False)
            if getkey == "q":
                break
        
        

    def printmap(self):
        while 1:
            self.screen.clear()
            self.screen.refresh()
            self.screen.border(0)
            counter = 1
            for line in range(self.max_y):
                xcounter = 1
                self.linecache(self.cur_y+counter)
                for col in range(self.max_x):
                    if self.cur_y +counter == self.selected["y"]:
                        if self.cur_x +xcounter == self.selected["x"]:
                            self.screen.addstr(counter, xcounter +1, self.getline(self.cur_x+xcounter), self.green)
                        else:
                            self.screen.addstr(counter,xcounter +1,self.getline(self.cur_x+xcounter))

                    else:        
                        self.screen.addstr(counter,xcounter +1,self.getline(self.cur_x+xcounter))
                    xcounter +=1
                counter += 1
            self.screen.refresh()
            self.tb.world_tb()
            curses.noecho()
            self.screen.keypad(True)
            getkey = self.screen.getkey(self.max_y+1, 1)
            curses.echo()
            self.screen.keypad(False)
          
            if getkey == "q":
                self.select("back")

            if getkey == "e":
                self.select("next")

            if getkey == "d":
                self.cur_x += 1

            if getkey == "a":
                if not self.cur_x == 0:
                    self.cur_x = self.cur_x -1

            if getkey == "w":
                if not self.cur_y == 0:
                    self.cur_y = self.cur_y -1

            if getkey == "s":
                self.cur_y +=1
                
            if getkey == "f":
                if self.is_showed(self.selected):
                    self.minimenu(self.selected)
                
class toolbar(object):

    def __init__(self, toolbar_height,toolbar_width, max_y):
        self.tb = curses.newwin(toolbar_height, toolbar_width, max_y +2, 1)#tb = toolbar
        self.yellow = curses.color_pair(11)
        self.green = curses.color_pair(10)
        self.bold = curses.A_BOLD
        #self.tb.border(0)

    def world_tb(self):
        self.tb.clear()
        self.tb.addstr(1,1,"w/a/s/d",self.yellow)
        self.tb.addstr(1,8,":Yon", self.bold)
        self.tb.addstr(2,1,"q/e",self.yellow)
        self.tb.addstr(2,4,":Onceki/Sonraki Secim", self.bold)
        self.tb.addstr(3,1,"f",self.yellow)
        self.tb.addstr(3,2,":Secim Yap",self.bold)
        self.tb.refresh()
        
    def quick_info_tb(self):
        self.tb.clear()
        self.tb.addstr(1,1,"q",self.yellow)
        self.tb.addstr(1,2,":Pencereyi Kapat",self.bold)
        self.tb.refresh()

ekran = gui(42,10)
ekran.cur_y = 0
ekran.cur_x = 0
ekran.map = [{"x":51,"y":11,"marker":"C", "quickinfo":["Yalı Kampı","Level: 67","atesli_55 Klanı"]},{"x":5,"y":6,"marker":"M","options":["Ele Gecir"]},{"x":10, "y":10, "marker":"c","options":[]}]
ekran.printmap()


