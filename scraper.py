import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# ============================================================================
# PART 1: HELPER FUNCTIONS
# ============================================================================

def estimate_playing_style(ppg_str, goals_str, assists_str):
    """
    Estimates playing style based on stats.
    """
    try:
        ppg = float(ppg_str.replace(",", "")) if ppg_str and ppg_str != "N/A" else 0
        goals = float(goals_str.replace(",", "")) if goals_str and goals_str != "N/A" else 0
        assists = float(assists_str.replace(",", "")) if assists_str and assists_str != "N/A" else 0
        
        if ppg < 0.3:
            return "Grinder"
        elif ppg > 1.0:
            if assists > goals:
                return "Playmaker"
            else:
                return "Scorer"
        elif assists > goals:
            return "Playmaker"
        elif goals > assists:
            return "Scorer"
        else:
            return "Two-Way"
    except:
        return "Two-Way"


def parse_salary(salary_str):
    """
    Cleans up salary string from CapWages.
    """
    if not salary_str or salary_str == "N/A":
        return "N/A"
    
    try:
        salary_num = float(salary_str.replace("$", "").replace(",", ""))
        return f"${salary_num/1000000:.1f}M"
    except:
        return salary_str


# ============================================================================
# PART 2: SCRAPE WITH SELENIUM
# ============================================================================

def scrape_capwages_with_selenium():
    """
    Scrapes all pages of CapWages using Selenium with webdriver-manager.
    """
    all_players = []
    
    # webdriver-manager automatically downloads and manages chromedriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    
    try:
        for page_num in range(1, 24):
            url = f"https://capwages.com/players/active?page={page_num}"
            
            print(f"Scraping page {page_num}/23...")
            
            driver.get(url)
            
            # Wait for table to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
                )
            except:
                print(f"  Timeout waiting for page {page_num}")
                continue
            
            time.sleep(2)
            
            # Find all table rows
            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            print(f"  Found {len(rows)} rows on page {page_num}")
            
            # Extract player data
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 9:
                        continue
                    
                    # Extract data
                    name_elem = cells[0].find_elements(By.TAG_NAME, "a")
                    if name_elem:
                        name = name_elem[0].text.strip()
                    else:
                        name = cells[0].text.strip()
                    
                    if not name:
                        continue
                    
                    team = cells[1].text.strip() if len(cells) > 1 else "N/A"
                    position = cells[2].text.strip() if len(cells) > 2 else "N/A"
                    age = cells[3].text.strip() if len(cells) > 3 else "N/A"
                    goals = cells[4].text.strip() if len(cells) > 4 else "N/A"
                    assists = cells[5].text.strip() if len(cells) > 5 else "N/A"
                    points = cells[6].text.strip() if len(cells) > 6 else "N/A"
                    ppg = cells[7].text.strip() if len(cells) > 7 else "N/A"
                    cap_hit = cells[8].text.strip() if len(cells) > 8 else "N/A"
                    
                    playing_style = estimate_playing_style(str(ppg), goals, assists)
                    salary_clean = parse_salary(cap_hit)
                    
                    player = {
                        "Name": name,
                        "Position": position,
                        "Team": team,
                        "Age": age,
                        "Salary": salary_clean,
                        "PPG_Last2": ppg if ppg != "N/A" else points,
                        "Goals_Last2": goals,
                        "Assists_Last2": assists,
                        "Playing_Style": playing_style
                    }
                    
                    all_players.append(player)
                    
                except Exception as e:
                    continue
            
            print(f"  Total players so far: {len(all_players)}")
            time.sleep(1)
        
        print(f"\nTotal scraped: {len(all_players)} players")
        return all_players
    
    finally:
        driver.quit()


# ============================================================================
# PART 3: SAVE TO CSV
# ============================================================================

def save_to_csv(players, filename="data/players.csv"):
    """
    Saves player list to CSV file.
    """
    if not players:
        print("No players to save!")
        return
    
    fieldnames = [
        "Name", "Position", "Team", "Age", "Salary",
        "PPG_Last2", "Goals_Last2", "Assists_Last2", "Playing_Style"
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for player in players:
                writer.writerow(player)
        
        print(f"✓ Saved {len(players)} players to {filename}")
        
    except Exception as e:
        print(f"Error saving to CSV: {e}")


# ============================================================================
# PART 4: MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("NHL Player Scraper (CapWages with Selenium)")
    print("=" * 60)
    
    players = scrape_capwages_with_selenium()
    
    if players:
        save_to_csv(players, "data/players.csv")
        print("=" * 60)
        print(f"Success! {len(players)} players saved.")
        print("=" * 60)
    else:
        print("=" * 60)
        print("No players scraped.")
        print("=" * 60)