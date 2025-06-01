from app import app, db, Product, Seller, Offer

def populate_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

        sellers = []
        seller_names = [
            "MediaMarkt",
            "RTV Euro AGD",
            "Komputronik",
            "X-Kom",
            "Morele.net",
            "Neonet",
            "Media Expert",
            "Alsen",
            "OleOle!",
            "Avans"
        ]
        import random
        for name in seller_names:
            shipping_cost = round(random.uniform(9.99, 24.99), 2)
            sellers.append(Seller(name=name, shipping_cost=shipping_cost))
        db.session.add_all(sellers)
        db.session.commit()

        products = [
            Product(name="Laptop ultrabook 14 cali", description="Lekki ultrabook z ekranem 14 cali, idealny do pracy i nauki"),
            Product(name="Laptop biznesowy Pro", description="Wytrzymały laptop biznesowy z czytnikiem linii papilarnych"),
            Product(name="Komputer stacjonarny MiniPC", description="Kompaktowy komputer stacjonarny do biura i domu"),
            Product(name="Tablet multimedialny 10 cali", description="Tablet z ekranem 10 cali, idealny do filmów i internetu"),
            Product(name="Serwer NAS 4xHDD", description="Domowy serwer plików z obsługą RAID i 4 dyskami twardymi"),
            Product(name="Pakiet biurowy Office", description="Licencja na popularny pakiet biurowy do pracy i nauki"),
            Product(name="Torba na laptopa 15,6 cala", description="Wygodna torba na laptopa z kieszenią na akcesoria"),
            Product(name="Stacja dokująca USB-C", description="Stacja dokująca do laptopa z portami USB, HDMI i Ethernet"),
            Product(name="Podstawka chłodząca pod laptopa", description="Podstawka z wentylatorami do chłodzenia laptopa"),
            Product(name="Etui na tablet 10 cali", description="Ochronne etui na tablet z funkcją podstawki"),
            Product(name="Monitor gamingowy 27 cali", description="Monitor 27 cali, 165Hz, matryca IPS, dla graczy"),
            Product(name="Konsola do gier nowej generacji", description="Konsola z obsługą 4K i szybkim dyskiem SSD"),
            Product(name="Stacjonarny komputer gamingowy", description="Komputer stacjonarny z kartą graficzną RTX i szybkim SSD"),
            Product(name="Mysz bezprzewodowa Bluetooth", description="Bezprzewodowa myszka z cichymi przyciskami i długim czasem pracy"),
            Product(name="Klawiatura bezprzewodowa slim", description="Cienka klawiatura bezprzewodowa z cichym skokiem klawiszy"),
            Product(name="Router Wi-Fi 6", description="Nowoczesny router z obsługą Wi-Fi 6 i gigabitowym Ethernetem"),
            Product(name="Kamera internetowa Full HD", description="Kamera do wideorozmów z mikrofonem i autofokusem"),
            Product(name="Głośniki komputerowe 2.1", description="Zestaw głośników z subwooferem do komputera i laptopa"),
            Product(name="Słuchawki nauszne z mikrofonem", description="Wygodne słuchawki z mikrofonem do pracy i grania"),
            Product(name="Pad do PC/Xbox", description="Kontroler bezprzewodowy kompatybilny z PC i Xbox"),
            Product(name="Karta graficzna GeForce", description="Wydajna karta graficzna do gier i pracy z grafiką"),
            Product(name="Dysk SSD NVMe 1TB", description="Szybki dysk SSD NVMe o pojemności 1TB"),
            Product(name="Zasilacz UPS 1000VA", description="Zasilacz awaryjny UPS do komputera i routera"),
            Product(name="Mikrofon USB do streamingu", description="Mikrofon do streamingu i wideokonferencji"),
            Product(name="Fotel gamingowy z podnóżkiem", description="Ergonomiczny fotel gamingowy z regulowanym podnóżkiem"),
            Product(name="Podkładka pod mysz XXL", description="Duża podkładka pod mysz i klawiaturę"),
            Product(name="Karta dźwiękowa USB", description="Zewnętrzna karta dźwiękowa USB do laptopa i PC"),
            Product(name="Hub USB 3.0 4-portowy", description="Hub USB 3.0 z czterema portami i zasilaniem"),
            Product(name="Adapter HDMI na VGA", description="Adapter do podłączenia monitora VGA do HDMI"),
            Product(name="Kabel USB-C do USB-A 1m", description="Przewód USB-C do USB-A o długości 1 metr"),
            Product(name="Czytnik kart pamięci SD/microSD", description="Uniwersalny czytnik kart pamięci do laptopa i PC"),
            Product(name="Stacja dokująca do smartfona", description="Stacja dokująca z ładowaniem bezprzewodowym do smartfona"),
            Product(name="Tablet graficzny z piórkiem", description="Tablet graficzny do rysowania i projektowania"),
            Product(name="Switch sieciowy 8-portowy", description="Przełącznik sieciowy 8x Gigabit Ethernet"),
            Product(name="Powerbank 20000mAh", description="Powerbank do ładowania laptopa, tabletu i smartfona"),
            Product(name="Karta podarunkowa do sklepu", description="Karta podarunkowa do wykorzystania w sklepie komputerowym"),
            Product(name="Gogle VR do PC", description="Gogle wirtualnej rzeczywistości do komputera"),
            Product(name="Stacja robocza CAD", description="Wydajna stacja robocza do projektowania CAD"),
            Product(name="Serwer rack 1U", description="Serwer rack 1U do zastosowań biznesowych"),
            Product(name="Torba na laptopa gamingowego", description="Torba na laptopa 17 cali z dodatkowym miejscem na akcesoria"),
            Product(name="Etui na laptopa 13 cali", description="Ochronne etui na laptopa 13 cali"),
            Product(name="Tablet edukacyjny dla dzieci", description="Tablet z aplikacjami edukacyjnymi dla dzieci"),
            Product(name="Laptop 2w1 z dotykiem", description="Laptop z ekranem dotykowym, obracany o 360 stopni"),
            Product(name="Stacja dokująca Thunderbolt", description="Stacja dokująca z Thunderbolt 4 i szybkim ładowaniem"),
            Product(name="Podstawka pod monitor z USB", description="Podstawka pod monitor z portami USB i organizerem"),
            Product(name="Konsola retro z grami", description="Konsola retro z wgranymi klasycznymi grami"),
            Product(name="Laptop gamingowy RTX", description="Laptop gamingowy z kartą RTX i szybkim ekranem"),
            Product(name="Tablet graficzny LCD", description="Tablet graficzny z wyświetlaczem LCD do rysowania"),
            Product(name="Kamera sportowa 4K", description="Kamera sportowa z nagrywaniem 4K i Wi-Fi"),
            Product(name="Głośnik Bluetooth wodoodporny", description="Przenośny głośnik Bluetooth odporny na zachlapania"),
            Product(name="Smartwatch z pulsometrem", description="Smartwatch z pomiarem tętna i powiadomieniami"),
            Product(name="Stacja ładowania USB 6-portowa", description="Stacja ładowania USB do 6 urządzeń jednocześnie")
        ]
        db.session.add_all(products)
        db.session.commit()

        import random
        offers = []
        for product in products:
            base_price = random.uniform(25, 300)
            seller_ids = random.sample(range(1, 11), k=random.randint(3, 7))
            for seller_id in seller_ids:
                price = round(base_price * random.uniform(0.85, 1.15), 2)
                offers.append(Offer(product_id=product.id, seller_id=seller_id, price=price))
        db.session.add_all(offers)
        db.session.commit()

if __name__ == '__main__':
    populate_database() 