# Algorytmy optymalizacji koszyka - wyjaśnienia po polsku

# Algorytm dokładny (brute force):
# Sprawdza wszystkie możliwe kombinacje wyboru ofert dla produktów.
# Dla każdego produktu rozważa każdą możliwą ofertę (od dowolnego sprzedawcy).
# Dla każdej kombinacji liczy sumę: ceny produktów + koszt wysyłki od każdego sprzedawcy, od którego kupujemy przynajmniej jeden produkt.
# Wybiera kombinację o najniższym koszcie całkowitym.
def exact(product_ids, product_offers, sellers):
    """Algorytm dokładny: sprawdza wszystkie możliwe kombinacje ofert i wybiera najtańszą."""
    best_combination = []
    best_total = float('inf')
    def calculate_total(combination):
        # Grupujemy produkty wg sprzedawcy, żeby policzyć koszt wysyłki tylko raz dla każdego sklepu
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
        # Jeśli nie zostały już żadne produkty do przypisania, liczymy koszt tej kombinacji
        if not remaining_products:
            total = calculate_total(current_combination)
            if total < best_total:
                best_total = total
                best_combination = current_combination.copy()
            return
        product_id = remaining_products[0]
        # Dla bieżącego produktu próbujemy każdą możliwą ofertę
        for offer in product_offers[product_id]:
            current_combination.append(offer)
            find_best_combination(current_combination, remaining_products[1:])
            current_combination.pop()
    # Startujemy z pustą kombinacją i wszystkimi produktami do przypisania
    find_best_combination([], product_ids)
    return best_combination

# Algorytm heurystyczny:
# Najpierw dla każdego produktu wybiera najtańszą ofertę (nie patrząc na koszt wysyłki).
# Następnie próbuje zamieniać oferty produktów na inne (od innych sprzedawców),
# jeśli to obniża całkowity koszt (cena + wysyłka). Działa szybko, ale nie zawsze daje optymalne rozwiązanie.
def heuristic(product_ids, product_offers, sellers):
    """Algorytm heurystyczny: najpierw najtańsze oferty, potem lokalne poprawki."""
    chosen = []
    # Krok 1: wybierz najtańszą ofertę dla każdego produktu
    for pid in product_ids:
        cheapest = min(product_offers[pid], key=lambda o: o.price)
        chosen.append(cheapest)
    # Krok 2: próbuj zamieniać oferty, by zoptymalizować koszt wysyłki
    for _ in range(2):
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

# Algorytm PRODUCT-ENUM:
# Generuje wszystkie możliwe przypisania produktów do sklepów (czyli dla każdego produktu rozważa każdą możliwą ofertę).
# Dla każdej kombinacji liczy koszt całkowity (ceny + wysyłka od sprzedawców, od których kupujemy).
# Wybiera kombinację o najniższym koszcie. Jest wykonalny dla małej liczby produktów.
def product_enum(product_ids, product_offers, sellers):
    """Algorytm PRODUCT-ENUM: generuje wszystkie możliwe przypisania produktów do sklepów."""
    from itertools import product
    offer_lists = [product_offers[pid] for pid in product_ids]
    best_combination = None
    best_total = float('inf')
    # Przeglądamy wszystkie możliwe kombinacje ofert (każdy produkt -> jedna oferta)
    for combination in product(*offer_lists):
        if len(combination) != len(product_ids):
            continue
        # Grupujemy produkty wg sprzedawcy
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

# Algorytm SHOP-ENUM:
# Rozważa wszystkie możliwe niepuste podzbiory sklepów, które mogą pokryć wszystkie produkty z koszyka.
# Dla każdego podzbioru sprawdza, czy można kupić wszystkie produkty tylko w tych sklepach.
# Jeśli tak, przypisuje każdy produkt do najtańszej oferty w tym podzbiorze sklepów i liczy koszt całkowity (ceny + wysyłka).
# Wybiera najlepszą kombinację. Algorytm jest wykonalny dla małej liczby sklepów.
def shop_enum(product_ids, product_offers, sellers):
    """Algorytm SHOP-ENUM: rozważa wszystkie podzbiory sklepów i przypisuje produkty do najtańszych ofert w tych sklepach."""
    from itertools import combinations
    all_seller_ids = set()
    # Zbieramy wszystkie sklepy, które mają jakiekolwiek produkty z koszyka
    for offers in product_offers.values():
        for offer in offers:
            all_seller_ids.add(offer.seller_id)
    all_seller_ids = list(all_seller_ids)
    n_sellers = len(all_seller_ids)
    best_combination = None
    best_total = float('inf')
    # Rozważamy wszystkie niepuste podzbiory sklepów
    for r in range(1, n_sellers + 1):
        for seller_subset in combinations(all_seller_ids, r):
            chosen_offers = []
            valid = True
            # Sprawdzamy, czy ten podzbiór sklepów pokrywa wszystkie produkty
            for pid in product_ids:
                offers_in_subset = [o for o in product_offers[pid] if o.seller_id in seller_subset]
                if not offers_in_subset:
                    valid = False
                    break
                cheapest = min(offers_in_subset, key=lambda o: o.price)
                chosen_offers.append(cheapest)
            if not valid:
                continue
            # Grupujemy produkty wg sprzedawcy
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