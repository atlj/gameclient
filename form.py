#-*-coding:utf8;-*-
import curses
import os
def create(formadi,liste, mode = "normal"):
    global isim
    global red
    global s
    global asistan
    global screen
    screen = curses.initscr()
    curses.start_color()
    curses.init_pair(1,curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    red = curses.color_pair(2)
    s = curses.color_pair(1)
    h = curses.A_NORMAL
    pos = 0
    gl = "________ "*len(liste)
    liste2 = gl.split(" ")
    select = 0
    while 1:
        b = 4
        a = 0
        f = 4
        d = 0
        screen.clear()
        screen.border(0)
        screen.refresh()
        screen.addstr(1,1,formadi, curses.A_BOLD)
        screen.addstr(2,1,"(w)Yukari (s)Asagi (e)Sec (c)Devam Et")
        screen.addstr(pos + 4, 1, "-->")
        for oge in liste:
            if pos == a:
                screen.addstr(b, 5, liste[a], s)
            else:
                screen.addstr(b,5,liste[a], h)
            a = a + 1
            b = b + 1
        for oge in liste2:
            if pos == d:
                screen.addstr(f,24,liste2[d])
                if select ==1:
                    liste2[d] = screen.getstr(f, 24).decode("utf-8")
                    select = 0
            else:
                screen.addstr(f, 24, liste2[d])
            f = f + 1
            d = d + 1
        curses.noecho()
        screen.keypad(True)
        try:
            getkey = screen.getkey(15,1)
        except Exception as e:
            pass
        curses.echo()
        screen.keypad(False)
        if getkey == "w":
            if pos > 0:
                pos = pos - 1
            else:
                pos = len(liste)-1
        if getkey == "s":
            if pos < len(liste)-1:
                pos = pos + 1
            else:
                pos = 0
        if getkey == "e":
            select = 1
        if getkey == "c":
            if liste2[0] == "" or liste2[1] == "":
                continue
            if liste2[0] =="________":
                continue
                
            if liste2[1] =="________":
                continue
                
            if " " in liste2[0] or " " in liste2[1]:
                continue
                                        
            if mode == "normal":
                break
                
            if mode == "register":
                user = liste2[0]
                passw = liste2[1]
                passw_control = liste2[2]
                
                if " " in user or " " in passw or " " in passw_control:
                    continue
                    
                if user == "" or passw == "" or passw_control == "":
                    continue
                    
                if not len(passw) >= 8:
                    alertwindow("Sifreniz 8 Karakterden", "Buyuk Olmalidir") 
                    
                if not passw == passw_control:
                    alertwindow("Girdiginiz Sifre Ile", "Tekrar Eslesmiyor")
                    liste2[2] = ""
                    continue
                    
            if mode == "connect":

                try:
                   liste2[1] = int(liste2[1])
                   break
                except ValueError:
                   alertwindow("Port Degeri", "Bir Sayi Olmali")
                   liste2[1] = ""
                   continue
                
            if mode == "login":
                if not len(liste2[0])>=4:                    
                    alertwindow("Kullanici Adi En Az", "3 Karakterden Olusmali")
                    liste2[0] = ""
                    continue
                
                if not len(liste2[1]) >=8:
                    alertwindow("Sifre En Az", "8 Karakterden Olusmali")
                    liste2[1] == ""
                    continue
                break
                
           
    screen.refresh()
    curses.endwin()
    curses.echo()
    os.system("clear")
    return liste2
    
def alertwindow(line1, line2):
    window = curses.newwin(7, 30,3 ,5)
    window.addstr(1,1,line1,curses.A_BOLD)
    window.addstr(2,1,line2, curses.A_BOLD)
    window.addstr(4,1,"Devam Etmek İcin",s)
    window.addstr(5,1,"Bir Tusa Basin",s)
    window.border(0)
    window.refresh()
    curses.noecho()
    screen.keypad(True)
    screen.getkey(15,1)
    


if __name__ == "__main__":
    form = input("//")
    liste = input(">>").split(" ")
    print(create(form, liste, "login"))