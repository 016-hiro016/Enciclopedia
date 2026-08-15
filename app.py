import os
from datetime import datetime, timezone
from urllib.parse import quote_plus

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

load_dotenv()
db = SQLAlchemy()
migrate = Migrate()

CATEGORIES = [
    ("imperium", "ИМПЕРИУМ", "Порядок, вера и военная мощь Человечества", "aquila.png"),
    ("chaos", "ХАОС", "Враги Трона и сущности Варпа", "chaos.png"),
    ("xenos", "КСЕНОСЫ", "Нечеловеческие цивилизации и угрозы", None),
    ("weapons", "ВООРУЖЕНИЕ", "Орудия войны и уничтожения", None),
    ("technology", "ТЕХНОЛОГИИ", "Археотех, машинные духи и запретные знания", None),
    ("history", "ИСТОРИЯ", "Великие события от Эпохи Раздора до 41-го тысячелетия", None),
    ("persons", "ИЗВЕСТНЫЕ ЛИЧНОСТИ", "Лица, оставившие след в анналах", None),
    ("archive", "АРХИВ", "Несортированные и засекреченные записи", None),
]

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    icon = db.Column(db.String(120))
    entries = db.relationship("Entry", backref="category", lazy=True, cascade="all, delete-orphan")

class Entry(db.Model):
    __tablename__ = "entries"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False, index=True)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False, default="")
    body = db.Column(db.Text, nullable=False, default="")
    subcategory = db.Column(db.String(160), nullable=False, default="")
    tags = db.Column(db.String(500), nullable=False, default="")
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False, index=True)

def seed_database():
    if Category.query.count():
        return
    categories = {}
    for slug, name, description, icon in CATEGORIES:
        categories[slug] = Category(slug=slug, name=name, description=description, icon=icon)
        db.session.add(categories[slug])
    db.session.flush()
    demo = [
        ("imperium", "Адептус Астартес", "Генетически улучшенные воины Империума", "Фракции Империума", "Сверхчеловеческие воины, созданные для защиты человечества.", "астартес,космодесант,империум"),
        ("imperium", "Адептус Механикус", "Жрецы Марса, хранители древних машинных знаний", "Фракции Империума", "Культ Машины чтит Омниссию и поддерживает древние технологии посредством ритуалов и литаний.", "механикус,марс,омниссия"),
        ("imperium", "Инквизиция", "Тайная власть, охраняющая человечество", "Ордо", "Инквизиторы обладают огромными полномочиями в борьбе с ересями, демонами и ксеносами.", "инквизиция,ересь,ордо"),
        ("chaos", "Четыре Великих Бога Хаоса", "Кхорн, Тзинч, Нургл и Слаанеш", "Боги Хаоса", "Четыре могущественных божества Варпа воплощают разные аспекты разрушительной психической энергии.", "хаос,варп,боги"),
        ("xenos", "Эльдары", "Древняя психически развитая раса", "Расы", "Эльдары пережили падение своей империи и теперь странствуют между мирами.", "эльдары,аэльдари,ксенос"),
        ("xenos", "Орки", "Воинственная ксенораса, существующая ради войны", "Расы", "Орки — биологически и психически необычные создания, для которых война естественна.", "орки,ксенос"),
        ("weapons", "Болтер", "Стандартное оружие космодесанта", "Стрелковое оружие", "Болтер использует реактивные боеприпасы для поражения брони и живой силы.", "болтер,оружие"),
        ("technology", "Машинный дух", "Почитаемая совокупность логики и древней технологии", "Механикус", "Сложные устройства требуют уважения, обслуживания и ритуала.", "машинный дух,технологии"),
        ("history", "Великий Раскол", "Катастрофическое разделение галактики", "Миллениум", "Великий Разлом изменил навигацию, связь и военную географию Империума.", "история,великий разлом"),
        ("persons", "Робаут Жиллиман", "Примарх Ультрамаринов", "Примархи", "Один из примархов, вернувшихся в эпоху после Великого Разлома.", "жилиман,примарх"),
        ("archive", "Омниссийский протокол 001", "Запись о состоянии каталога", "Архивные записи", "Пустой слот для будущих материалов архива. Добавляйте записи через PostgreSQL.", "архив,протокол"),
    ]
    for cat, title, desc, sub, body, tags in demo:
        db.session.add(Entry(title=title, slug=f"{cat}-{len(title)}-{len(tags)}", description=desc, body=body, subcategory=sub, tags=tags, category_id=categories[cat].id))
    db.session.commit()

def create_app():
    app = Flask(__name__)
    database_url = os.getenv("DATABASE_URL", "sqlite:///enciclopedia.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    app.config.update(SQLALCHEMY_DATABASE_URI=database_url, SQLALCHEMY_TRACK_MODIFICATIONS=False, SECRET_KEY=os.getenv("SECRET_KEY", "omnisiah-secret"))
    db.init_app(app)
    migrate.init_app(app, db)
    with app.app_context():
        db.create_all()
        seed_database()

    @app.get("/")
    def index():
        return render_template("index.html", categories=Category.query.order_by(Category.id).all())

    @app.get("/api/category/<slug>")
    def category(slug):
        cat = Category.query.filter_by(slug=slug).first_or_404()
        groups = {}
        for item in cat.entries:
            groups.setdefault(item.subcategory or "Архив", []).append({"id": item.id, "title": item.title, "description": item.description})
        return jsonify({"name": cat.name, "description": cat.description, "groups": groups})

    @app.get("/api/entry/<int:entry_id>")
    def entry(entry_id):
        item = db.get_or_404(Entry, entry_id)
        return jsonify({"id": item.id, "title": item.title, "description": item.description, "body": item.body, "subcategory": item.subcategory, "category": item.category.name, "tags": item.tags.split(",") if item.tags else []})

    @app.get("/api/search")
    def search():
        q = request.args.get("q", "").strip()
        if not q:
            return jsonify({"query": "", "results": []})
        p = f"%{q}%"
        items = Entry.query.join(Category).filter(or_(Entry.title.ilike(p), Entry.description.ilike(p), Entry.body.ilike(p), Entry.tags.ilike(p), Category.name.ilike(p))).limit(80).all()
        return jsonify({"query": q, "results": [{"id": x.id, "title": x.title, "description": x.description, "category": x.category.name, "subcategory": x.subcategory} for x in items]})

    @app.get("/network-search")
    def network_search():
        q = request.args.get("q", "").strip()
        return redirect(f"https://www.google.com/search?q={quote_plus(q + ' Warhammer 40,000')}") if q else redirect("/")

    @app.get("/api/system")
    def system_status():
        now = datetime.now(timezone.utc)
        return jsonify({"time": now.strftime("%H:%M:%S"), "date": now.strftime("%d.%m.%Y"), "imperial_year": 0, "load": 37 + now.second % 11, "temperature": 64 + now.second % 4})
    return app

app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
