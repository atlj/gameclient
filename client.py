import socket, time, os, json, curses
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cdir = os.path.dirname(os.path.realpath(__file__))+"/"


class logger(object):
    def __init__(self, logtype):
        self.logname = logtype +"log" + " "+time.ctime()
        self.logdir = "{}logs/".format(cdir)
        self.logtype = logtype

    def write(self, data):
        
        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)
        
        if not os.path.exists(self.logdir+self.logname):#her logdan once dosya acmayi engellemek icin
            self.logfile = open(self.logdir+self.logname, "w")

        self.logfile.write(time.ctime().split(" ")[3] + ">>"+ " ["+self.logtype+"] >> "+data+"\n")
        self.logfile.flush()
        os.fsync(self.logfile.fileno())#dosyayi kapatmadan verileri yazmak icin


class client(object):
    def __init__(self, ip, port):
        self.log = logger("client")
        self.connect(ip, port)
        self.ip = ip
        self.port = port

    def connect(self, ip, port):
        s.connect((ip, port))

    def listener(self):#serverdan gelen tum veriyi manupule eden kod blogu
        while 1:
            try:
                message = s.recv(1024**2).decode("utf-8")
            except socket.error:
                print("baglanti koptu")
                self.log.write("baglanti koptu")

            try:
                package = json.loads(message)

            except Exception as e:#hata adi sistemden sisteme farklilik gosteriyor.
                self.log.write("veri islenemedi: "+message)
            #TODO error handler classi acilabilir
        
    def send(self, data):
        try:
            s.send(bytes(json.dumps(data), "utf-8"))

        except json.decoder.JSONDecodeError:
            self.log.write("gonderilecek veri islenemedi:" +data)

        except socket.error:
            self.log.write("sockette meydana gelen hatadan dolayi paket gonderilemedi: "+data)


