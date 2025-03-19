import requests
import subprocess
import re
import platform
from ipaddress import ip_network
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# Funkcja do ekstrakcji prefiksów IP ze strony CIDR-Report
def get_prefixes_from_cidr_report(asn):
    url = f"https://www.cidr-report.org/cgi-bin/as-report?as=AS{asn}&view=2.0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    print(f"Status Code for AS{asn}: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: Failed to fetch data for AS{asn}")
        return None
    soup = BeautifulSoup(response.text, 'html.parser')
    prefixes = []
    for pre_tag in soup.find_all("pre"):
        for a_tag in pre_tag.find_all("a", class_=["black", "red", "green"]):
            prefix = a_tag.get_text().strip()
            if prefix and "/" in prefix:
                prefixes.append(prefix)
    return prefixes

# Funkcja do odczytu listy AS z pliku
def read_as_list(file_path):
    try:
        with open(file_path, "r") as file:
            return [line.strip().replace("AS", "") for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []

# Funkcja do wykonania traceroute (kompatybilna z Windows)
def perform_traceroute(ip, max_hops=30):
    try:
        # Użycie "tracert" dla Windows
        if platform.system() == "Windows":
            result = subprocess.run(["tracert", "-h", str(max_hops), ip], capture_output=True, text=True)
        else:  # Użycie "traceroute" dla Unix/Linux
            result = subprocess.run(["traceroute", "-m", str(max_hops), ip], capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        print(f"Error performing traceroute for {ip}: {e}")
        return None

# Funkcja do rozpoznania AS dla danego IP
def resolve_as(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            return data.get("org", "").split()[0].replace("AS", "")
    except Exception as e:
        print(f"Error resolving AS for {ip}: {e}")
    return None

# Funkcja do pobrania pierwszego IP hosta z zakresu CIDR
def get_first_host_ip_from_cidr(cidr):
    try:
        network = ip_network(cidr, strict=False)
        if network.num_addresses > 2:
            return str(network.network_address + 1)
        else:
            return str(network.network_address)
    except ValueError:
        print(f"Invalid CIDR range: {cidr}")
        return None
    
def save_as_paths_to_file(as_paths, file_path):
    try:
        with open(file_path, "w") as file:
            for path in as_paths:
                file.write(f"{path}\n")
        print(f"Ścieżki AS i kraje zostały zapisane do pliku: {file_path}")
    except Exception as e:
        print(f"Error saving AS paths to file: {e}")

poland_as_list = read_as_list("as_pl.txt")
taiwan_as_list = read_as_list("as_tw.txt")

if not poland_as_list:
    print("Error: No ASNs found for Poland.")
    exit()
if not taiwan_as_list:
    print("Error: No ASNs found for taiwan.")
    exit()

target_ips = []
for asn in taiwan_as_list:
    prefixes = get_prefixes_from_cidr_report(asn)
    if prefixes:
        first_ip = get_first_host_ip_from_cidr(prefixes[0])
        if first_ip:
            target_ips.append(first_ip)
    else:
        print(f"No IP prefixes found for AS{asn}.")

if not target_ips:
    print("Error: No valid IPs found for taiwan ASes.")
    exit()

def resolve_country_he(asn):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        service = Service(executable_path=".../chromedriver.exe") # Update this path with your ChromeDriver location
        driver = webdriver.Chrome(service=service, options=chrome_options)

        url = f"https://bgp.he.net/AS{asn}"
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//body"))
        )

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Wszystkie divs z klasą 'asleft'
        asleft_divs = soup.find_all("div", class_="asleft")
        for div in asleft_divs:
            if "Country of Origin" in div.text:
                country_info_div = div.find_next_sibling("div", class_="asright")
                if country_info_div and country_info_div.find("a"):
                    country_name = country_info_div.find("a").text.strip()
                    driver.quit()
                    return country_name

        driver.quit()
        return "Unknown"

    except Exception as e:
        print(f"Error extracting country of origin for AS{asn}: {e}")
        if 'driver' in locals():
            driver.quit()
        return "Unknown"


# Funkcja do zapisywania ścieżek AS i krajów do pliku
def save_as_paths_to_file(as_paths, file_path):
    try:
        with open(file_path, "w") as file:
            for path in as_paths:
                file.write(f"{path}\n")
        print(f"Ścieżki AS i kraje zostały zapisane do pliku: {file_path}")
    except Exception as e:
        print(f"Error saving AS paths to file: {e}")

# Wykonanie traceroute i sprawdzenie AS dla każdego IP
as_paths = []
for ip in target_ips:
    print(f"\nTracing route to {ip}:")
    traceroute_output = perform_traceroute(ip, max_hops=30)
    if traceroute_output:
        print(traceroute_output)
        ips_in_path = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", traceroute_output)
        path_asns = []
        for hop_ip in ips_in_path:
            asn = resolve_as(hop_ip)
            if asn:
                if asn in poland_as_list:
                    path_asns.append(f"AS{asn} (Poland)")
                elif asn in taiwan_as_list:
                    path_asns.append(f"AS{asn} (taiwan)")
                else:
                    # Sprawdzenie kraj za pomocą Hurricane Electric BGP Toolkit
                    country = resolve_country_he(asn)
                    path_asns.append(f"AS{asn} ({country})")
        as_paths.append(f"{ip}: {' -> '.join(path_asns)}")

save_as_paths_to_file(as_paths, "as_paths_with_countries_he.txt")