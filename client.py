import socket, time, os, json, curses, form, menu
from threading import Thread
import pickle
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
cdir = os.path.dirname(os.path.realpath(__file__))



class infopool(object):
    def __init__(self, name):
        self.name = name
        self.log = logger(self.name+" pool")
        self.pool = {}
        self.info_ids = []

    def getid(self):
        while 1:
            id = random.randint(1, 10**6)
            if id in self.info_ids:
                continue
            self.info_ids.append(id)
            return id

    def findbyid(self, data):
        for info_id in self.pool:
            if self.pool[info_id]["id"] == data["id"]:
                return info_id
        return False

    def add(self,id,  data):
        self.pool[id] = data

    def replace(self,newid,  data):
        old_id = self.findbyid(data)
        if old_id:
            del self.pool[old_id]
        self.add(newid, data)

    def sum_ids(self):
        idlist = []
        for id in self.pool:
            idlist.append(id)
        return idlist

    def remove(self, data):
        info_id = self.findbyid(data)
        try:
            del self.pool[info_id]
 #           del self.info_ids[self.info_ids.index(info_id)]
        except KeyError:
            self.log.write("Veri, mevcut veritabaninda bulunmadigindan dolayi silinemedi: "+str(data))

    def sum(self):
        liste = []
        for element in self.pool:
            liste.append(self.pool[element])
        return liste

    def __getitem__(self, index):
        return self.pool[index]

    def save(self):#pickle object dondurecek
        savelist = {"pool":self.pool,  "info_ids":self.info_ids}
        with open(os.path.join(cdir,self.name+ ".pooldata"), "wb") as dosya:
            pickle.dump(savelist, dosya)

    def load(self):#pickle object alicak
        if os.path.exists(os.path.join(cdir, self.name+".pooldata")):
            with open(os.path.join(cdir,self.name+ ".pooldata"), "rb") as dosya:
                loadlist = pickle.load(dosya)
            self.pool = loadlist["pool"]
            self.info_ids = loadlist["info_ids"]
        else:
            self.log.write(self.name+".pooldata dosyasi bulunamadigindan dolayi havuz yuklenemedi havuz: "+self.name)

class config(object):
    def __init__(self, config_name, directory = cdir):
        self.config_name = config_name
        self.directory = directory
        if self.control():
            self.config_table = self.load()
        else:
            self.config_table = {}

    def add(self, index, data):
        self.config_table[index] = data
        self.save(self.config_table)

    def check_index(self, data):
        try:
            self.config_table[data]
            return True

        except KeyError:
            return False

    def load(self):
        with open(os.path.join(self.directory,self.config_name), "r") as dosya:
           return json.load(dosya)

    def save(self, data):
        with open(os.path.join(self.directory,self.config_name), "w") as dosya:
            json.dump(data, dosya)

    def delete(self):
        os.remove(os.path.join(self.directory,self.config_name))
        self.config.table = {}

    def control(self):
        if os.path.exists(os.path.join(self.directory,self.config_name)):
           return True
        return False

class logger(object):
    def __init__(self, logtype):
        self.logname = logtype +"log" + " "+time.ctime()+".log"
        self.logdir = os.path.join(cdir, "logs")
        self.logtype = logtype

    def write(self, data):

        if not os.path.exists(self.logdir):
            os.makedirs(self.logdir)

        if not os.path.exists(os.path.join(self.logdir,self.logname)):#her logdan once dosya acmayi engellemek icin
            self.logfile = open(os.path.join(self.logdir,self.logname), "w")

        self.logfile.write(time.ctime().split(" ")[3] + " >>"+ " ["+self.logtype+"] >> "+data+"\n")
        self.logfile.flush()
        os.fsync(self.logfile.fileno())#dosyayi kapatmadan verileri yazmak icin


