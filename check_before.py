from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

def resolve_country_he(asn):
    try:
        # Set up Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # Update this path with your ChromeDriver location
        service = Service(executable_path="C:/Users/Emilia/Downloads/chromedriver-win64/chromedriver.exe")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load the ASN details page
        url = f"https://bgp.he.net/AS{asn}"
        driver.get(url)

        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//body"))
        )

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find all divs with class 'asleft' and check their text
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

# Function to save AS paths with country information to a file
def save_as_paths_to_file(as_paths, file_path):
    try:
        with open(file_path, "w") as file:
            for path in as_paths:
                file.write(f"{path}\n")
        print(f"AS paths with countries have been saved to: {file_path}")
    except Exception as e:
        print(f"Error saving AS paths to file: {e}")

# Read AS paths from the input file
def read_as_paths_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read().strip().split("\n")
    except Exception as e:
        print(f"Error reading AS paths from file: {e}")
        return []

# Main logic
input_file = "as_paths_poland_taiwan.txt"  # Path to your input file
output_file = "as_paths_with_countries_before.txt"  # Path to save the output

# Read AS paths from the input file
as_paths_input = read_as_paths_from_file(input_file)

# Function to load AS numbers from a file into a set
def load_as_set(file_path):
    try:
        with open(file_path, "r") as file:
            # Extract numeric part of AS numbers (e.g., "1234" from "as1234")
            return set(line.strip().lower().replace("as", "") for line in file if line.strip())
    except Exception as e:
        print(f"Error loading AS set from {file_path}: {e}")
        return set()

# Load AS numbers for Poland and Germany
as_pl_set = load_as_set("as_pl.txt")  # Load Poland AS numbers
as_de_set = load_as_set("as_tw.txt")  # Load Germany AS numbers

# Process each AS path
as_paths_with_countries = []
for line in as_paths_input:
    parts = line.split(": ")
    if len(parts) == 2:
        as_path = parts[1]
        as_numbers = re.findall(r'\d+', as_path)
        as_path_with_countries = []
        for asn in as_numbers:
            if asn in as_pl_set:
                as_path_with_countries.append(f"AS{asn} (Poland)")
            elif asn in as_de_set:
                as_path_with_countries.append(f"AS{asn} (Taiwan)")
            else:
                # If AS is not in Poland or Germany sets, resolve the country
                country = resolve_country_he(asn)
                as_path_with_countries.append(f"AS{asn} ({country})")
        as_paths_with_countries.append(f"{parts[0]}: {' -> '.join(as_path_with_countries)}")

# Save the AS paths with country information to the output file
save_as_paths_to_file(as_paths_with_countries, output_file)