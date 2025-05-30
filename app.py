from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

# Database Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    offers = db.relationship('Offer', backref='product', lazy=True)

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    shipping_cost = db.Column(db.Float, nullable=False)
    offers = db.relationship('Offer', backref='seller', lazy=True)

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

def get_cart_info():
    cart_items = session.get('cart', [])
    cart_count = len(cart_items)
    cart_total = 0
    for item in cart_items:
        offer = Offer.query.get(item['offer_id'])
        if offer:
            cart_total += offer.price + offer.seller.shipping_cost
    return cart_count, cart_total

@app.context_processor
def inject_cart_info():
    cart_count, cart_total = get_cart_info()
    return dict(cart_count=cart_count, cart_total=cart_total)

@app.route('/', methods=['GET'])
def index():
    sort = request.args.get('sort', 'name_asc')
    filter_name = request.args.get('filter_name', '')
    filter_min_price = request.args.get('filter_min_price', '')
    filter_max_price = request.args.get('filter_max_price', '')
    algo = request.args.get('algo', session.get('algo', 'exact'))
    session['algo'] = algo
    products = Product.query
    if filter_name:
        products = products.filter(Product.name.ilike(f'%{filter_name}%'))
    products = products.all()
    offers = []
    for product in products:
        for offer in product.offers:
            offers.append({
                'product': product,
                'offer': offer,
                'seller': offer.seller
            })
    if filter_min_price:
        offers = [o for o in offers if o['offer'].price >= float(filter_min_price)]
    if filter_max_price:
        offers = [o for o in offers if o['offer'].price <= float(filter_max_price)]
    if sort == 'name_asc':
        offers.sort(key=lambda x: x['product'].name.lower())
    elif sort == 'name_desc':
        offers.sort(key=lambda x: x['product'].name.lower(), reverse=True)
    elif sort == 'price_asc':
        offers.sort(key=lambda x: x['offer'].price)
    elif sort == 'price_desc':
        offers.sort(key=lambda x: x['offer'].price, reverse=True)
    # Count products and offers in cart
    cart_items = session.get('cart', [])
    cart_product_counts = {}
    cart_offer_counts = {}
    for item in cart_items:
        pid = item['product_id']
        cart_product_counts[pid] = cart_product_counts.get(pid, 0) + 1
        oid = item['offer_id']
        cart_offer_counts[oid] = cart_offer_counts.get(oid, 0) + 1
    return render_template('index.html', offers=offers, sort=sort, filter_name=filter_name, filter_min_price=filter_min_price, filter_max_price=filter_max_price, algo=algo, cart_product_counts=cart_product_counts, cart_offer_counts=cart_offer_counts)

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    items = []
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        offer = Offer.query.get(item['offer_id'])
        items.append({
            'product': product,
            'offer': offer,
            'seller': offer.seller
        })
    # Group by seller and keep global index
    seller_map = {}
    global_index = 0
    for item in items:
        sid = item['seller'].id
        if sid not in seller_map:
            seller_map[sid] = {'seller': item['seller'], 'items': []}
        item_with_index = dict(item)
        item_with_index['global_index'] = global_index
        seller_map[sid]['items'].append(item_with_index)
        global_index += 1
    # Sort sellers alphabetically by name
    sorted_seller_map = dict(sorted(seller_map.items(), key=lambda x: x[1]['seller'].name.lower()))
    message = session.pop('cart_message', None)
    return render_template('cart.html', seller_map=sorted_seller_map, message=message)

@app.route('/add_to_cart/<int:offer_id>')
def add_to_cart(offer_id):
    if 'cart' not in session:
        session['cart'] = []
    cart = session['cart']
    cart.append({
        'product_id': Offer.query.get(offer_id).product_id,
        'offer_id': offer_id
    })
    session['cart'] = cart
    # preserve filter/sort/algo settings
    args = request.args.to_dict()
    return redirect(url_for('index', **args))

