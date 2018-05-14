import socket, time, os, json, curses, form, menu
from threading import Thread
import pickle, random
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
            self.log.write(str(info_id)+str(":")+str(self.pool[info_id]))
            if self.pool[info_id]["id"] == data["id"]:
                return info_id
        return False

    def add(self,id,  data):
        self.pool[id] = data

    def add_rand(self, data):
        self.pool[self.getid()] = data

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

    def remove_by_id(self, id):
        try:
            del self.pool[id]
            self.info_ids.remove(id)
        except KeyError:
            self.log.write("havuzda {} diye bir id bulunamadigindan silme islemi basarisiz oldu".format(str(id)))
    def remove(self, data):
        info_id = self.findbyid(data)
        try:
            del self.pool[info_id]
 #           del self.info_ids[self.info_ids.index(info_id)]
        except KeyError:
            self.log.write("Veri, mevcut veritabaninda bulunmadigindan dolayi silinemedi: "+str(data))

    def sum(self, fltr):
        liste = []
        for element in self.pool:
            if self.pool[element]["datatype"] == fltr:
                liste.append(self.pool[element])
        self.log.write("Havuz Ozeti Sonuclari: Filtre:{}\n{}".format(str(fltr), str(liste)))
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
        self.socketqueue = []

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
            feedback = self.listen_once()
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
                message = message.replace("\\n", "").split("\n")[0]
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

        if self.socketqueue == [""]:
            self.socketqueue = []
        if not self.socketqueue == []:
            message = self.socketqueue.pop(0)
        else:
            try:
                message = s.recv(1024**2).decode("utf-8")
                if "\\n" in message:
                    message = message.replace("\\n", "")
                splitted = message.split("\n")
                if len(splitted) == 2:
                    message = splitted[0]
                else:
                    self.socketqueue = splitted
                    message = self.socketqueue.pop(0)
            except socket.error:
                self.log.write("Baglanti kesildi")
                feedback = self.err.connect_error()
                if not feedback:
                    pass#TODO buraya el at
                else:
                    self.ip = feedback[0]
                    self.port = feedback[1]
                    self.connect()
                    if self.state == "logged":
                        if self.login(self.user, self.passw):
                            print("HATA")#TODO buraya da bi el lazim


        try:
            package = json.loads(message)
            package["tag"]
            self.log.write("gelen veri(listen fonksiyonu) >> "+str(package))
            return package

        except Exception as e:#hata adi sistemden sisteme farklilik gosteriyor.
            self.log.write("Veri islenemedi: "+message)
            self.err.force_exit()



    def send(self, data):
        try:
            s.send(bytes(json.dumps(data)+"\n", "utf-8"))

        except json.decoder.JSONDecodeError:
            self.log.write("gonderilecek veri islenemedi:" +data)

        except socket.error:
            self.log.write("sockette meydana gelen hatadan dolayi paket gonderilemedi: "+str(data))
            #TODO edit here



