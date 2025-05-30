from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

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
    # --- Algorytm zachłanny (Greedy) ---
    # 1. Ustal kolejność produktów (np. wg malejącej rekomendowanej ceny lub po prostu tak jak w koszyku).
    # 2. Dla każdego produktu wybierz sklep, który daje najniższy koszt (cena produktu + koszt wysyłki, jeśli jeszcze nie był użyty).
    # 3. Po przypisaniu produktu do sklepu, koszt wysyłki tego sklepu ustaw na 0 dla kolejnych produktów (bo płacimy za wysyłkę tylko raz).
    # 4. Powtarzaj dla wszystkich produktów.
    # 5. Na końcu sumuj ceny produktów i koszty wysyłki użytych sklepów.
    # Algorytm bardzo szybki, daje dobre wyniki w praktyce, ale nie zawsze optymalne.
    def greedy():
        ordered_pids = product_ids.copy()
        shipping_paid = {sid: False for sid in sellers}
        chosen_offers = []
        total_shipping = 0
        for pid in ordered_pids:
            best_offer = None
            best_cost = None
            for offer in product_offers[pid]:
                shipping = 0 if shipping_paid[offer.seller_id] else sellers[offer.seller_id].shipping_cost
                cost = offer.price + shipping
                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_offer = offer
            chosen_offers.append(best_offer)
            if not shipping_paid[best_offer.seller_id]:
                total_shipping += sellers[best_offer.seller_id].shipping_cost
                shipping_paid[best_offer.seller_id] = True
        return chosen_offers

    old_total = 0
    for item in cart_items:
        offer = Offer.query.get(item['offer_id'])
        if offer:
            old_total += offer.price + sellers[offer.seller_id].shipping_cost
    best_combination = greedy()
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
    changes = []
    for i, offer in enumerate(best_combination):
        old_offer = Offer.query.get(cart_items[i]['offer_id'])
        if old_offer.id != offer.id:
            changes.append(f"{offer.product.name}: {old_offer.seller.name} → {offer.seller.name} ({old_offer.price:.2f} zł → {offer.price:.2f} zł)")
    if changes:
        message = f"Koszyk zoptymalizowany! Zaoszczędzono {old_total - new_total:.2f} zł. Zmiany: " + "; ".join(changes)
    else:
        message = "Koszyk już jest zoptymalizowany pod względem ceny!"
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