@app.route('/remove_from_cart/<int:index>')
def remove_from_cart(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
        session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/optimize', methods=['POST'])
def optimize():
    # Pobierz wybrany algorytm z formularza lub sesji
    algo = request.form.get('algo', session.get('algo', 'exact'))
    session['algo'] = algo
    cart_items = session.get('cart', [])
    if not cart_items:
        return redirect(url_for('cart'))
    product_ids = [item['product_id'] for item in cart_items]
    offers = Offer.query.filter(Offer.product_id.in_(product_ids)).all()
    product_offers = {}
    for offer in offers:
        if offer.product_id not in product_offers:
            product_offers[offer.product_id] = []
        product_offers[offer.product_id].append(offer)
    # Wczytaj wszystkich sprzedawców do pamięci, aby zminimalizować zapytania do bazy
    sellers = {s.id: s for s in Seller.query.all()}
    # --- Algorytm dokładny (brute force, PRODUCT-ENUM z permutacją) ---
    # Przegląda wszystkie możliwe kombinacje ofert dla produktów w koszyku.
    # Dla każdego produktu wybiera jedną z dostępnych ofert (od dowolnego sprzedawcy).
    # Dla każdej kombinacji liczy sumę: ceny produktów + koszt wysyłki od każdego sprzedawcy, od którego kupujemy przynajmniej jeden produkt.
    # Zwraca kombinację o najniższym koszcie całkowitym.
    def exact():
        best_combination = []
        best_total = float('inf')
        def calculate_total(combination):
            # Grupowanie produktów wg sprzedawcy
            seller_items = {}
            for offer in combination:
                if offer.seller_id not in seller_items:
                    seller_items[offer.seller_id] = []
                seller_items[offer.seller_id].append(offer)
            total = 0
            # Dodajemy koszt wysyłki i ceny produktów dla każdego sprzedawcy
            for seller_id, items in seller_items.items():
                seller = sellers[seller_id]
                total += seller.shipping_cost
                total += sum(item.price for item in items)
            return total
        def find_best_combination(current_combination, remaining_products):
            nonlocal best_combination, best_total
            if not remaining_products:
                total = calculate_total(current_combination)
                if total < best_total:
                    best_total = total
                    best_combination = current_combination.copy()
                return
            product_id = remaining_products[0]
            # Rekurencyjnie próbujemy każdą ofertę dla bieżącego produktu
            for offer in product_offers[product_id]:
                current_combination.append(offer)
                find_best_combination(current_combination, remaining_products[1:])
                current_combination.pop()
        find_best_combination([], product_ids)
        return best_combination

    # --- Algorytm heurystyczny (DP-inspired) ---
    # 1. Najpierw przypisuje każdemu produktowi najtańszą ofertę (nie patrząc na wysyłkę).
    # 2. Następnie iteracyjnie próbuje zamieniać oferty produktów na inne (od innych sprzedawców),
    #    jeśli to obniża całkowity koszt (cena + wysyłka). Działa szybko, ale nie zawsze daje optymalne rozwiązanie.
    def heuristic():
        chosen = []
        # Krok 1: wybierz najtańszą ofertę dla każdego produktu
        for pid in product_ids:
            cheapest = min(product_offers[pid], key=lambda o: o.price)
            chosen.append(cheapest)
        # Krok 2: próbuj zamieniać oferty, by zoptymalizować koszt wysyłki
        for _ in range(2):  # Dwie iteracje lokalnej optymalizacji
            for i, pid in enumerate(product_ids):
                best_offer = chosen[i]
                best_total = None
                for offer in product_offers[pid]:
                    temp = chosen.copy()
                    temp[i] = offer
                    # Liczymy koszt dla tej zamiany
                    seller_items = {}
                    for off in temp:
                        if off.seller_id not in seller_items:
                            seller_items[off.seller_id] = []
                        seller_items[off.seller_id].append(off)
                    total = 0
                    for seller_id, items in seller_items.items():
                        seller = sellers[seller_id]
                        total += seller.shipping_cost
                        total += sum(item.price for item in items)
                    if best_total is None or total < best_total:
                        best_total = total
                        best_offer = offer
                chosen[i] = best_offer
        return chosen

    # --- Algorytm PRODUCT-ENUM (dokładny, produkty → sklepy) ---
    # 1. Dla każdego produktu generuje listę wszystkich możliwych ofert (od różnych sprzedawców).
    # 2. Przegląda wszystkie możliwe kombinacje wyboru ofert (każdy produkt -> jedna oferta).
    # 3. Dla każdej kombinacji liczy koszt całkowity (ceny + wysyłka od sprzedawców, od których kupujemy).
    # 4. Zwraca kombinację o najniższym koszcie.
    # Algorytm jest wykonalny dla małej liczby produktów (bo złożoność rośnie wykładniczo z liczbą produktów).
    def product_enum():
        from itertools import product
        offer_lists = [product_offers[pid] for pid in product_ids]
        best_combination = None
        best_total = float('inf')
        # Przeglądaj wszystkie możliwe kombinacje ofert (każdy produkt -> jedna oferta)
        for combination in product(*offer_lists):
            # Upewnij się, że dla każdego produktu wybrano dokładnie jedną ofertę
            if len(combination) != len(product_ids):
                continue
            # Grupowanie produktów wg sprzedawcy
            seller_items = {}
            for offer in combination:
                if offer.seller_id not in seller_items:
                    seller_items[offer.seller_id] = []
                seller_items[offer.seller_id].append(offer)
            total = 0
            # Dodajemy koszt wysyłki i ceny produktów dla każdego sprzedawcy
            for seller_id, items in seller_items.items():
                seller = sellers[seller_id]
                total += seller.shipping_cost
                total += sum(item.price for item in items)
            if total < best_total:
                best_total = total
                best_combination = combination
        return list(best_combination) if best_combination else []

    # --- Algorytm SHOP-ENUM (dokładny, sklepy → produkty) ---
    # 1. Zbiera wszystkie sklepy, które mają jakiekolwiek produkty z koszyka.
    # 2. Przegląda wszystkie możliwe niepuste podzbiory tych sklepów.
    # 3. Dla każdego podzbioru sprawdza, czy można kupić wszystkie produkty tylko w tych sklepach.
    #    Jeśli tak, przypisuje każdy produkt do najtańszej oferty w tym podzbiorze sklepów.
    # 4. Liczy koszt całkowity (ceny + wysyłka od wybranych sklepów).
    # 5. Zwraca najlepszą kombinację (o najniższym koszcie).
    # Algorytm jest wykonalny dla małej liczby sklepów (bo złożoność rośnie wykładniczo z liczbą sklepów).
    def shop_enum():
        from itertools import combinations, chain
        # Zbierz wszystkie sklepy, które mają jakiekolwiek produkty z koszyka
        all_seller_ids = set()
        for offers in product_offers.values():
            for offer in offers:
                all_seller_ids.add(offer.seller_id)
        all_seller_ids = list(all_seller_ids)
        n_sellers = len(all_seller_ids)
        best_combination = None
        best_total = float('inf')
        # Rozważ wszystkie niepuste podzbiory sklepów
        for r in range(1, n_sellers + 1):
            for seller_subset in combinations(all_seller_ids, r):
                # Sprawdź, czy ten podzbiór sklepów pokrywa wszystkie produkty
                chosen_offers = []
                valid = True
                for pid in product_ids:
                    # Wybierz najtańszą ofertę dla produktu wśród wybranych sklepów
                    offers_in_subset = [o for o in product_offers[pid] if o.seller_id in seller_subset]
                    if not offers_in_subset:
                        valid = False
                        break
                    cheapest = min(offers_in_subset, key=lambda o: o.price)
                    chosen_offers.append(cheapest)
                if not valid:
                    continue
                # Grupowanie produktów wg sprzedawcy
                seller_items = {}
                for offer in chosen_offers:
                    if offer.seller_id not in seller_items:
                        seller_items[offer.seller_id] = []
                    seller_items[offer.seller_id].append(offer)
                total = 0
                # Dodajemy koszt wysyłki i ceny produktów dla każdego sprzedawcy
                for seller_id, items in seller_items.items():
                    seller = sellers[seller_id]
                    total += seller.shipping_cost
                    total += sum(item.price for item in items)
                if total < best_total:
                    best_total = total
                    best_combination = chosen_offers.copy()
        return best_combination if best_combination else []

    # --- Algorytm zachłanny (Greedy) ---
    # 1. Ustal kolejność produktów (np. wg malejącej rekomendowanej ceny lub po prostu tak jak w koszyku).
    # 2. Dla każdego produktu wybierz sklep, który daje najniższy koszt (cena produktu + koszt wysyłki, jeśli jeszcze nie był użyty).
    # 3. Po przypisaniu produktu do sklepu, koszt wysyłki tego sklepu ustaw na 0 dla kolejnych produktów (bo płacimy za wysyłkę tylko raz).
    # 4. Powtarzaj dla wszystkich produktów.
    # 5. Na końcu sumuj ceny produktów i koszty wysyłki użytych sklepów.
    # Algorytm bardzo szybki, daje dobre wyniki w praktyce, ale nie zawsze optymalne.
    def greedy():
        # Krok 1: Ustal kolejność produktów (tu: tak jak w koszyku)
        ordered_pids = product_ids.copy()
        # Można też sortować po rekomendowanej cenie, jeśli taka jest dostępna
        # Krok 2: Inicjalizacja struktur pomocniczych
        used_sellers = set()  # Sklepy, dla których już zapłaciliśmy wysyłkę
        shipping_paid = {sid: False for sid in sellers}  # Czy wysyłka już opłacona
        chosen_offers = []  # Wybrane oferty (po jednej dla każdego produktu)
        total_shipping = 0  # Suma kosztów wysyłki
        # Krok 3: Dla każdego produktu wybierz najlepszy sklep
        for pid in ordered_pids:
            best_offer = None
            best_cost = None
            # Przeglądamy wszystkie oferty dla danego produktu
            for offer in product_offers[pid]:
                # Jeśli wysyłka dla tego sklepu już była opłacona, to koszt wysyłki = 0
                shipping = 0 if shipping_paid[offer.seller_id] else sellers[offer.seller_id].shipping_cost
                cost = offer.price + shipping
                # Wybieramy ofertę o najniższym koszcie (cena + ewentualna wysyłka)
                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_offer = offer
            # Dodaj wybraną ofertę do wyniku
            chosen_offers.append(best_offer)
            # Jeśli to pierwsza rzecz z tego sklepu, dolicz koszt wysyłki i oznacz, że już zapłacono
            if not shipping_paid[best_offer.seller_id]:
                total_shipping += sellers[best_offer.seller_id].shipping_cost
                shipping_paid[best_offer.seller_id] = True
        # Krok 4: Suma cen produktów + suma kosztów wysyłki
        # (dla spójności z innymi algorytmami, zwracamy tylko listę ofert)
        return chosen_offers

    # Oblicz stary koszt
    old_total = 0
    for item in cart_items:
        offer = Offer.query.get(item['offer_id'])
        if offer:
            old_total += offer.price + sellers[offer.seller_id].shipping_cost
    # Uruchom wybrany algorytm
    if algo == 'heuristic':
        best_combination = heuristic()
    elif algo == 'product_enum':
        best_combination = product_enum()
    elif algo == 'shop_enum':
        best_combination = shop_enum()
    elif algo == 'greedy':
        best_combination = greedy()
    else:
        best_combination = exact()
    # Funkcja pomocnicza do obliczania kosztu
    def calculate_total(combination):
        seller_items = {}
        for offer in combination:
            if offer.seller_id not in seller_items:
                seller_items[offer.seller_id] = []
            seller_items[offer.seller_id].append(offer)
        total = 0
        for seller_id, items in seller_items.items():
            seller = sellers[seller_id]
            total += seller.shipping_cost
            total += sum(item.price for item in items)
        return total
    new_total = calculate_total(best_combination)
    # Znajdź co się zmieniło
    changes = []
    for i, offer in enumerate(best_combination):
        old_offer = Offer.query.get(cart_items[i]['offer_id'])
        if old_offer.id != offer.id:
            changes.append(f"{offer.product.name}: {old_offer.seller.name} → {offer.seller.name} ({old_offer.price:.2f} zł → {offer.price:.2f} zł)")
    if changes:
        message = f"Koszyk zoptymalizowany! Zaoszczędzono {old_total - new_total:.2f} zł. Zmiany: " + "; ".join(changes)
    else:
        message = "Koszyk już jest zoptymalizowany pod względem ceny!"
    # Zaktualizuj koszyk
    optimized_cart = []
    for offer in best_combination:
        optimized_cart.append({
            'product_id': offer.product_id,
            'offer_id': offer.id
        })
    session['cart'] = optimized_cart
    session['cart_message'] = message
    return redirect(url_for('cart'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session['cart'] = []
    session['cart_message'] = 'Koszyk został wyczyszczony.'
    return redirect(url_for('cart'))

if __name__ == '__main__':
    app.run(debug=True) 