class gui(object):

    def __init__(self, max_x, max_y, tb_height = 7, tb_width = 30):
        self.fps = 60 #Insert PCmasterrace Propaganda here
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
        self.armies = []
        self.lockmode = False
        self.client = None
        self.nb = notification_bar(max_y + tb_height + 2)
        #HARDCORE ALERT TODO fix here
        self.prices = {"troop_price":{"yaya_asker":{"Demir":"N/A", "Odun":"N/A", "Kil":"N/A"},"zirhli_asker":{"Demir":"N/A","Odun":"N/A", "Kil":"N/A"}, "atli_asker":{"Demir":"N/A","Odun":"N/A", "Kil":"N/A"}, "kusatma_makinesi":{"Demir":"N/A","Odun":"N/A", "Kil":"N/A"} }, "army_price": {"Demir":"N/A", "Odun":"N/A", "Kil":"N/A"}}
        #END OF HARDCODE
    def linecache(self, line):#sutunlari onyukler
        self.ycache = []
        for location in self.map:
            if location["y"] == line:
                self.ycache.append(location)

    def alert(self, text, **kwargs):
        #ozellikleri ayarlayan kisim
        linecount = 0
        max_len = 0
        if not isinstance(text, list):
            text = [text]
        for line in text:
            if len(line)>max_len:
                max_len = len(line)
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
            try:
                win.getkey(count +1, 1)#edit here
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)
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
            try:
                getkey = self.screen.getkey(self.max_y+1, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)
            curses.echo()
            self.screen.keypad(False)
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
            try:
                getkey = self.screen.getkey(self.max_y+1,1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)
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

    def army_screen(self):
        army_count = 0
        max_count = 8
        operation_list = ["[Yeni Bir Ordu Olustur]"]
        for army in self.armies:
            army_count += 1
            operation_list.append("{}".format(army["name"]+" "+army["general_name"]+" "+str(army["total_size"])))
        pos = 0
        adix = 5#addition to index
        while 1:
            self.screen.clear()
            self.screen.addstr(1, 1, "Ordu Menusu", self.bold)
            self.screen.addstr(2, 1, "Sahip Oldugunuz Ordular {}/{}".format(str(army_count), str(max_count)), self.bold)
            index = 0
            for operation in operation_list:
                if index == pos:
                    self.screen.addstr(index+adix, 1, operation, self.green)
                else:
                    self.screen.addstr(index+adix, 1, operation)
                index += 1

            self.screen.refresh()
            self.tb.army_tb()
            curses.noecho()
            self.screen.keypad(True)
            try:
                getkey = self.screen.getkey(max_count +1 + adix, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)
            curses.echo()
            self.screen.keypad(False)
       
            if getkey == "w":
                if not pos == 0:
                    pos = pos -1
                else:
                    pos = army_count 
        
            if getkey == "s":
                if not pos == army_count:
                    pos +=1
                else:
                    pos = 0

            if getkey == "f":
                if not pos == 0:
                    self.army_operation(self.armies[pos-1])
                else:
                    self.create_army()

            if getkey == "q":
                break
    def army_operation(self, army):
        pos = 0
        span = 3
        islemler = ["Birlikleri Goruntule", "Yeni Bir Birlik Olustur", "Formasyonu Duzenle", "Hareket Ettir"]
        while 1:
            ndx = 1
            self.screen.clear()
            self.screen.addstr(1, 1, "Ordu Menusu", self.bold)
            self.screen.addstr(2, 1, "Ordu Adi: {} General Adi: {}".format(army["name"], army["general_name"]), self.bold)

            for islem in islemler:
                if pos + 1 == ndx:
                    self.screen.addstr(ndx+span, 1, islem, self.green)
                else:
                    self.screen.addstr(ndx+span, 1, islem)
                ndx +=1

            self.screen.refresh()
            self.tb.army_operation_tb()
            self.screen.keypad(True)
            curses.noecho()
            try:
                getkey = self.screen.getkey(len(islemler)+span+1, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)
            self.screen.keypad(False)
            curses.echo()

            if getkey == "w":
                if not pos == 0:
                    pos = pos -1
                else:
                    pos = len(islemler)- 1

            if getkey == "s":
                if not pos == len(islemler) -1:
                    pos +=1
                else:
                    pos = 0

            if getkey == "q":
                break

            if getkey == "f":
                if pos == 0:#Birlikleri Goruntule
                    liste = []
                    for troop in army["troops"]:
                        liste.append(troop["name"])
                    if liste == []:
                        self.alert(["Sectiginiz Orduda", "Herhangi Bir Birlik Bulunmuyor"])
                        continue
                    feedback = self.common_menu(liste, "Birlikleri Goruntule", "Ordu Adi: {}, General Adi: {}".format(army["name"], army["general_name"]))
                    pass #TODO make here
                if pos == 1:#Yeni Bir Birlik Olustur
                    self.create_troop(army)
                if pos == 2:#Formasyonu Duzenle
                    pass
                if pos == 3:#Hareket Ettir
                    self.move_army(army)

    def common_menu(self, liste, headertext, subtext):
        span = 4
        pos = 0
        max_count = 8
        pages = []
        rcount = 0
        if int(len(liste)/max_count)<len(liste)/max_count:
            rcount = int(len(liste)/max_count) + 1
        else:
            rcount = int(len(liste)/max_count)
        for i in range(rcount):
            pages.append([])
        page_pos = 0
        counter = 0
        cur_page_index = 0
        last_count = 0
        for element in liste:
            if not counter == max_count:
                pages[page_pos].append(element)
                counter += 1
                last_count +=1
            else:
                last_count = 1
                page_pos += 1
                pages[page_pos].append(element)
                counter = 1

        while 1:
            self.screen.clear()
            self.screen.addstr(1, 1, headertext, self.bold)
            self.screen.addstr(2, 1, subtext, self.bold)
            self.screen.addstr(3, 1, "Sayfa: {}/{}".format(str(cur_page_index + 1), str(len(pages))), self.bold)
            ndx = 1
            for element in pages[cur_page_index]:
                if pos+1 == ndx:
                    self.screen.addstr(ndx+span, 1, element, self.green)
                else:
                    self.screen.addstr(ndx+span, 1, element)
                ndx += 1
            self.screen.refresh()
            self.tb.common_tb()
            self.screen.keypad(True)
            curses.noecho()
            try:
                getkey = self.screen.getkey(max_count + span + 2, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(1)
            curses.echo()
            self.screen.keypad(False)

            if getkey == "w":
                if not pos == 0:
                    pos -= 1
                else:
                    if not cur_page_index == 0:
                        cur_page_index -= 1
                        pos = max_count - 1
                    else:
                        cur_page_index = len(pages) - 1
                        pos = last_count - 1

            if getkey == "s":
                if not cur_page_index == len(pages) - 1:
                    if not pos == len(pages[cur_page_index]) - 1:
                        pos +=1
                    else:
                        cur_page_index += 1
                        pos = 0
                else:
                    if not pos == last_count - 1:
                        pos += 1
                    else:
                        pos = 0
                        cur_page_index = 0

            if getkey == "f":
                return cur_page_index * max_count + pos

            if getkey == "q":
                break

            if getkey == "d":
                if not cur_page_index == len(pages) - 1:
                    cur_page_index += 1
                else:
                    cur_page_index = 0
                while not pos <= len(pages[cur_page_index])- 1:
                    pos -= 1

            if getkey == "a":
                if not cur_page_index == 0:
                    cur_page_index -= 1

                else:
                    cur_page_index = len(pages) - 1
                while not pos <= len(pages[cur_page_index]) - 1:
                    pos -= 1



    def move_army(self, army):
        ops = ["Bir Koordinata Gonder", "Bir Mekana Gonder"]
        pos = 0
        span = 3
        while 1:
            self.screen.clear()
            self.screen.addstr(1, 1, "Orduyu Hareket Ettir", self.bold)
            self.screen.addstr(2, 1, "Ordu Adi: {}, General Adi: {}".format(army["name"], army["general_name"]), self.bold)
            ndx = 1
            for op in ops:
                if pos +1 == ndx:
                    self.screen.addstr(ndx + span, 1, op, self.green)
                else:
                    self.screen.addstr(ndx+span, 1, op)
                ndx += 1
            self.screen.refresh()
            self.tb.army_operation_tb()
            curses.noecho()
            self.screen.keypad(True)
            try:
                getkey = self.screen.getkey(len(ops)+ span + 1, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)
            curses.echo()
            self.screen.keypad(False)

            if getkey == "w":
                if not pos == 0:
                    pos = pos -1
                else:
                    pos = len(ops) -1

            if getkey == "s":
                if not pos == len(ops) -1:
                    pos +=1
                else:
                    pos = 0

            if getkey == "q":
                break

            if getkey == "f":
                if pos == 0:
                    sublist = ["X:", "Y:"]
                    pre = ["___", "___"]
                    span = 3
                    spos = 0
                    while 1:
                        self.screen.clear()
                        self.screen.addstr(1, 1, "Bir Koordinata Gonder", self.bold)
                        self.screen.addstr(2, 1, "Ordu Adi: {}, General Adi: {}".format(army["name"], army["general_name"]), self.bold)
                        ndx = 1
                        for i in sublist:
                            if spos +1 == ndx:
                                self.screen.addstr(span + ndx, 1, i, self.green)
                            else:
                                self.screen.addstr(span+ndx, 1, i)
                            self.screen.addstr(span+ndx, 5, str(pre[sublist.index(i)]))
                            ndx +=1
                        self.screen.refresh()
                        self.tb.army_pos_tb()
                        curses.noecho()
                        self.screen.keypad(True)
                        try:
                            getkey = self.screen.getkey(span+ len(sublist)+2, 1)
                        except KeyboardInterrupt:
                            curses.endwin()
                            print("Istemci Sonlandirildi")
                            os._exit(0)

                        curses.echo()
                        self.screen.keypad(False)

                        if getkey == "w":
                            if not spos == 0:
                                spos = spos - 1
                            else:
                                spos = len(sublist) -1

                        if getkey == "s":
                            if not spos == len(sublist) - 1:
                                spos +=1
                            else:
                                spos = 0

                        if getkey == "q":
                            break

                        if getkey == "e":
                            try:
                                pre[spos] = self.screen.getstr(span + spos +1, 5)
                                pre[spos] = int(pre[spos])
                            except ValueError:
                                self.alert(["Girdiginiz Deger", "Bir Sayi Degeri Olmali"])
                                pre[spos] = "___"
                                continue
                            if pre[spos] <1:
                                self.alert(["Girdiginiz Deger", "Bir Pozitif Tamsayi Olmali"])
                                pre[spos] = "___"
                                continue

                        if getkey == "c":
                            try:
                                for i in pre:
                                    pre[pre.index(i)] = int(i)

                                self.client.send({"tag":"action", "data":[{"type":"move_army", 
                                "x":pre[0], "y":pre[1], "army_id":army["id"]}]})
                                break
                            except ValueError:
                                self.alert(["Girdiginiz Degerler", "Sayi Degerleri Olmali"])




    def common_minimenu(self, contains, headertext, subtext, span = 3):
        pos = 0
        while 1:
            self.screen.clear()
            self.screen.addstr(1, 1, headertext, self.bold)
            self.screen.addstr(2, 1, subtext, self.bold)
            ndx = 1
            for op in contains:
                if pos +1 == ndx:
                    self.screen.addstr(ndx + span, 1, op, self.yellow)
                else:
                    self.screen.addstr(ndx+span, 1, op)
                ndx +=1

            self.screen.refresh()
            self.tb.army_operation_tb()
            self.screen.keypad(True)
            curses.noecho()
            try:
                getkey = self.screen.getkey(len(contains)+span+1, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)

            curses.echo()
            self.screen.keypad(False)

            if getkey == "w":
                if not pos == 0:
                    pos = pos-1
                else:
                    pos = len(contains) -1

            if getkey == "s":
                if not pos == len(contains) -1:
                    pos += 1

                else:
                    pos = 0

            if getkey == "q":
                break

            if getkey == "f":
                return pos

    def create_troop(self, army):
        birlikler = ["Yaya Asker", "Zirhli Asker", "Atli Asker", "Kusatma Makinesi"]
        bio = ["", "", "", ""]#TODO bio yaz

        pos = 0
        span = 2
        while 1:
            self.screen.clear()
            self.screen.addstr(1, 1, "Birlik Olusturma", self.bold)
            ndx = 1

            for birlik in birlikler:
                if pos +1 == ndx:
                    self.screen.addstr(span + ndx, 1, birlik, self.green)
                else:
                    self.screen.addstr(span+ndx, 1, birlik)
                ndx +=1

            self.screen.refresh()
            self.tb.army_operation_tb()

            curses.noecho()
            self.screen.keypad(True)
            try:
                getkey = self.screen.getkey(len(birlikler)+span+1, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)

            if getkey == "w":
                if not pos == 0:
                    pos = pos - 1

                else:
                    pos = len(birlikler) -1

            if getkey == "s":
                if not pos == len(birlikler) -1:
                    pos +=1
                else:
                    pos = 0

            if getkey == "q":
                break

            if getkey == "f":
                name = birlikler[pos]
                name = name.lower()
                name = name.replace(" ", "_")
                price = ""
                for i in self.prices["troop_price"][name]:
                    price += "{}: {} ".format(i, str(self.prices["troop_price"][name][i]))
                while 1:
                    self.screen.clear()
                    self.screen.addstr(1, 1, "Birlik Olusturma", self.bold)
                    self.screen.addstr(3, 1, "Tur: ", self.yellow)
                    self.screen.addstr(3, 6, birlikler[pos], self.bold)
                    self.screen.addstr(4, 1, "Fiyat: ", self.yellow)
                    self.screen.addstr(4, 8, price, self.bold)
                    self.screen.addstr(5, 1, "Tanim: ", self.yellow)
                    self.screen.addstr(5, 8, bio[pos], self.bold)
                    self.screen.refresh()
                    self.tb.yn_tb()

                    curses.noecho()
                    self.screen.keypad(True)
                    try:
                        getkey = self.screen.getkey(7, 1)
                    except KeyboardInterrupt:
                        curses.endwin()
                        print("Istemci Sonlandirildi")
                        os._exit(0)
                    curses.echo()
                    self.screen.keypad(False)

                    if getkey == "e":
                        self.client.send({"tag":"action", "data":[{
                            "type":"create_troop",
                            "army_id":army["id"],
                            "troop_type":pos}]})
                        break

                    if getkey == "h":
                        break


    def create_army(self):
        price = ""
        
        for i in self.prices["army_price"]:
            price = price + i+": "+str(self.prices["army_price"][i])+" "
            
        pos = 0
        army_name = "___"
        general_name = "___"
        while 1:
            self.screen.clear()
            self.screen.addstr(1, 1, "Bir Ordu Olustur", self.bold)
            self.screen.addstr(2, 1, "Ordu Olusturma Fiyati:", self.bold)
            self.screen.addstr(3, 1, price, self.green)
            self.screen.addstr(pos + 5, 1, "-->", self.green)
            self.screen.addstr(5, 5, "Ordu Ismi")
            self.screen.addstr(5, 20, army_name)
            self.screen.addstr(6, 5, "General Ismi")
            self.screen.addstr(6, 20, general_name)
            self.screen.refresh()

            curses.noecho()
            self.screen.keypad(True)
            self.tb.create_army_tb()
            try:
                getkey = self.screen.getkey(7, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)
            curses.echo()
            self.screen.keypad(False)
            if getkey == "w":
                if not pos == 0:
                    pos = pos -1
                else:
                    pos = 1

            if getkey == "s":
                if not pos == 1:
                    pos +=1
                else:
                    pos = 0

            if getkey == "q":
                break

            if getkey == "e":
                if pos == 0:
                    army_name = self.screen.getstr(5, 20)
                if pos == 1:
                    general_name = self.screen.getstr(6, 20)

            if getkey == "c":
                if not len(army_name)>3:
                    self.alert(["Ordu Adi", "En Az 4 Karakter Olmali"])
                    continue
                if not len(general_name)>3:
                    self.alert(["General Adi", "En Az 4 Karakter Olmali"])
                    continue
                self.client.send({"tag":"create_army", "data":[str(army_name), str(general_name)]})
                break

    def frame_handler(self, fps):
        Thread(target=self.control).start()
        while 1:
            self.frame()
            time.sleep(1/fps)

    def frame(self):
        if self.frame_lock:
            self.screen.clear()
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
            if self.selected["x"] == 0:
                text = "x: {} y: {}".format(str(self.cur_x + int(self.max_x/2)),str(self.cur_y + int(self.max_y/2)))
            else:
                if self.is_showed(self.selected):
                    text = "x: {} y: {} Secim: {}".format(str(self.cur_x + int(self.max_x/2)), str(self.cur_y + int(self.max_y/2)), self.selected["name"])
                else:
                    text = "x: {} y: {}".format(str(self.cur_x + int(self.max_x / 2)), str(self.cur_y + int(self.max_y/2)))
            self.screen.addstr(self.max_y+ 1, int(self.max_x/2) - 4, text, self.bold)
            self.screen.refresh()
            self.nb.hud()
            if not self.lockmode:
                self.tb.world_tb()

    def control(self):#Dunya haritasini ekrana yazdirir
        while 1:
            self.frame_lock = True
            curses.noecho()
            self.screen.keypad(True)
            try:
                getkey = self.screen.getkey(self.max_y+1, 1)
            except KeyboardInterrupt:
                curses.endwin()
                print("Istemci Sonlandirildi")
                os._exit(0)
            curses.echo()
            self.screen.keypad(False)
            self.frame_lock = False

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

            if getkey == "k":#cikis yap
                miniscreen = curses.newwin(5, 37, int(self.max_y/2)-2, int(self.max_x/2)-16)
                pos = False
                while 1:
                    miniscreen.clear()
                    miniscreen.border(0)
                    miniscreen.addstr(1, 2, "Cikmak Istediginize Emin Misiniz?", self.bold)
                    if pos == False:
                        miniscreen.addstr(3, 9, "Hayir", self.green)
                        miniscreen.addstr(3, 20, "Evet")

                    if pos == True:
                        miniscreen.addstr(3, 9, "Hayir")
                        miniscreen.addstr(3, 20 ,"Evet", self.green)
                    miniscreen.refresh()
                    self.tb.yntb()
                    curses.noecho()
                    miniscreen.keypad(True)
                    getkey = miniscreen.getkey(3, 1)
                    curses.echo()
                    miniscreen.keypad(False)
                    if getkey in ["d", "a"]:
                        pos = not pos
                    if getkey == "e":
                        break

                if pos:
                    curses.endwin()
                    print("Istemci Sonlandirildi")
                    os._exit(0)

            if getkey == "p":#kale menusu
                player_menu_list = ["Ordu Tasarla"]#edit here
                highlighted = self.placemenu(player_menu_list) - 1
                
                if highlighted == 0:
                    self.army_screen()

            if getkey == "m":#material menusu
                self.lockmode = True
                self.materials()

            if getkey == "c":#dunya menusu
                world_menu_list = ["Oyunculari Goruntule"]
                highlighted = self.placemenu(world_menu_list) - 1
                if highlighted == 0:
                    pass


            if getkey == "b":#bildirimler
              while 1:
                not_read = []
                read = []
                read_header = []
                not_read_header = []
                for id in self.nb.feedpool.pool:
                    if id in self.nb.feedpool.pool[-1]:
                        not_read.append(self.nb.feedpool.pool[id])
                    else:
                        if not id == -1:
                            read.append(self.nb.feedpool.pool[id])

                if not read == []:
                    self.log.write(str(read))
                    read = sorted(read, reverse = True, key= lambda x:x["pos"])
                    for ntf in read:
                        read_header.append(ntf["header"])
                if not not_read == []:
                    not_read = sorted(not_read, reverse = True,key= lambda x:x["pos"])
                    for ntf in not_read:
                        not_read_header.append("*"+ntf["header"])

                fb = self.common_menu(["[Bildirimleri Sil]"]+not_read_header+read_header, "Bildirimler", "Okunmamis:{}, Toplam:{}".format(str(len(not_read)), str(len(not_read)+len(read))))
                if fb == None :
                    break
                if fb == 0:
                    pass#TODO delete notification menu

                else:
                    if fb <= len(not_read):
                        chosen = not_read[fb -1]
                    else:
                        chosen = read[fb -1-len(not_read)]
                    desc = chosen["desc"]
                    desclist = []
                    x, y = self.screen.getmaxyx()
                    if len(desc)>x:
                        count = 0
                        current = ""
                        for char in list(desc):
                            current += char
                            count += 1
                            if count == x:
                                desclist.append(current)
                                count = 0
                                current = ""
                        if not current == "":
                            desclist.append(current)
                    else:
                        desclist = [desc]
                    if chosen["type"] == "ntf":
                      while 1:
                        self.screen.clear()
                        self.screen.addstr(1, 5, chosen["header"], self.bold)
                        ndx = 0
                        for i in desclist:
                            self.screen.addstr(3+ndx, 1, i)
                            ndx += 1
                        self.screen.refresh()
                        self.tb.ntf_tb()
                        try:
                            self.nb.feedpool.pool[-1].remove(chosen["id"])#Bildirimi okunmus bildirimlerin idlerinin oldugu listeden kaldirmak icin.
                        except ValueError:#eger bildirim daha onceden okunmussa valuerror verir
                            pass
                        self.nb.feedpool.save()
                        curses.noecho()
                        self.screen.keypad(True)
                        try:
                            getkey = self.screen.getkey(9, 1)
                        except KeyboardInterrupt:
                            curses.endwin()
                            print("Istemci Sonlandirildi")
                            os._exit(0)
                        curses.echo()
                        self.screen.keypad(False)
                        if getkey == "q":
                            break
                        if getkey == "x":
                            self.nb.feedpool.remove_by_id(chosen["id"])
                            self.nb.feedpool.save()
                            break
                    if chosen["type"] == "msg":
                        pass#TODO
                    if chosen["type"] == "rqs":
                        pass#TODO


class notification_bar(object):
    def __init__(self,y):
        self.y = y
        self.green = curses.color_pair(10)
        self.yellow = curses.color_pair(11)
        self.feedpool = infopool("notification")
        self.feedpool.load()
        if not -1 in self.feedpool.pool:
            self.feedpool.pool[-1] = []
        self.config = config("notification_bar.conf")
        if not self.config.control():
            self.mode = "simple"
            self.config.add("mode", "simple")
        else:
            self.mode = self.config.config_table["mode"]

    def hud(self):
        if self.mode == "simple":
            self.simple()
        
    def simple(self):
        self.win = curses.newwin(3, 40, self.y, 1)
        self.win.clear()
        self.win.addstr(1, 1, "Okunmamis:", self.yellow)
        okunmamis_count = len(self.feedpool.pool[-1])
        self.win.addstr(1, 11, "{}".format(str(okunmamis_count)), self.green)
        self.win.border(0)
        self.win.refresh()


class toolbar(object):

    def __init__(self, toolbar_height,toolbar_width, max_y):
        self.tb = curses.newwin(toolbar_height, toolbar_width, max_y +2, 1)#tb = toolbar
        self.yellow = curses.color_pair(11)
        self.green = curses.color_pair(10)
        self.bold = curses.A_BOLD
        #self.tb.border(0)

    def yntb(self):
        self.tb.clear()
        self.tb.addstr(1, 1, "(a/d)", self.yellow)
        self.tb.addstr(1, 6, ":Sag/Sol", self.bold)
        self.tb.addstr(2, 1, "(e)", self.yellow)
        self.tb.addstr(2, 4, ":Sec", self.bold)
        self.tb.refresh()

    def world_tb(self):
        self.tb.clear()
        self.tb.addstr(1,1,"(w/a/s/d)",self.yellow)
        self.tb.addstr(1,10,":Yon", self.bold)
        self.tb.addstr(6,18, "(b)", self.yellow)
        self.tb.addstr(6,21, ":Bildirimler", self.bold)
        self.tb.addstr(2,1,"(q/e)",self.yellow)
        self.tb.addstr(2,6,":Onceki/Sonraki Secim", self.bold)
        self.tb.addstr(3,1,"(f)",self.yellow)
        self.tb.addstr(3,4,":Bilgileri Goster",self.bold)
        self.tb.addstr(4,1,"(g)", self.yellow)
        self.tb.addstr(4,4,":Mekan Listesi",self.bold)
        self.tb.addstr(5,1, "(p)", self.yellow)
        self.tb.addstr(5,4, ":Kale Menusu", self.bold)
        self.tb.addstr(5, 18, "(k)", self.yellow)
        self.tb.addstr(5, 21, ":Cikis Yap", self.bold)
        self.tb.addstr(6, 1, "(m)" , self.yellow)
        self.tb.addstr(6, 4, ":Materyaller", self.bold)
        self.tb.refresh()

    def army_tb(self):
        self.tb.clear()
        self.tb.addstr(1, 1, "(w/s)", self.yellow)
        self.tb.addstr(1, 6, ":Yukari/Asagi", self.bold)
        self.tb.addstr(2, 1, "(f)", self.yellow)
        self.tb.addstr(2, 4, ":Sec", self.bold)
        self.tb.addstr(3, 1, "(q)", self.yellow)
        self.tb.addstr(3, 4, ":Cik", self.bold)
        self.tb.refresh()

    def army_operation_tb(self):
        self.tb.clear()
        self.tb.addstr(1, 1, "(w/s)", self.yellow)
        self.tb.addstr(1, 6, ":Yukari/Asagi", self.bold)
        self.tb.addstr(2, 1, "(f)", self.yellow)
        self.tb.addstr(2, 4, ":Sec", self.bold)
        self.tb.addstr(3, 1, "(q)", self.yellow)
        self.tb.addstr(3, 4, ":Geri", self.bold)
        self.tb.refresh()

    def create_army_tb(self):
        self.tb.clear()
        self.tb.addstr(1, 1, "(w/s)", self.yellow)
        self.tb.addstr(1, 6, ":Yukari/Asagi", self.bold)
        self.tb.addstr(2, 1, "(e)", self.yellow)
        self.tb.addstr(2, 4, ":Sec", self.bold)
        self.tb.addstr(3, 1, "(c)", self.yellow)
        self.tb.addstr(3, 4, ":Devam Et", self.bold)
        self.tb.addstr(4, 1, "(q)", self.yellow)
        self.tb.addstr(4, 4, ":Cik", self.bold)
        self.tb.refresh()

    def ntf_tb(self):
        self.tb.clear()
        self.tb.addstr(1, 1, "(q)", self.yellow)
        self.tb.addstr(1, 4, ":Geri Don", self.bold)
        self.tb.addstr(2, 1, "(x)", self.yellow)
        self.tb.addstr(2, 4, ":Bildirimi Sil", self.bold)
        self.tb.refresh()

    def common_tb(self):
        self.tb.clear()
        self.tb.addstr(1, 1, "(w/s)", self.yellow)
        self.tb.addstr(1, 6, ":Yukari/Asagi", self.bold)
        self.tb.addstr(2, 1, "(q)", self.yellow)
        self.tb.addstr(2, 4, ":Geri", self.bold)
        self.tb.addstr(3, 1, "(f)", self.yellow)
        self.tb.addstr(3, 4, ":Sec", self.bold)
        self.tb.addstr(4, 1, "(d/a)", self.yellow)
        self.tb.addstr(4, 6, ":Sonraki/Onceki Sayfa", self.bold)
        self.tb.refresh()

    def army_pos_tb(self):
        self.tb.clear()
        self.tb.addstr(1, 1, "(w/s)", self.yellow)
        self.tb.addstr(1, 6, ":Yukari/Asagi", self.bold)
        self.tb.addstr(2, 1, "(e)", self.yellow)
        self.tb.addstr(2, 4, ":Sec", self.bold)
        self.tb.addstr(3, 1, "(c)", self.yellow)
        self.tb.addstr(3, 4, ":Devam Et", self.bold)
        self.tb.addstr(4, 1, "(q)", self.yellow)
        self.tb.addstr(4, 4, ":Geri", self.bold)
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

    def yn_tb(self):
        self.tb.clear()
        self.tb.addstr(1, 1, "(e)", self.yellow)
        self.tb.addstr(1, 4, ":Devam Et", self.bold)
        self.tb.addstr(2, 1, "(h)", self.yellow)
        self.tb.addstr(2, 4, "Geri", self.bold)
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
        self.log = logger("Handler")
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
            if tag == "create_army_feedback":
                if data == [True]:
                    self.gui.alert(["Ordu Olusturma", "Basarili"])
                else:
                    if data[1] == "err_name":
                        self.gui.alert(["Ayni Isimli Bir Ordu Bulunmakta"], pro_color = self.gui.yellow)
                    if data[1] == "err_material":
                        self.gui.alert(["Yetersiz Materyal"], pro_color = self.gui.yellow)
            if tag == "notification":
                for ntf in data:
                    randid = self.gui.nb.feedpool.getid()
                    ntf["id"]=randid
                    self.gui.nb.feedpool.pool[randid] = ntf
                    self.gui.nb.feedpool.pool[-1].append(randid)
                self.gui.nb.feedpool.save()
            if tag == "update":
                if "generic" in data[0]:
                    for element in data[0]["generic"]["replace"]:
                        for obj in element:
                            self.genericpool.replace(obj, element[obj])

                    for element in data[0]["generic"]["delete"]:
                        self.genericpool.remove(element)
                    self.genericpool.save()
                    self.gui.map = self.genericpool.sum("place")
                if "player" in data[0]:
                    for element in data[0]["player"]["replace"]:
                        for obj in element:
                            self.playerpool.replace(obj, element[obj])

                    for element in data[0]["player"]["delete"]:
                        self.playerpool.remove(element)
                    self.playerpool.save()
                    if not data[0]["player"]["replace"] == []:
                        element = self.playerpool.sum("materials")[0]
                        self.gui.iron = element["Demir"]
                        self.gui.clay = element["Kil"]
                        self.gui.wood = element["Odun"]
                        self.gui.materials_refresher()
                        self.gui.armies = self.playerpool.sum("army")


            if tag == "sync_feedback":
                for element in data[0]["generic"]["replace"]:
                    for obj in element:
                        self.genericpool.replace(obj, element[obj])
                    self.genericpool.save()
                for element in data[0]["generic"]["delete"]:
                    self.genericpool.remove(element)
                    self.genericpool.save()

                if not data[0]["generic"]["replace"] == [] or not data[0]["generic"]["delete"] == []:
                    self.gui.map = self.genericpool.sum("place")
                    self.gui.prices = self.genericpool.sum("prices")[0]["data"]
                
                for element in data[0]["player"]["replace"]:
                    for obj in element:
                        self.playerpool.replace(obj, element[obj])
                        self.playerpool.save()
                
                for element in data[0]["player"]["delete"]:
                    self.playerpool.remove(element)
                    self.playerpool.save()
                
                if not data[0]["player"]["replace"] == []:
                    element = self.playerpool.sum("materials")[0]
                    self.gui.iron = element["Demir"]
                    self.gui.clay = element["Kil"]
                    self.gui.wood = element["Odun"]
                    self.gui.materials_refresher()
                    self.gui.armies = self.playerpool.sum("army")
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
                self.client.send({"tag":"register_info", "data":[cr]})#burayi kontrol et
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
        self.client.send({"tag":"notification_control", "data":[]})
        self.sync(["generic", "player"],{"generic_idlist":self.genericpool.sum_ids(),"player_idlist":self.playerpool.sum_ids()})
        self.gui = gui(self.gui_height, self.gui_width, 7, 40)#burdaki harcode sikinti yapablir
        self.gui.client = self.client
        self.gui.map = self.genericpool.sum("place")
        self.gui.frame_handler(10)

if __name__ == "__main__":
    Handler_object = Handler(42, 18)
    Handler_object.loopmode = True
    Handler_object.main()
