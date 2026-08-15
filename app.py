import os
from datetime import datetime, timezone
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, render_template_string, request, session, url_for
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text

load_dotenv()
db=SQLAlchemy(); migrate=Migrate()
CATEGORIES=[("imperium","ИМПЕРИУМ","Порядок, вера и военная мощь Человечества","aquila.png"),("chaos","ХАОС","Враги Трона и сущности Варпа","chaos.png"),("xenos","КСЕНОСЫ","Нечеловеческие цивилизации и угрозы",None),("weapons","ВООРУЖЕНИЕ","Орудия войны и уничтожения",None),("technology","ТЕХНОЛОГИИ","Археотех, машинные духи и запретные знания",None),("history","ИСТОРИЯ","Великие события от Эпохи Раздора до 41-го тысячелетия",None),("persons","ИЗВЕСТНЫЕ ЛИЧНОСТИ","Лица, оставившие след в анналах",None),("archive","АРХИВ","Несортированные и засекреченные записи",None)]
STATUS=["ЖИВ","МЕРТВ","НЕИЗВЕСТНО"]
LOYALTY=["ИМПЕРИУМ","ХАОС","КСЕНОСЫ","НЕИЗВЕСТНО","НЕЗАВИСИМЫЙ"]
AFFILIATIONS=["Не указано","Ультрамарины","Имперские Кулаки","Кровавые Ангелы","Чёрные Храмовники","Гвардия Ворона","Саламандры","Железные Руки","Космические Волки","Тёмные Ангелы","Гвардия Смерти","Тысяча Сынов","Дети Императора","Пожиратели Миров","Чёрный Легион","Серые Рыцари","Ордо Еретикус","Ордо Ксенос","Ордо Маллеус","Адептус Механикус"]
class Category(db.Model):
    __tablename__="categories"; id=db.Column(db.Integer,primary_key=True); slug=db.Column(db.String(80),unique=True,nullable=False,index=True); name=db.Column(db.String(120),nullable=False); description=db.Column(db.Text,default="",nullable=False); icon=db.Column(db.String(120)); entries=db.relationship("Entry",back_populates="category",lazy=True,cascade="all, delete-orphan")
class Entry(db.Model):
    __tablename__="entries"; id=db.Column(db.Integer,primary_key=True); title=db.Column(db.String(180),nullable=False,index=True); slug=db.Column(db.String(200),nullable=False,unique=True); description=db.Column(db.Text,default="",nullable=False); body=db.Column(db.Text,default="",nullable=False); subcategory=db.Column(db.String(160),default="",nullable=False); tags=db.Column(db.String(500),default="",nullable=False); category_id=db.Column(db.Integer,db.ForeignKey("categories.id",ondelete="CASCADE"),nullable=False,index=True); status=db.Column(db.String(30),default="НЕИЗВЕСТНО",nullable=False); loyalty=db.Column(db.String(50),default="НЕИЗВЕСТНО",nullable=False); homeworld=db.Column(db.String(160),default="",nullable=False); affiliation=db.Column(db.String(160),default="",nullable=False); category=db.relationship("Category",back_populates="entries")