class gui(object):

    def __init__(self, max_x, max_y, tb_height = 5, tb_width = 30):
        self.log = logger("gui")
        self.max_x = max_x
        self.max_y = max_y
        self.screen = curses.initscr()
        curses.start_color() #curses renkleri
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

    def linecache(self, line):#sutunlari onyukler
        self.ycache = []
        for location in self.map:
            if location["y"] == line:
                self.ycache.append(location)

    def getline(self, x):#satirlarin icerigine gore cikti gonderir

        if self.ycache == []:
            return "_"

        else:
            for location in self.ycache:
                if x == location["x"]:
                    return location["marker"]
                else:
                    return "_"
                    
    def is_showed(self, location):#world mapte f ye basinca lokasyonu ekranda mi diye kontrol eder
        x = location["x"]
        y = location["y"]
        if x == 0:
            if y == 0:
                return False
        if y<=self.cur_y+self.max_y:
            if y >= self.cur_y:
                if x<=self.cur_x + self.max_x:
                    if x>= self.cur_x:
                        return True
        return False
        
    def select(self, direction):#q ve e tuslarinin secim yapmasi
        ycache2 = []
        self.cache = []
        cache_count = -1
        for location in self.map:#once sutunları tarayıp ekranda olanları donduruyor
            if location["y"] <= self.cur_y + self.max_y:
                if location["y"] > self.cur_y:
                    ycache2.append(location)
        
        if not ycache2 == []:#daha sonra satirlari isliyor
            for location in ycache2:
                if location["x"] <= self.cur_x+self.max_x:
                    if location["x"] > self.cur_x:
                        self.cache.append(location)
                        cache_count += 1

        def sort_key(data):#son olarak x e gore tekrar siraliyor
            return data["x"]
        self.cache = sorted(self.cache, key=sort_key)
        
        if direction == "next":#e tusu
            if not self.cache == []:
                self.location_index += 1
                try:
                    self.selected = self.cache[self.location_index]
                except IndexError:
                    self.location_index = 0
                    self.selected = self.cache[0]

            else:
                self.selected = {"x":0, "y":0}

        if direction == "back":#q tusu
            if not self.cache == []:
                self.location_index = self.location_index - 1
                try:
                    self.selected = self.cache[self.location_index]
                except IndexError:
                    self.location_index = cache_count
                    self.selected = self.cache[cache_count]
                    
    def placemenu(self, data):#g tusuna basinca acilan menunun kontrol edilmesi
        count = 0
        width = 30
        cursor_pos = 1
        pagecount = 1
        itemcount = 0
        pages = []
        page_count = 0
        cur_page = []
        cur_page_index = 0
        for place in data:#tum lokasyonlari sayfalara gore siniflandirir
            count +=1
            itemcount += 1
            cur_page.append(place)
            if itemcount == self.max_y:
                pages.append(cur_page)
                page_count += 1
                itemcount = 0
                cur_page = []

        if not cur_page == []:#siniflandirmadan arda kalanlari tek bi sayfaya toplar
            pages.append(cur_page)
            page_count += 1
            last_count = itemcount

        else:
            last_count = self.max_y


        if count > self.max_y:
            count = self.max_y
            
        menu = curses.newwin(count +2, width, 1, int(self.max_x/2)-int(width/2))
        while 1:
            menu.clear()
            ndx = 1
            for place in pages[cur_page_index]:
                if ndx == cursor_pos:
                    menu.addstr(ndx, 1, place["quickinfo"][0], self.green)
                else:
                    menu.addstr(ndx, 1, place["quickinfo"][0])
                ndx += 1
            
            self.tb.placemenu_tb()
            menu.border(0)
            menu.refresh()
        
            curses.noecho()
            self.screen.keypad(True)
            getkey = self.screen.getkey(self.max_y+1, 1)
            if getkey == "g":
                break

            if getkey == "w":
                if not cursor_pos == 1:
                    cursor_pos = cursor_pos -1

                else:
                    if cur_page_index == 0:#eger ilk sayfa disinda herhangi bir sayfada ilk nesnedeyken w ya basilirsa gerideki sayfaya doner
                        cursor_pos = last_count
                        cur_page_index = page_count -1

                    else:
                        cursor_pos = count#eger ilk sayfanin ilk nesnesinde w ya basilirsa son sayfaya atar
                        cur_page_index = cur_page_index -1

            if getkey == "s":
                if not cur_page_index == page_count-1:
                    if not cursor_pos == count:
                        cursor_pos += 1

                    else:
                        cursor_pos = 1#eger son sayfa disinda herhangi bir sayfada son nesnedeyken s ye basilirsa sonraki sayfanin ilk nesnesine gider
                        cur_page_index +=1

                else:
                    if cursor_pos == last_count:
                        cursor_pos = 1#eger son sayfada son ogede s ye basilirsa ilk sayfanin ilk nesnesine gider
                        cur_page_index = 0

                    else:
                        cursor_pos += 1
            if getkey == "f":
                return cursor_pos + cur_page_index * self.max_y 

        return False 
        
        
    def minimenu(self, data):
        width = 25
        count = 5
        if data["x"] - self.cur_x > self.cur_x+self.max_x-data["x"]:#bu satir da dahil olmak uzere ilerideki 10 satir pop-up pencerenin en uygun yerde acilmasi icin
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
            if getkey == "f":
                break
        
        

    def printmap(self):#Dunya haritasini ekrana yazdirir
        while 1:
            self.screen.clear()
            self.screen.refresh()
            self.screen.border(0)
            counter = 1
            for line in range(self.max_y):#sutunlari kontrol eder
                xcounter = 1
                self.linecache(self.cur_y+counter)
                for col in range(self.max_x):#satirlari kontrol eder
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
                
            if getkey == "g":
                highlighted = self.placemenu(self.map)
                if highlighted:
                    self.selected = self.map[highlighted- 1]
                    if self.selected["x"] - int(self.max_x/2)>0:
                        self.cur_x = self.selected["x"]- int(self.max_x/2)
                    else:
                        self.cur_x = 0

                    if self.selected["y"] - int(self.max_y/2)> 0:
                        self.cur_y = self.selected["y"] - int(self.max_y/2)

                    else:
                        self.cur_y = 0

                
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
        self.tb.addstr(1,1,"(w/a/s/d)",self.yellow)
        self.tb.addstr(1,10,":Yon", self.bold)
        self.tb.addstr(2,1,"(q/e)",self.yellow)
        self.tb.addstr(2,6,":Onceki/Sonraki Secim", self.bold)
        self.tb.addstr(3,1,"(f)",self.yellow)
        self.tb.addstr(3,4,":Bilgileri Goster",self.bold)
        self.tb.addstr(4,1,"(g)", self.yellow)
        self.tb.addstr(4,4,":Mekan Listesi",self.bold)
        self.tb.refresh()
        
    def quick_info_tb(self):
        self.tb.clear()
        self.tb.addstr(1,1,"(f)",self.yellow)
        self.tb.addstr(1,4,":Pencereyi Kapat",self.bold)
        self.tb.refresh()
        
    def placemenu_tb(self):
        self.tb.clear()
        self.tb.addstr(1,1,"(g)",self.yellow)
        self.tb.addstr(1,4,":Pencereyi Kapat", self.bold)
        self.tb.addstr(2,1,"(w/s)", self.yellow)
        self.tb.addstr(2,6,":Yukari/Asagi", self.bold)
        self.tb.addstr(3,1,"(f)", self.yellow)
        self.tb.addstr(3,4,":Sec", self.bold)
        self.tb.refresh()
        

ekran = gui(40,25,7,40)
ekran.cur_y = 0
ekran.cur_x = 0
ekran.map = [{"x":1,"y":1,"marker":"V","quickinfo":["Kahraman Köyü","Level 278","babatek Klanı"]},{"x":51,"y":11,"marker":"C", "quickinfo":["Yalı Kampı","Level: 67","atesli_55 Klanı"]},{"x":5,"y":6,"marker":"M","quickinfo":["Pussydestroyer Madeni","Level 69", "Biricik Klanı"]},{"x":10, "y":10, "marker":"c","quickinfo":["Swagboyyolo Kampı","Level 100","Babatek Klanı"]}]
def map_sort(data):
    return data["quickinfo"][0]
ekran.map = sorted(ekran.map, key=map_sort)
ekran.printmap()


