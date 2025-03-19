import requests
from bs4 import BeautifulSoup

# Adres URL strony
url_pl = "https://bgp.he.net/country/PL"

# Wysyłanie żądania HTTP
response = requests.get(url_pl)

# Sprawdzenie, czy żądanie zakończyło się sukcesem
if response.status_code != 200:
    print("Nie udało się pobrać strony.")
    exit()

# Parsowanie HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Znajdowanie tabeli z danymi AS
table = soup.find('table', id='asns')

# Przygotowanie listy do przechowywania wyników
as_list = []

# Przechodzenie przez wiersze tabeli
for row in table.find_all('tr')[1:]:  # Pomijamy nagłówek tabeli
    columns = row.find_all('td')
    
    # Pobieranie numeru AS i liczby tras IPv4
    as_number = columns[0].text.strip()
    ipv4_routes = int(columns[3].text.strip().replace(',', ''))  # Usuwamy przecinki i konwertujemy na int
    
    # Filtrowanie AS, gdzie liczba tras IPv4 > 200
    if ipv4_routes > 300:
        as_list.append(as_number)

# Zapisanie wyników do pliku txt
with open("as_pl.txt", "w") as file:
    for as_number in as_list:
        file.write(f"{as_number}\n")

print(f"Znaleziono {len(as_list)} AS i zapisano do pliku as_pl.txt.")

# Adres URL strony
url_tw = "https://bgp.he.net/country/TW"

# Wysyłanie żądania HTTP
response = requests.get(url_tw)

# Sprawdzenie, czy żądanie zakończyło się sukcesem
if response.status_code != 200:
    print("Nie udało się pobrać strony.")
    exit()

# Parsowanie HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Znajdowanie tabeli z danymi AS
table = soup.find('table', id='asns')

# Przygotowanie listy do przechowywania wyników
as_list = []

# Przechodzenie przez wiersze tabeli
for row in table.find_all('tr')[1:]:  # Pomijamy nagłówek tabeli
    columns = row.find_all('td')
    
    # Pobieranie numeru AS i liczby tras IPv4
    as_number = columns[0].text.strip()
    ipv4_routes = int(columns[3].text.strip().replace(',', ''))  # Usuwamy przecinki i konwertujemy na int
    
    # Filtrowanie AS, gdzie liczba tras IPv4 > 200
    if ipv4_routes > 300:
        as_list.append(as_number)

# Zapisanie wyników do pliku txt
with open("as_tw.txt", "w") as file:
    for as_number in as_list:
        file.write(f"{as_number}\n")

print(f"Znaleziono {len(as_list)} AS i zapisano do pliku as_tw.txt.")