class client(object):
    def __init__(self, ip, port):
        self.log = logger("socket_client")
        self.ip = ip
        self.port = port
        self.err = Error_Handler()
        self.state = "no-connection"

    def register(self, user, passw):
        self.user = user
        self.passw = passw
        while 1:
            self.send({"tag":"register", "data":[{"user":self.user, "pass":self.passw}]})
            feedback = self.listen_once()
            if feedback["tag"] == "feedback":
                if feedback["data"] == [True]:
                    return True
                else:
                    feedback = self.err.register_error()
                    self.user = feedback[0]
                    self.passw = feedback[1]
                    continue
            else:
                self.log.write("sunucudan beklenmedik paket alindi alinan paket: "+str(feedback))
                self.err.force_exit()

    def positive_fb(self):
        self.send({"tag":"feedback", "data":[True]})

    def negative_fb(self, data = [False]):
        self.send({"tag":"feedback", "data":data})


    def login(self, user, passw):
        self.user = user
        self.passw = passw
        while 1:
            self.send({"tag":"login", "data":[{"user":self.user, "pass":self.passw}]})
            feedback = self.listen_once(35)
            if feedback["tag"] == "feedback":
                if feedback["data"] == [True]:
                    return True
                else:
                    feedback = self.err.login_error()
                    self.user = feedback[0]
                    self.passw = feedback[1]
                    continue
            else:
                self.log.write("giris yapilirken sunucudan beklenmedik paket alindi alinan paket: "+str(feedback))
                self.err.force_exit()

    def connect(self):
        while 1:
            try:
              if not self.state == "connected":
                s.connect((self.ip, self.port))
                self.state = "connected"
                self.log.write("Baglanti kuruldu")
              break
            except socket.error:
                self.log.write("Sunucuya baglanilamadi")
                feedback = self.err.connect_error()
                if not feedback:
                    continue

                else:
                    self.ip = feedback[0]
                    self.port = feedback[1]

    def listen_once(self, buff=1024**2):
        while 1:
            try:
                message = s.recv(buff).decode("utf-8")
                package = json.loads(message)
                self.log.write("gelen veri >> "+str(package))
                return package
            except socket.error:
                self.err.connect_error_critic()
                self.log.write("Tekli dinleme modunda baglanti basarisiz oldu ve program kapatildi")
                os._exit(0)
            except json.decoder.JSONDecodeError:
                self.log.write("Tekli dinleme modunda JSON decode basarisiz oldu paket: "+str(message))

    def listen(self):

        while 1:
            try:
                message = s.recv(1024**2).decode("utf-8")
            except socket.error:
                self.log.write("Baglanti kesildi")
                feedback = self.err.connect_error()
                if not feedback:
                    continue
                else:
                    self.ip = feedback[0]
                    self.port = feedback[1]
                    self.connect()
                    if self.state == "logged":
                        if self.login(self.user, self.passw):
                            continue


            try:
                package = json.loads(message)
                package["tag"]
                self.log.write("gelen veri >> "+str(package))
                return package

            except Exception as e:#hata adi sistemden sisteme farklilik gosteriyor.
                self.log.write("Veri islenemedi: "+message)
                self.err.force_exit()



    def send(self, data):
        try:
            s.send(bytes(json.dumps(data), "utf-8"))

        except json.decoder.JSONDecodeError:
            self.log.write("gonderilecek veri islenemedi:" +data)

        except socket.error:
            self.log.write("sockette meydana gelen hatadan dolayi paket gonderilemedi: "+data)
            #TODO edit here



