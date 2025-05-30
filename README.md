# Price Compare

A simple web application that demonstrates price optimization in a shopping cart. The application simulates an online marketplace where users can compare prices from different sellers and optimize their cart for the best total price, taking into account shipping costs.

## Features

- Browse products from multiple sellers
- Add items to cart
- View cart contents
- Optimize cart for best total price (including shipping costs)
- Simple and clean interface

## Setup

1. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with sample data:
```bash
python populate_db.py
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to `http://localhost:5000`

## How to Use

1. Browse products on the home page
2. Add items to your cart by clicking "Add to Cart" on any offer
3. View your cart by clicking "View Cart" in the header
4. Use the "Optimize Cart" button to find the best combination of sellers for your items
5. Remove items from your cart using the "Remove" button

## Sample Data

The application comes pre-populated with sample data including:
- 5 gaming-related products
- 5 different sellers with varying shipping costs
- Multiple offers per product from different sellers 

## Opis algorytmów optymalizacji koszyka

W aplikacji dostępnych jest pięć algorytmów optymalizacji koszyka. Każdy z nich działa inaczej i ma swoje zalety oraz ograniczenia. Poniżej znajdziesz szczegółowe opisy każdego z nich:

### 1. Algorytm dokładny (Exact)
Ten algorytm sprawdza wszystkie możliwe kombinacje wyboru ofert dla produktów w koszyku. Dla każdego produktu rozważa każdą możliwą ofertę (od dowolnego sprzedawcy), a następnie dla każdej kombinacji liczy sumę: ceny produktów + koszt wysyłki od każdego sprzedawcy, od którego kupujemy przynajmniej jeden produkt. Wybiera kombinację o najniższym koszcie całkowitym. Algorytm gwarantuje znalezienie rozwiązania optymalnego, ale jest bardzo wolny dla większych koszyków (złożoność rośnie wykładniczo z liczbą produktów).

**Zalety:**
- Zawsze znajduje rozwiązanie optymalne.

**Wady:**
- Bardzo wolny przy większej liczbie produktów.

**Kiedy używać:**
- Gdy koszyk jest mały (do kilku produktów) i zależy nam na najlepszym możliwym wyniku.

---

### 2. Algorytm heurystyczny (Heuristic)
Algorytm ten działa w dwóch etapach. Najpierw dla każdego produktu wybiera najtańszą ofertę (nie patrząc na koszt wysyłki). Następnie próbuje zamieniać oferty produktów na inne (od innych sprzedawców), jeśli to obniża całkowity koszt (cena + wysyłka). W praktyce działa bardzo szybko i często daje dobre wyniki, ale nie zawsze znajduje rozwiązanie optymalne.

**Zalety:**
- Bardzo szybki, nadaje się do dużych koszyków.
- Często daje dobre wyniki.

**Wady:**
- Nie gwarantuje rozwiązania optymalnego.

**Kiedy używać:**
- Gdy koszyk jest duży i zależy nam na szybkim wyniku.

---

### 3. PRODUCT-ENUM (dokładny, produkty → sklepy)
Ten algorytm generuje wszystkie możliwe przypisania produktów do sklepów (czyli dla każdego produktu rozważa każdą możliwą ofertę). Dla każdej kombinacji liczy koszt całkowity (ceny + wysyłka od sprzedawców, od których kupujemy). Wybiera kombinację o najniższym koszcie. Jest wykonalny dla małej liczby produktów, bo złożoność rośnie wykładniczo z liczbą produktów.

**Zalety:**
- Zawsze znajduje rozwiązanie optymalne.
- Działa szybciej niż exact, jeśli liczba sklepów jest duża, a produktów mało.

**Wady:**
- Bardzo wolny przy większej liczbie produktów.

**Kiedy używać:**
- Gdy produktów jest mało, a sklepów dużo.

---

### 4. SHOP-ENUM (dokładny, sklepy → produkty)
Algorytm ten rozważa wszystkie możliwe niepuste podzbiory sklepów, które mogą pokryć wszystkie produkty z koszyka. Dla każdego podzbioru sprawdza, czy można kupić wszystkie produkty tylko w tych sklepach. Jeśli tak, przypisuje każdy produkt do najtańszej oferty w tym podzbiorze sklepów i liczy koszt całkowity (ceny + wysyłka). Wybiera najlepszą kombinację. Algorytm jest wykonalny dla małej liczby sklepów (złożoność rośnie wykładniczo z liczbą sklepów).

**Zalety:**
- Zawsze znajduje rozwiązanie optymalne.
- Działa szybciej niż exact, jeśli sklepów jest mało, a produktów dużo.

**Wady:**
- Bardzo wolny przy większej liczbie sklepów.

**Kiedy używać:**
- Gdy sklepów jest mało, a produktów dużo.

---

### 5. Algorytm zachłanny (Greedy)
Algorytm zachłanny działa bardzo szybko i w praktyce często daje dobre wyniki. Dla każdego produktu (w ustalonej kolejności) wybiera sklep, który daje najniższy koszt (cena produktu + koszt wysyłki, jeśli jeszcze nie był opłacony). Po przypisaniu produktu do sklepu, koszt wysyłki tego sklepu jest ustawiany na 0 dla kolejnych produktów (bo płacimy za wysyłkę tylko raz). Na końcu sumuje ceny produktów i koszty wysyłki użytych sklepów. Algorytm nie zawsze daje rozwiązanie optymalne, ale jest bardzo szybki i prosty.

**Zalety:**
- Bardzo szybki, nadaje się do dużych koszyków.
- Prosty w implementacji i zrozumieniu.

**Wady:**
- Nie gwarantuje rozwiązania optymalnego.
- W specyficznych przypadkach może dać wynik znacznie gorszy od optimum.

**Kiedy używać:**
- Gdy zależy nam na bardzo szybkim wyniku i akceptujemy rozwiązanie przybliżone. 