def seed_database():
    if Category.query.count(): return
    cats={}
    for slug,name,description,icon in CATEGORIES: cats[slug]=Category(slug=slug,name=name,description=description,icon=icon); db.session.add(cats[slug])
    db.session.flush(); demo=[("imperium","Адептус Астартес","Генетически улучшенные воины Империума","Фракции Империума","Сверхчеловеческие воины, созданные для защиты человечества.","астартес,космодесант,империум"),("imperium","Адептус Механикус","Жрецы Марса, хранители древних машинных знаний","Фракции Империума","Культ Машины чтит Омниссию и поддерживает древние технологии.","механикус,марс,омниссия"),("imperium","Инквизиция","Тайная власть, охраняющая человечество","Ордо","Инквизиторы обладают огромными полномочиями.","инквизиция,ересь,ордо"),("chaos","Четыре Великих Бога Хаоса","Кхорн, Тзинч, Нургл и Слаанеш","Боги Хаоса","Четыре могущественных божества Варпа.","хаос,варп,боги"),("xenos","Эльдары","Древняя психически развитая раса","Расы","Эльдары пережили падение своей империи.","эльдары,аэльдари,ксенос"),("xenos","Орки","Воинственная ксенораса","Расы","Орки существуют ради войны.","орки,ксенос"),("weapons","Болтер","Стандартное оружие космодесанта","Стрелковое оружие","Болтер использует реактивные боеприпасы.","болтер,оружие"),("technology","Машинный дух","Почитаемая совокупность логики и древней технологии","Механикус","Сложные устройства требуют уважения и ритуала.","машинный дух,технологии"),("history","Великий Раскол","Катастрофическое разделение галактики","Миллениум","Великий Разлом изменил Империум.","история,великий разлом"),("persons","Робаут Жиллиман","Примарх Ультрамаринов","Примархи","Один из примархов.","жилиман,примарх"),("archive","Омниссийский протокол 001","Запись о состоянии каталога","Архивные записи","Пустой слот для будущих материалов.","архив,протокол")]
    for cat,title,desc,sub,body,tags in demo: db.session.add(Entry(title=title,slug=f"{cat}-{len(title)}-{len(tags)}",description=desc,body=body,subcategory=sub,tags=tags,category_id=cats[cat].id,status="НЕИЗВЕСТНО",loyalty="НЕИЗВЕСТНО",homeworld="Не указано",affiliation="Не указано"))
    db.session.commit()