class gui(object):

    def __init__(self, max_x, max_y, tb_height = 5, tb_width = 30):
        self.log = logger("gui")
        self.err = Error_Handler()
        self.max_x = max_x
        self.max_y = max_y
        self.cur_y = 0
        self.cur_x = 0#to edited
        self.screen = curses.initscr()
        curses.start_color() #curses renkleri
        curses.init_pair(10, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(11, curses.COLOR_YELLOW,curses.COLOR_BLACK)
        curses.init_pair(12, curses.COLOR_WHITE, curses.COLOR_BLACK)
        self.white = curses.color_pair(12)
        self.yellow = curses.color_pair(11)
        self.green = curses.color_pair(10)
        self.bold = curses.A_BOLD
        self.tb = toolbar(tb_height, tb_width, max_y)
        self.cursor_x = 1
        self.cursor_y = 1
        self.location_index = 0
        self.selected = {"x":0, "y":0}
        self.iron = 0
        self.clay = 0
        self.wood = 0

    def linecache(self, line):#sutunlari onyukler
        self.ycache = []
        for location in self.map:
            if location["y"] == line:
                self.ycache.append(location)

    def alert(self, text, **kwargs):
        #ozellikleri ayarlayan kisim
        linecount = 0
        if not isinstance(text, list):
            text = [text]
        if not "pro_text" in kwargs:
            pro_text = ["Devam Etmek Icin", "Bir Tusa Basin"]
        else:
            pro_text = kwargs["pro_text"]
        textlist = []
        for line in text:
            linecount += 1
            textlist.append(len(line))
        for line in pro_text:
            linecount += 1
            textlist.append(len(line))

        if not "x" in kwargs:
            x = int(self.max_x/2)-int(max_len/2)
        else:
            x = kwargs["x"]

        if not "y" in kwargs:
            y = int(self.max_y/2)-int(linecount/2+2)
        else:
            y = kwargs["y"]

        if not "size_y" in kwargs:
            size_y = linecount + 4
        else:
            size_y = kwargs["size_y"]

        if not "size_x" in kwargs:
            size_x = max(textlist)+4
        else:
            size_x = kwargs["size_x"]

        if not "color" in kwargs:
            color = self.white
        else:
            color = kwargs["color"]

        if not "pro_color" in kwargs:
            pro_color = self.green
        else:
            pro_color = kwargs["pro_color"]


        win = curses.newwin(size_y, size_x, y, x)
        win.border(0)
        while 1:

            count = 1
            for line in text:
                win.addstr(count, 2, line, color)
                count += 1

            for line in pro_text:
                win.addstr(count+1, 2, line, pro_color)
                count += 1
            win.refresh()
            curses.noecho()
            self.screen.keypad(True)
            win.getkey(count +1, 1)#edit here
            curses.echo()
            self.screen.keypad(False)
            break



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
            if y > self.cur_y:
                if x<=self.cur_x + self.max_x:
                    if x> self.cur_x:
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

    def placemenu(self, data,mode = "normal", width = 30):#genel amacli menu
        count = 0
        cursor_pos = 1
        pagecount = 1
        itemcount = 0
        pages = []
        page_count = 0
        cur_page = []
        cur_page_index = 0
        if len(data) == 0:
            self.log.write("placemenuye gelen verideki nesne sayisi 0 oldugundan dolayi placemenu acilamadi")
            return False
        for place in data:#sayfalara gore siniflandirir
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
                if mode == "place":
                    if ndx == cursor_pos:
                        menu.addstr(ndx, 1, place["quickinfo"][0], self.green)
                    else:
                        menu.addstr(ndx, 1, place["quickinfo"][0])
                
                if mode == "normal":
                    if ndx == cursor_pos:
                        menu.addstr(ndx, 1, place, self.green)
                    else:
                        menu.addstr(ndx, 1, place)
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

    def materials_refresher(self):
        if self.lockmode:
            self.tb.material_tb(self.wood, self.clay, self.iron)

    def materials(self):
        self.tb.material_tb(self.wood, self.clay, self.iron)
        while 1:
           curses.noecho()
           self.screen.keypad(True)
           getkey = self.screen.getkey(self.max_y +1, 1)
           curses.echo()
           self.screen.keypad(False)
           if getkey == "m":
               self.lockmode = False
               break


    def printmap(self):#Dunya haritasini ekrana yazdirir
        self.lockmode = False
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
            if not self.lockmode:
                self.tb.world_tb()
            curses.noecho()
            self.screen.keypad(True)
            getkey = self.screen.getkey(self.max_y+1, 1)
            curses.echo()
            self.screen.keypad(False)

            if getkey == "q":#onceki secim
                self.select("back")

            if getkey == "e":#sonraki secim
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

            if getkey == "g":#yer secici menusu
                highlighted = self.placemenu(self.map, "place")
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


            if getkey == "f":#secim yap
                if self.is_showed(self.selected):
                    self.minimenu(self.selected)

            if getkey == "p":#kale menusu
                player_menu_list = [""]#edit here
                highlighted = self.placemenu(player_menu_list)

            if getkey == "m":#material menusu
                self.lockmode = True
                self.materials()
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
        self.tb.addstr(5,1, "(p)", self.yellow)
        self.tb.addstr(5,4, ":Kale Menusu", self.bold)
        self.tb.addstr(6, 1, "(m)" , self.yellow)
        self.tb.addstr(6, 4, ":Materyaller", self.bold)
        self.tb.refresh()

    def material_tb(self, mt1, mt2, mt3 ):
        self.tb.clear()
        self.tb.addstr(1, 1, "Odun:", self.bold)
        self.tb.addstr(1, 7, str(mt1), self.yellow)
        self.tb.addstr(2, 1, "Kil:", self.bold)
        self.tb.addstr(2, 6, str(mt2), self.yellow)
        self.tb.addstr(3, 1, "Demir:", self.bold)
        self.tb.addstr(3, 8, str(mt3), self.yellow)
        self.tb.addstr(4, 1, "(m)", self.yellow)
        self.tb.addstr(4, 4, ":Geri Don", self.bold)
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

class Error_Handler(object):
    def __init__(self):
        self.menu = Menu_Screens()

    def login_error(self):
        os.system("clear")
        print("\n\tGecersiz Girdi Bilgileri\n\n\tc\tBilgileri Tekrar Gir\n\te\tCikis Yap")
        while 1:
            girdi = input("\t>>")
            if not girdi in ["e", "c"]:
                continue
            if girdi == "e":
                os._exit(0)
            if girdi == "c":
                info = self.menu.login_screen()
                return info

    def register_error(self):
        os.system("clear")
        print("\n\tKullanici Adi Kullanimda\n\n\te\tCikis Yap\n\tc\tBilgileri Tekrar Gir")
        while 1:
            feedback = input("\t>>")
            if not feedback in ["e", "c"]:
                continue

            if feedback == "e":
                return False

            if feedback == "c":
                feedback = self.menu.register_screen()
                return feedback

    def force_exit(self):
        os.system("clear")
        print("\n\tBeklenmedik Bir Hata Ile Karsilasildi\n\tProgram Kapatildi\n\tAyrintili Bilgi Icin Loglara Bakabilirsiniz.\n\tDevam Etmek Icin Enter'a Basin")
        input("")
        os._exit(0)

    def connect_error_critic(self):
        os.system("clear")
        print("\n\tSunucu Ile Baglanti Kurulamiyor\n\tProgramdan Cikis Yapilacak")

    def connect_error(self):
        os.system("clear")
        print("\n\tSunucu Ile Baglanti Kurulamiyor")
        print("\n\te\tTekrar Dene\n\tc\tBilgileri Tekrar Ayarla\n\tx\tCikis Yap\n")
        while 1:
            girdi = input("\t>>")
            if not girdi in ["e", "c", "x"]:
                continue

            if girdi == "e":
                return False
            if girdi == "c":
                newconf = self.menu.connect_screen()
                Handler_object.ip = newconf[0]
                Handler_object.port = newconf[1]
                Handler_object.conf.add("ip",newconf[0])
                Handler_object.conf.add("port", newconf[1])
                return newconf

            if girdi == "x":
                os._exit(0)


class Menu_Screens(object):

    def main_screen(self):
        return menu.create(["Giris Yap", "Kayıt Ol","Ayarlar"])

    def config_screen(self):
        pass

    def connect_screen(self):
        connect_info = form.create("Sunucu Bilgileri", ["Adres", "Port"],"connect")
        self.ip = connect_info[0]
        self.port = connect_info[1]
        return [self.ip, self.port]

    def login_screen(self):
        self.login_info = form.create("Giris Yap",["Kullanici Adi","Sifre"], "login")
        return self.login_info

    def register_screen(self):
        self.register_info = form.create("Kayit Ol", ["Kullanici Adi", "Sifre", "Sifre Tekrar"], "register")
        return self.register_info

    def name_screen(self):
        self.name_info = form.create("Kalenizin Adini Belirleyin", ["Kale Ismi"],"getname")
        return self.name_info[0]

class Handler(object):
    def __init__(self, gui_height, gui_width):
        self.gui_height = gui_height
        self.gui_width = gui_width
        self.conf = config("GameClient Config.conf")
        self.menu = Menu_Screens()
        self.err = Error_Handler()
        self.client = False #yalnizca bir kere client tanimlamak icin
        self.genericpool = infopool("genericpool")
        self.genericpool.load()
        self.playerpool = infopool("playerpool")
        self.playerpool.load()

    def main(self):
      os.system("clear")
      print("\n\n\tSocketGameClient\n\tCreated By:atlj\n\t\u001b[32mgithub.com/atlj\u001b[0m\n\tDevam etmek icin bir tusa basin")
      input("")
      while 1:
        choice = self.menu.main_screen()
        if choice in [0, 1]:
            if not self.conf.control():
                os.system("clear")
                print("\n\n\tHerhangi Bir Tanimli Sunucu Bulunamadi\n\tSunucu Yapilandirmaya Geciliyor\n\t\u001b[32mDevam Etmek İcin Enter'a Basin")
                input("")
                connect_info = self.menu.connect_screen()
                self.ip = connect_info[0]
                self.port = connect_info[1]
                self.conf.add("ip", self.ip)
                self.conf.add("port", self.port)
                if not self.client:
                    self.client = client(self.ip, self.port)
                self.client.connect()

            else:
                self.ip = self.conf.load()["ip"]
                self.port = self.conf.load()["port"]
                if not self.client:
                    self.client = client(self.ip, self.port)
                self.client.connect()

        if choice == 0:#login
            info = self.menu.login_screen()
            self.user = info[0]
            self.passw = info[1]
            if self.client.login(self.user, self.passw):
                self.runtime()#here we go

        if choice == 1:#register
            info = self.menu.register_screen()
            self.user = info[0]
            self.passw = info[1]
            if self.client.register(self.user, self.passw):
                continue

        if choice == 2:#config
            pass

    def listen_handler(self):
        while self.loopmode:
            feedback = self.client.listen()
            tag = feedback["tag"]
            data = feedback["data"]

            if tag == "sync_feedback":
                for element in data[0]["generic"]["replace"]:
                    for obj in element:
                        self.genericpool.replace(obj, element[obj])
                        self.genericpool.save()
                for element in data[0]["generic"]["delete"]:
                    self.genericpool.remove(element)
                    self.genericpool.save()
                
                for element in data[0]["player"]["replace"]:
                    for obj in element:
                        self.playerpool.replace(obj, element[obj])
                        self.playerpool.save()
                
                for element in data[0]["player"]["delete"]:
                    self.playerpool.remove(element)
                    self.playerpool.save()
                
                if not data[0]["player"]["replace"] == []:
                    for id in self.playerpool.pool:
                        element = self.playerpool.pool[id]
                        if "iron" in element:
                            
                            self.gui.iron = element["iron"]
                            self.gui.clay = element["clay"]
                            self.gui.wood = element["wood"]
                    self.gui.materials_refresher()
    def add_thread(self, number =1):
        for count in range(number):
            t = Thread(target=self.listen_handler)
            t.start()

    def control(self):
        self.client.send({"tag":"user_control", "data":[]})
        fb = self.client.listen_once()
        if False in fb["data"]:
            #Kale adi belirleme
            while 1:
                cr = self.menu.name_screen()
                self.client.send({"tag":"register_info", "data":[cr[0]]})#burayi kontrol et
                fb = self.client.listen_once()
                if fb["data"] == [False]:
                    continue
                break

    def sync(self, data, idlist):
        self.client.send({"tag":"sync", "data":[data, idlist]})

    def runtime(self):
        self.client.positive_fb()#hata verebilir
        self.control()
        self.add_thread()
        self.sync(["generic", "player"],{"generic_idlist":self.genericpool.sum_ids(),"player_idlist":self.playerpool.sum_ids()})
        self.gui = gui(self.gui_height, self.gui_width, 7, 40)#burdaki harcode sikinti yapablir
        self.gui.map = self.genericpool.sum()
        
        self.gui.printmap()

if __name__ == "__main__":
    Handler_object = Handler(42, 18)
    Handler_object.loopmode = True
    Handler_object.main()

"""
ekran = gui(42,18,7,40)

ekran.cur_y = 0
ekran.cur_x = 0
ekran.map = [{"x":1,"y":1,"marker":"V","quickinfo":["Kahraman Köyü","Level 278","babatek Klanı"]},{"x":51,"y":11,"marker":"C", "quickinfo":["Yalı Kampı","Level: 67","atesli_55 Klanı"]},{"x":5,"y":6,"marker":"M","quickinfo":["Pussydestroyer Madeni","Level 69", "Biricik Klanı"]},{"x":10, "y":10, "marker":"c","quickinfo":["Swagboyyolo Kampı","Level 100","Babatek Klanı"]}]
def map_sort(data):
    return data["quickinfo"][0]
ekran.map = sorted(ekran.map, key=map_sort)
ekran.printmap()
"""
