from dataclasses import dataclass


@dataclass(frozen=True)
class Service:
    id: str
    name: str
    duration_minutes: int
    price: int
    emoji: str


SERVICES: list[Service] = [
    Service(id="manicure_classic",  name="Маникюр классический",            duration_minutes=60,  price=1200, emoji="💅"),
    Service(id="manicure_gel",      name="Маникюр с покрытием гель-лак",    duration_minutes=90,  price=1800, emoji="✨"),
    Service(id="gel_removal",       name="Снятие гель-лака",                duration_minutes=30,  price=400,  emoji="🧴"),
    Service(id="gel_removal_new",   name="Снятие + новое покрытие гель-лак",duration_minutes=90,  price=1900, emoji="🔄"),
    Service(id="manicure_hardware", name="Аппаратный маникюр",              duration_minutes=60,  price=1500, emoji="🔧"),
    Service(id="manicure_men",      name="Мужской маникюр",                 duration_minutes=45,  price=1000, emoji="🙌"),
    Service(id="pedicure_classic",  name="Педикюр классический",            duration_minutes=90,  price=1800, emoji="🦶"),
    Service(id="pedicure_gel",      name="Педикюр с покрытием гель-лак",    duration_minutes=120, price=2500, emoji="🌸"),
    Service(id="manicure_french",   name="Французский маникюр",             duration_minutes=75,  price=2000, emoji="🤍"),
    Service(id="nail_extension",    name="Наращивание ногтей",              duration_minutes=180, price=3500, emoji="💎"),
]

SERVICES_BY_ID: dict[str, Service] = {s.id: s for s in SERVICES}

PAYMENT_METHODS: list[tuple[str, str]] = [
    ("cash",     "💵 Наличные"),
    ("card",     "💳 Карта (терминал)"),
    ("transfer", "📲 Перевод на карту"),
]

PAYMENT_LABELS: dict[str, str] = {key: label for key, label in PAYMENT_METHODS}