def create_app():
    app=Flask(__name__); url=os.getenv("DATABASE_URL","sqlite:///enciclopedia.db")
    if url.startswith("postgres://"): url=url.replace("postgres://","postgresql+psycopg2://",1)
    elif url.startswith("postgresql://"): url=url.replace("postgresql://","postgresql+psycopg2://",1)
    app.config.update(SQLALCHEMY_DATABASE_URI=url,SQLALCHEMY_TRACK_MODIFICATIONS=False,SECRET_KEY=os.getenv("SECRET_KEY","omnisiah-secret")); db.init_app(app); migrate.init_app(app,db)
    with app.app_context():
        db.create_all(); seed_database();
        # Existing installations get the new personnel fields without destroying their archive.
        if db.engine.url.get_backend_name()=="sqlite":
            cols={r[1] for r in db.session.execute(text("PRAGMA table_info(entries)"))}
            for name,typ,default in [("status","VARCHAR(30)","'НЕИЗВЕСТНО'"),("loyalty","VARCHAR(50)","'НЕИЗВЕСТНО'"),("homeworld","VARCHAR(160)","''"),("affiliation","VARCHAR(160)","''")]:
                if name not in cols: db.session.execute(text(f"ALTER TABLE entries ADD COLUMN {name} {typ} NOT NULL DEFAULT {default}"))
            db.session.commit()
    @app.get("/")
    def index(): return render_template("index.html",categories=Category.query.order_by(Category.id).all())
    @app.get("/api/category/<slug>")
    def category(slug):
        cat=Category.query.filter_by(slug=slug).first_or_404(); groups={}
        for x in cat.entries: groups.setdefault(x.subcategory or "Архив",[]).append({"id":x.id,"title":x.title,"description":x.description})
        return jsonify(name=cat.name,description=cat.description,groups=groups)
    @app.get("/api/entry/<int:entry_id>")
    def entry(entry_id):
        x=db.get_or_404(Entry,entry_id); return jsonify(id=x.id,title=x.title,description=x.description,body=x.body,subcategory=x.subcategory,category=x.category.name,tags=x.tags.split(",") if x.tags else [],status=x.status,loyalty=x.loyalty,homeworld=x.homeworld,affiliation=x.affiliation)
    @app.get("/api/search")
    def search():
        q=request.args.get("q","").strip()
        if not q:return jsonify(query="",results=[])
        p=f"%{q}%"; items=Entry.query.join(Category).filter(or_(Entry.title.ilike(p),Entry.description.ilike(p),Entry.body.ilike(p),Entry.tags.ilike(p),Category.name.ilike(p),Entry.homeworld.ilike(p),Entry.affiliation.ilike(p))).limit(80).all(); return jsonify(query=q,results=[{"id":x.id,"title":x.title,"description":x.description,"category":x.category.name,"subcategory":x.subcategory} for x in items])
    @app.get("/api/system")
    def system_status(): now=datetime.now(timezone.utc); return jsonify(time=now.strftime("%H:%M:%S"),date=now.strftime("%d.%m.%Y"),imperial_year=999,load=37,temperature=64)
    def admin_required(f):
        @wraps(f)
        def w(*a,**kw): return f(*a,**kw) if session.get("admin") else redirect(url_for("admin_login",next=request.path))
        return w
    ADMIN_CSS="body{background:#010201;color:#b9d8c1;font:14px monospace;margin:0;padding:30px}.admin{max-width:1180px;margin:auto;position:relative}.admin h1{color:#39ff72;letter-spacing:4px}.admin h2{color:#8cff9e;letter-spacing:2px}.admin a{color:#39ff72}.admin .box{border:1px solid #28643a;background:#030805;padding:22px;margin:16px 0;box-shadow:0 0 25px #000,inset 0 0 25px rgba(57,255,114,.03)}.admin input,.admin textarea,.admin select{display:block;width:100%;box-sizing:border-box;background:#010302;border:1px solid #174a29;color:#caffd4;padding:11px;margin:7px 0 14px}.admin textarea{min-height:150px}.admin button{background:#06120a;color:#caffd4;border:1px solid #39ff72;padding:11px 18px;cursor:pointer}.admin-grid{display:grid;grid-template-columns:1.35fr .85fr;gap:16px}.admin-aquila{width:100px;height:70px;object-fit:contain;filter:grayscale(1) brightness(1.8);mix-blend-mode:screen}.person-meta{border-top:1px solid #164529;margin-top:18px;padding-top:16px}.status-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.status-grid label{color:#477052;font-size:10px;letter-spacing:2px}.danger{border-color:#a33!important;color:#ff8888!important}.entry-row{border:1px solid #164529;padding:12px;margin:10px 0}.access{position:absolute;right:0;top:0;border:1px solid #39ff72;padding:10px 16px;color:#39ff72;box-shadow:0 0 18px rgba(57,255,114,.12);letter-spacing:2px}@media(max-width:800px){.admin-grid{grid-template-columns:1fr}.access{position:static;margin-bottom:20px}}
    @app.route("/admin/login",methods=["GET","POST"])
    def admin_login():
        if request.method=="POST" and request.form.get("password")==os.getenv("ADMIN_PASSWORD","change-me"): session["admin"]=True; return redirect(request.args.get("next") or url_for("admin_dashboard"))
        return render_template_string('<style>{{css}}</style><main class="admin box"><img class="admin-aquila" src="/static/img/aquila.png"><p>+++ ADEPTUS MECHANICUS // MAGOS ACCESS +++</p><h1>ДОСТУП К АРХИВУ</h1>{% if request.method=="POST" %}<p>+++ КЛЮЧ ОТКЛОНЁН +++</p>{% endif %}<form method="post"><input name="password" type="password" autofocus placeholder="СЕКРЕТНЫЙ КЛЮЧ"><button>☩ ВОЙТИ В КОГИТОР ☩</button></form><p><a href="/">← терминал</a></p></main>',css=ADMIN_CSS)
    @app.get("/admin/logout")
    def admin_logout(): session.pop("admin",None); return redirect(url_for("index"))
    @app.get("/admin")
    @admin_required
    def admin_dashboard():
        cats=Category.query.order_by(Category.id).all(); entries=Entry.query.order_by(Entry.id.desc()).all()
        return render_template_string('<style>{{css}}</style><main class="admin"><div class="access">ДОПУСК: <b>OMEGA-PRIME</b></div><img class="admin-aquila" src="/static/img/aquila.png"><p>+++ MAGOS ADMIN // ARCHIVUM +++</p><h1>ТЕРМИНАЛ УПРАВЛЕНИЯ</h1><p><a href="/">ТЕРМИНАЛ</a> · <a href="/admin/logout">ЗАВЕРШИТЬ СЕАНС</a></p><div class="admin-grid"><div class="box"><h2>ЗАПИСЬ В АРХИВ</h2><form method="post" action="/admin/entry/save"><label>Название записи</label><input name="title" required><label>Slug</label><input name="slug"><label>Сектор</label><select name="category_id">{% for c in cats %}<option value="{{c.id}}">{{c.name}}</option>{% endfor %}</select><label>Подкатегория / тип</label><input name="subcategory"><label>Краткое описание</label><textarea name="description"></textarea><label>Полный текст записи</label><textarea name="body"></textarea><label>Теги через запятую</label><input name="tags"><div class="person-meta"><h2>ЛИЧНОСТЬ // ПОЛЯ ДОСЬЕ</h2><div class="status-grid"><div><label>СТАТУС</label><select name="status">{% for x in statuses %}<option>{{x}}</option>{% endfor %}</select></div><div><label>ЛОЯЛЬНОСТЬ</label><select name="loyalty">{% for x in loyalties %}<option>{{x}}</option>{% endfor %}</select></div></div><label>РОДНОЙ МИР</label><input name="homeworld" placeholder="Напр. Макрагг"><label>ЛЕГИОН / ОРДЕН / ФРАКЦИЯ</label><select name="affiliation">{% for x in affiliations %}<option>{{x}}</option>{% endfor %}</select></div><button>☩ ЗАПЕЧАТАТЬ В АРХИВ ☩</button></form></div><div class="box"><h2>ПОСЛЕДНИЕ ЗАПИСИ</h2>{% for x in entries %}<div class="entry-row"><b>{{x.title}}</b><br><small>{{x.category.name}} // {{x.subcategory}}</small>{% if x.category.slug=="persons" %}<br><small>{{x.status}} · {{x.loyalty}} · {{x.homeworld}} · {{x.affiliation}}</small>{% endif %}<form method="post" action="/admin/entry/delete/{{x.id}}"><button class="danger">УДАЛИТЬ</button></form></div>{% else %}<p>АРХИВ ПУСТ.</p>{% endfor %}</div></div></main>',css=ADMIN_CSS,cats=cats,entries=entries,statuses=STATUS,loyalties=LOYALTY,affiliations=AFFILIATIONS)
    @app.post("/admin/entry/save")
    @admin_required
    def admin_save():
        eid=request.form.get("id"); x=db.get_or_404(Entry,int(eid)) if eid else Entry(); title=request.form.get("title","").strip(); cat=db.get_or_404(Category,int(request.form.get("category_id"))); x.title=title;x.slug=request.form.get("slug","").strip() or title.lower().replace(" ","-");x.description=request.form.get("description","");x.body=request.form.get("body","");x.subcategory=request.form.get("subcategory","");x.tags=request.form.get("tags","");x.category_id=cat.id;x.status=request.form.get("status","НЕИЗВЕСТНО");x.loyalty=request.form.get("loyalty","НЕИЗВЕСТНО");x.homeworld=request.form.get("homeworld","");x.affiliation=request.form.get("affiliation","");
        if not eid: db.session.add(x)
        db.session.commit(); return redirect(url_for("admin_dashboard"))
    @app.post("/admin/entry/delete/<int:entry_id>")
    @admin_required
    def admin_delete(entry_id): db.session.delete(db.get_or_404(Entry,entry_id));db.session.commit();return redirect(url_for("admin_dashboard"))
    return app
app=create_app()
if __name__=="__main__": app.run(debug=True)
