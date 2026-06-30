import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================================================
# PART 1: HELPER FUNCTIONS
# ============================================================================

def estimate_playing_style(ppg_str, goals_str, assists_str):
    """
    Estimates playing style based on stats.
    
    Logic:
    - High PPG + more assists = Playmaker
    - High PPG + more goals = Scorer
    - Low PPG = Grinder
    - Balanced = Two-Way
    """
    try:
        # Extract numeric values
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
    
    CapWages shows salaries like "$17,000,000"
    We want to convert to "17M"
    """
    if not salary_str or salary_str == "N/A":
        return "N/A"
    
    try:
        # Remove $ and commas, convert to number
        salary_num = float(salary_str.replace("$", "").replace(",", ""))
        # Convert to millions format
        return f"${salary_num/1000000:.1f}M"
    except:
        return salary_str


# ============================================================================
# PART 2: SCRAPE WITH SELENIUM
# ============================================================================

def scrape_capwages_with_selenium():
    """
    Scrapes all pages of CapWages using Selenium.
    
    Selenium opens a real browser, waits for content to load,
    then extracts the player data.
    
    Returns:
        list: List of all player dictionaries
    """
    all_players = []
    
    # Initialize Chrome driver
    # If chromedriver is in your trade-fit-matrix folder, use the path
    # Otherwise, just use 'chromedriver' if it's in your PATH
    try:
        driver = webdriver.Chrome('./chromedriver')  # Or just webdriver.Chrome()
    except:
        print("Could not find chromedriver. Make sure it's installed.")
        return all_players
    
    try:
        # Loop through all pages
        for page_num in range(1, 24):
            url = f"https://capwages.com/players/active?page={page_num}"
            
            print(f"Scraping page {page_num}/23...")
            
            # Navigate to the page
            driver.get(url)
            
            # Wait for the table to load (wait up to 10 seconds)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
                )
            except:
                print(f"  Timeout waiting for page {page_num}")
                continue
            
            # Wait a bit more for data to fully render
            time.sleep(2)
            
            # Find all table rows
            rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            print(f"  Found {len(rows)} rows on page {page_num}")
            
            # Extract player data from each row
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 9:
                        continue
                    
                    # Extract data from cells
                    # Cell 0: Player name
                    name_elem = cells[0].find_elements(By.TAG_NAME, "a")
                    if name_elem:
                        name = name_elem[0].text.strip()
                    else:
                        name = cells[0].text.strip()
                    
                    # Skip if name is empty
                    if not name:
                        continue
                    
                    # Extract other cells
                    team = cells[1].text.strip() if len(cells) > 1 else "N/A"
                    position = cells[2].text.strip() if len(cells) > 2 else "N/A"
                    age = cells[3].text.strip() if len(cells) > 3 else "N/A"
                    goals = cells[4].text.strip() if len(cells) > 4 else "N/A"
                    assists = cells[5].text.strip() if len(cells) > 5 else "N/A"
                    points = cells[6].text.strip() if len(cells) > 6 else "N/A"
                    ppg = cells[7].text.strip() if len(cells) > 7 else "N/A"
                    cap_hit = cells[8].text.strip() if len(cells) > 8 else "N/A"
                    
                    # Estimate playing style
                    playing_style = estimate_playing_style(str(ppg), goals, assists)
                    
                    # Clean up salary
                    salary_clean = parse_salary(cap_hit)
                    
                    # Create player dictionary
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
            
            # Be nice to the website - wait between pages
            time.sleep(1)
        
        print(f"\nTotal scraped: {len(all_players)} players")
        return all_players
    
    finally:
        # Always close the browser
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
    
    # Scrape CapWages with Selenium
    players = scrape_capwages_with_selenium()
    
    # Save to CSV
    if players:
        save_to_csv(players, "data/players.csv")
        print("=" * 60)
        print(f"Success! {len(players)} players saved.")
        print("=" * 60)
    else:
        print("=" * 60)
        print("No players scraped. Check the website or chromedriver.")
        print("=" * 60)