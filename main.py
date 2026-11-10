
import os, sqlite3, calendar
from datetime import date, datetime, timedelta
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, RoundedRectangle, Ellipse

BG=(.025,.028,.04,1); PANEL=(.105,.108,.145,1); CARD=(.155,.16,.205,1)
BLUE=(.34,.40,.96,1); GREEN=(.30,.88,.62,1); WHITE=(.95,.95,.98,1)
MUTED=(.61,.63,.70,1); RED=(.90,.30,.40,1)

def database(path):
    db=sqlite3.connect(path); db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS workouts(id INTEGER PRIMARY KEY, d TEXT, title TEXT, done INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS exercises(id INTEGER PRIMARY KEY, wid INTEGER REFERENCES workouts(id) ON DELETE CASCADE, name TEXT, note TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS sets(id INTEGER PRIMARY KEY, eid INTEGER REFERENCES exercises(id) ON DELETE CASCADE, n INTEGER, reps INTEGER DEFAULT 0, kg REAL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS body_weight(d TEXT PRIMARY KEY, kg REAL);
    """)
    db.commit(); return db

class WeightChart(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw); self.values=[]
        self.bind(size=self.draw, pos=self.draw)
    def set_values(self, rows): self.values=rows; self.draw()
    def draw(self,*_):
        self.canvas.clear()
        if self.width<20 or self.height<20: return
        with self.canvas:
            Color(*CARD); RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(8)])
            if not self.values: return
            vals=[float(x[1]) for x in self.values]; lo=min(vals); hi=max(vals)
            if lo==hi: lo-=.5; hi+=.5
            l=self.x+dp(22); r=self.right-dp(12); b=self.y+dp(20); t=self.top-dp(12)
            Color(*MUTED)
            for f in (.25,.5,.75):
                y=b+f*(t-b); Line(points=[l,y,r,y],width=.7)
            pts=[]
            for i,v in enumerate(vals):
                x=l if len(vals)==1 else l+i*(r-l)/(len(vals)-1)
                y=b+(v-lo)*(t-b)/(hi-lo); pts.extend([x,y])
            Color(*BLUE)
            if len(pts)>=4: Line(points=pts,width=2)
            Color(*GREEN)
            for i in range(0,len(pts),2): Ellipse(pos=(pts[i]-dp(4),pts[i+1]-dp(4)),size=(dp(8),dp(8)))

class WorkoutApp(App):
    def build(self):
        self.title="Workout Tracker"; Window.clearcolor=BG
        self.db=database(os.path.join(self.user_data_dir,"workouts.db"))
        self.selected=date.today(); self.yy=self.selected.year; self.mm=self.selected.month
        self.wid=None
        self.rootbox=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(8))
        self.home(); return self.rootbox
    def on_stop(self):
        try: self.db.commit(); self.db.close()
        except: pass
    def label(self,s,size=14,color=WHITE,h=None,bold=False):
        x=Label(text=str(s),font_size=dp(size),color=color,bold=bold,halign="left",valign="middle")
        if h is not None: x.size_hint_y=None; x.height=dp(h)
        x.bind(size=lambda o,v:setattr(o,"text_size",(v[0],None))); return x
    def btn(self,s,fn,color=BLUE,h=44):
        x=Button(text=s,size_hint_y=None,height=dp(h),background_normal="",background_down="",background_color=color,color=WHITE,font_size=dp(14))
        x.bind(on_release=lambda *_:fn()); return x
    def inp(self,hint,value="",multi=False,h=44):
        return TextInput(text=str(value),hint_text=hint,multiline=multi,size_hint_y=None,height=dp(h),font_size=dp(15),foreground_color=WHITE,hint_text_color=MUTED,background_normal="",background_active="",background_color=CARD,cursor_color=BLUE,padding=[dp(10),dp(9)])
    def panel(self):
        x=BoxLayout(orientation="vertical",padding=dp(10),spacing=dp(7),size_hint_y=None)
        x.bind(minimum_height=x.setter("height"))
        with x.canvas.before:
            Color(*PANEL); x.bg=RoundedRectangle(pos=x.pos,size=x.size,radius=[dp(12)])
        x.bind(pos=lambda o,v:setattr(o.bg,"pos",v),size=lambda o,v:setattr(o.bg,"size",v)); return x
    def clear(self): self.rootbox.clear_widgets()
    def header(self,title,back=None):
        bar=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        if back: bar.add_widget(self.btn("‹",back,CARD,42))
        bar.add_widget(self.label(title,20,BLUE,bold=True)); self.rootbox.add_widget(bar)
    def scroll(self):
        sv=ScrollView(do_scroll_x=False,bar_width=dp(3))
        c=BoxLayout(orientation="vertical",spacing=dp(10),padding=[0,dp(2),0,dp(18)],size_hint_y=None)
        c.bind(minimum_height=c.setter("height")); sv.add_widget(c); self.rootbox.add_widget(sv); return c
    def msg(self,s):
        Popup(title="Workout Tracker",content=Label(text=s,color=WHITE),size_hint=(.88,None),height=dp(170),background_color=PANEL).open()

    def home(self):
        self.clear(); self.header("WORKOUT TRACKER"); c=self.scroll()
        p=self.panel(); p.add_widget(self.label("КАЛЕНДАРЬ ТРЕНИРОВОК",14,WHITE,26,True))
        nav=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(8))
        nav.add_widget(self.btn("‹",lambda:self.month(-1),CARD,40))
        self.monthtxt=self.label("",15,BLUE,bold=True); nav.add_widget(self.monthtxt)
        nav.add_widget(self.btn("›",lambda:self.month(1),CARD,40)); p.add_widget(nav)
        self.cal=GridLayout(cols=7,spacing=dp(3),size_hint_y=None); self.cal.bind(minimum_height=self.cal.setter("height")); p.add_widget(self.cal); c.add_widget(p)
        p=self.panel(); p.add_widget(self.label("ТРЕНИРОВКИ ЗА ДЕНЬ",14,WHITE,25,True))
        self.daytxt=self.label("",12,GREEN,24); p.add_widget(self.daytxt)
        self.daylist=BoxLayout(orientation="vertical",spacing=dp(5),size_hint_y=None); self.daylist.bind(minimum_height=self.daylist.setter("height")); p.add_widget(self.daylist)
        p.add_widget(self.btn("+ НОВАЯ ТРЕНИРОВКА",self.new_workout,GREEN)); c.add_widget(p)
        p=self.panel(); p.add_widget(self.label("МОЙ ВЕС",14,WHITE,25,True))
        self.wdate=self.inp("Дата ГГГГ-ММ-ДД",self.selected.isoformat()); self.wvalue=self.inp("Вес в кг, например 70.5")
        p.add_widget(self.wdate); p.add_widget(self.wvalue); p.add_widget(self.btn("СОХРАНИТЬ ВЕС ЗА ЭТУ ДАТУ",self.save_weight,GREEN))
        self.wfeedback=self.label("Можно выбрать любую дату.",11,MUTED,22); p.add_widget(self.wfeedback); c.add_widget(p)
        p=self.panel(); p.add_widget(self.label("МОЯ СТАТИСТИКА",16,WHITE,28,True))
        self.stats=self.label("",12,WHITE,145); p.add_widget(self.stats)
        p.add_widget(self.label("ИЗМЕНЕНИЕ СОБСТВЕННОГО ВЕСА",13,GREEN,25,True))
        self.chart=WeightChart(size_hint_y=None,height=dp(190)); p.add_widget(self.chart)
        p.add_widget(self.label("ПОСЛЕДНИЕ ТРЕНИРОВКИ",13,GREEN,25,True))
        self.recent=self.label("",12,MUTED,100); p.add_widget(self.recent)
        p.add_widget(self.btn("ЭКСПОРТ АНАЛИЗА",self.export)); c.add_widget(p)
        self.refresh()
    def month(self,d):
        self.mm+=d
        if self.mm<1: self.mm=12; self.yy-=1
        if self.mm>12: self.mm=1; self.yy+=1
        self.calendar_draw()
    def calendar_draw(self):
        names=["","Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"]
        self.monthtxt.text=f"{names[self.mm]} {self.yy}"; self.cal.clear_widgets()
        for n in ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]: self.cal.add_widget(self.label(n,10,MUTED,24))
        key=f"{self.yy:04d}-{self.mm:02d}"
        marked={r[0] for r in self.db.execute("SELECT DISTINCT d FROM workouts WHERE substr(d,1,7)=?",(key,))}
        for week in calendar.monthcalendar(self.yy,self.mm):
            for day in week:
                if not day: self.cal.add_widget(Label(text="",size_hint_y=None,height=dp(43))); continue
                dt=date(self.yy,self.mm,day); sel=dt==self.selected
                b=self.btn(str(day)+(" •" if dt.isoformat() in marked else ""),lambda x=dt:self.pick(x),GREEN if sel else CARD,43)
                if sel: b.color=BG
                self.cal.add_widget(b)
    def pick(self,dt):
        self.selected=dt; self.wdate.text=dt.isoformat(); self.refresh()
    def refresh(self):
        self.calendar_draw(); self.daytxt.text=self.selected.strftime("%d.%m.%Y"); self.daylist.clear_widgets()
        rows=self.db.execute("SELECT id,title,done FROM workouts WHERE d=? ORDER BY id",(self.selected.isoformat(),)).fetchall()
        if not rows: self.daylist.add_widget(self.label("На эту дату тренировок нет.",12,MUTED,30))
        for wid,title,done in rows: self.daylist.add_widget(self.btn(("✓ " if done else "○ ")+title,lambda i=wid:self.workout(i),CARD))
        total=self.db.execute("SELECT COUNT(*) FROM workouts").fetchone()[0]
        month_count=self.db.execute("SELECT COUNT(*) FROM workouts WHERE substr(d,1,7)=?",(self.selected.strftime("%Y-%m"),)).fetchone()[0]
        nsets=self.db.execute("SELECT COUNT(*) FROM sets").fetchone()[0]
        ton=self.db.execute("SELECT COALESCE(SUM(reps*kg),0) FROM sets").fetchone()[0]
        best=self.db.execute("SELECT COALESCE(MAX(kg),0) FROM sets").fetchone()[0]
        streak=self.streak()
        self.stats.text=f"Всего тренировок: {total}\nТренировок за месяц: {month_count}\nКоличество подходов: {nsets}\nОбщий тоннаж: {ton:,.1f} кг\nЛучшая рабочая нагрузка: {best:g} кг\nСерия тренировок подряд: {streak} дн.".replace(","," ")
        weights=self.db.execute("SELECT d,kg FROM body_weight ORDER BY d").fetchall(); self.chart.set_values(weights)
        recent=self.db.execute("SELECT d,title,done FROM workouts ORDER BY d DESC,id DESC LIMIT 5").fetchall()
        self.recent.text="\n".join(f"{'✓' if done else '○'} {d} — {t}" for d,t,done in recent) or "Пока нет тренировок."
    def streak(self):
        dates={date.fromisoformat(r[0]) for r in self.db.execute("SELECT DISTINCT d FROM workouts WHERE done=1")}
        if not dates:return 0
        cur=date.today()
        if cur not in dates and cur-timedelta(days=1) in dates: cur-=timedelta(days=1)
        n=0
        while cur in dates: n+=1; cur-=timedelta(days=1)
        return n

    def new_workout(self):
        box=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(9)); field=self.inp("Название тренировки"); box.add_widget(field)
        pop=Popup(title="Новая тренировка",content=box,size_hint=(.9,None),height=dp(190),background_color=PANEL)
        def save():
            if not field.text.strip(): self.msg("Введи название тренировки."); return
            cur=self.db.execute("INSERT INTO workouts(d,title) VALUES (?,?)",(self.selected.isoformat(),field.text.strip()))
            self.db.commit(); wid=cur.lastrowid; pop.dismiss(); self.workout(wid)
        box.add_widget(self.btn("СОЗДАТЬ",save,GREEN)); pop.open()
    def workout(self,wid):
        self.wid=wid; row=self.db.execute("SELECT title,d,done FROM workouts WHERE id=?",(wid,)).fetchone()
        if not row: self.home(); return
        title,dt,done=row; self.clear(); self.header(title,self.home); c=self.scroll()
        c.add_widget(self.label(dt,12,GREEN,24))
        c.add_widget(self.btn("✓ ТРЕНИРОВКА ВЫПОЛНЕНА" if done else "ОТМЕТИТЬ КАК ВЫПОЛНЕННУЮ",lambda:self.toggle(wid),GREEN if done else CARD))
        c.add_widget(self.btn("+ ДОБАВИТЬ УПРАЖНЕНИЕ",lambda:self.new_exercise(wid)))
        exercises=self.db.execute("SELECT id,name,note FROM exercises WHERE wid=? ORDER BY id",(wid,)).fetchall()
        if not exercises:c.add_widget(self.label("Добавь первое упражнение.",12,MUTED,30))
        for eid,name,note in exercises:
            p=self.panel(); p.add_widget(self.label(name,15,GREEN,28,True))
            if note:p.add_widget(self.label("Описание: "+note,11,MUTED,38))
            sets=self.db.execute("SELECT id,n,reps,kg FROM sets WHERE eid=? ORDER BY n",(eid,)).fetchall()
            for sid,num,reps,kg in sets:
                rowbox=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(4))
                rowbox.add_widget(self.label(f"#{num}",11,WHITE,42))
                ri=self.inp("Повт.",reps); ri.input_filter="int"
                wi=self.inp("Кг",kg)
                rowbox.add_widget(ri); rowbox.add_widget(wi)
                rowbox.add_widget(self.btn("✓",lambda s=sid,r=ri,w=wi:self.save_set(s,r.text,w.text),GREEN,42))
                rowbox.add_widget(self.btn("×",lambda s=sid,i=wid:self.del_set(s,i),RED,42))
                p.add_widget(rowbox)
            p.add_widget(self.btn("+ ДОБАВИТЬ ПОДХОД",lambda e=eid,i=wid:self.add_set(e,i),CARD,40))
            p.add_widget(self.btn("УДАЛИТЬ УПРАЖНЕНИЕ",lambda e=eid,i=wid:self.del_exercise(e,i),RED,38))
            c.add_widget(p)
        c.add_widget(self.btn("УДАЛИТЬ ТРЕНИРОВКУ",lambda:self.del_workout(wid),RED))
    def toggle(self,wid):
        self.db.execute("UPDATE workouts SET done=1-done WHERE id=?",(wid,)); self.db.commit(); self.workout(wid)
    def new_exercise(self,wid):
        box=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
        name=self.inp("Название упражнения"); note=self.inp("Описание (необязательно)",multi=True,h=75)
        box.add_widget(name); box.add_widget(note)
        pop=Popup(title="Новое упражнение",content=box,size_hint=(.9,None),height=dp(260),background_color=PANEL)
        def save():
            if not name.text.strip(): self.msg("Введи название упражнения."); return
            cur=self.db.execute("INSERT INTO exercises(wid,name,note) VALUES (?,?,?)",(wid,name.text.strip(),note.text.strip()))
            eid=cur.lastrowid; self.db.execute("INSERT INTO sets(eid,n,reps,kg) VALUES (?,1,0,0)",(eid,))
            self.db.commit(); pop.dismiss(); self.workout(wid)
        box.add_widget(self.btn("ДОБАВИТЬ",save,GREEN)); pop.open()
    def add_set(self,eid,wid):
        n=self.db.execute("SELECT COALESCE(MAX(n),0)+1 FROM sets WHERE eid=?",(eid,)).fetchone()[0]
        self.db.execute("INSERT INTO sets(eid,n,reps,kg) VALUES (?,?,0,0)",(eid,n)); self.db.commit(); self.workout(wid)
    def save_set(self,sid,reps,kg):
        try:r=max(0,int(reps or 0)); w=max(0,float((kg or "0").replace(",",".")))
        except ValueError:self.msg("Проверь повторения и вес."); return
        self.db.execute("UPDATE sets SET reps=?,kg=? WHERE id=?",(r,w,sid)); self.db.commit(); self.workout(self.wid)
    def del_set(self,sid,wid):
        self.db.execute("DELETE FROM sets WHERE id=?",(sid,)); self.db.commit(); self.workout(wid)
    def del_exercise(self,eid,wid):
        self.db.execute("DELETE FROM exercises WHERE id=?",(eid,)); self.db.commit(); self.workout(wid)
    def del_workout(self,wid):
        self.db.execute("DELETE FROM workouts WHERE id=?",(wid,)); self.db.commit(); self.home()

    def save_weight(self):
        try:
            dt=date.fromisoformat(self.wdate.text.strip()); kg=float(self.wvalue.text.strip().replace(",","." ))
            if kg<=0 or kg>500: raise ValueError
        except ValueError:self.msg("Введи дату ГГГГ-ММ-ДД и вес, например 72.5."); return
        self.db.execute("INSERT OR REPLACE INTO body_weight(d,kg) VALUES (?,?)",(dt.isoformat(),kg))
        self.db.commit(); self.wfeedback.text=f"Сохранено: {kg:g} кг · {dt.isoformat()}"; self.refresh()
    def export(self):
        lines=["ОТЧЁТ WORKOUT TRACKER",f"Экспорт: {datetime.now():%Y-%m-%d %H:%M}",""]
        for wid,dt,title,done in self.db.execute("SELECT id,d,title,done FROM workouts ORDER BY d,id"):
            lines.append(f"{dt} | {title} | Выполнена: {'да' if done else 'нет'}")
            for eid,name,note in self.db.execute("SELECT id,name,note FROM exercises WHERE wid=? ORDER BY id",(wid,)):
                lines.append("  Упражнение: "+name)
                if note:lines.append("  Описание: "+note)
                for n,reps,kg in self.db.execute("SELECT n,reps,kg FROM sets WHERE eid=? ORDER BY n",(eid,)):
                    lines.append(f"    Подход {n}: {reps} повторений × {kg:g} кг")
            lines.append("")
        lines.append("СОБСТВЕННЫЙ ВЕС")
        for dt,kg in self.db.execute("SELECT d,kg FROM body_weight ORDER BY d"):lines.append(f"{dt}: {kg:g} кг")
        lines += ["","Проанализируй динамику рабочих весов, повторений, тренировочного объёма",
                  "и регулярности. Укажи тенденции и осторожные ориентиры дальнейшей прогрессии."]
        report="\n".join(lines); path=os.path.join(self.user_data_dir,"workout_report.txt")
        with open(path,"w",encoding="utf-8") as f:f.write(report)
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(report); self.msg("Отчёт сохранён и скопирован. Вставь его в нейросеть.")
        except Exception:self.msg("Отчёт сохранён в папке данных приложения:\n"+path)

if __name__=="__main__": WorkoutApp().run()
