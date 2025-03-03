from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import signal
import sys
from InquirerPy import inquirer

def error_msg():
    print('You pressed Ctrl+C!')
    exit_application()

def exit_application():
    print('Exiting the application')
    sys.exit(0)

def signal_handler(sig, frame):
    error_msg()

signal.signal(signal.SIGINT, signal_handler)

def save_data(data, columns, data_set_name, file_name):
    df = pd.DataFrame(data, columns=columns)
    file_path = f'./{file_name}-{data_set_name}.csv'
    df.to_csv(file_path, index=False)
    print(f'{data_set_name} saved as: {os.path.abspath(file_path)}')

def process_table_data(table_text):
    lines = table_text.split('\n')
    headers = lines[0].split()
    data = []
    i = 1

    while i < len(lines):
        if lines[i].strip().isdigit():
            pos = lines[i].strip()
            i += 1
            player = lines[i].strip()
            i += 1
            team = lines[i].strip()
            i += 1
            stats = lines[i].strip().split()
            
            player_info = f"{player} ({team})"
            row = [pos, player_info] + stats
            data.append(row)
            i += 1
        else:
            i += 1

    return data, headers

def get_page(driver, url, wait_condition):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(wait_condition)
        return driver.find_element(By.CSS_SELECTOR, ".st-table.statsTable").text
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def get_years(driver):
    try:
        driver.get("https://www.iplt20.com/stats/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".np-battingtable_contaner"))
        )
        containers = driver.find_elements(By.CSS_SELECTOR, ".np-battingtable_contaner")
        years = list(set([cont.get_attribute("class").split()[-1] for cont in containers]))
        years.append("all-time")
        return years
    except Exception as e:
        print(f"Error getting years: {e}")
        return []

def get_stats(driver):
    try:
        driver.get("https://www.iplt20.com/stats/")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".st-table.statsTable"))
        )
        stats = driver.find_elements(By.CSS_SELECTOR, ".st-table.statsTable")
        return [s.get_attribute("href").split("/")[-1] for s in stats], [s.text for s in stats]
    except Exception as e:
        print(f"Error getting stats: {e}")
        return [], []

def scrap_data(driver, years, stats):
    base = 'https://www.iplt20.com/stats/'
    for year in years:
        for stat in stats:
            if stat == 'team-ranking':
                url = f"{base}{year}"
                table_text = get_page(driver, url, EC.presence_of_element_located((By.CSS_SELECTOR, ".st-table.statsTable")))
            else:
                url = f"{base}{year}/{stat}"
                table_text = get_page(driver, url, EC.presence_of_element_located((By.CSS_SELECTOR, ".st-table.statsTable")))
            
            if table_text:
                data, headers = process_table_data(table_text)
                data_set_name = f"{stat.title()}-{year}" if stat != 'team-ranking' else f"Team-Ranking-{year}"
                save_data(data, headers, data_set_name, "Result")
            else:
                print(f"Data not available for {stat}-{year}")

def main():
    driver = webdriver.Chrome()
    try:
        years = get_years(driver)
        stats_url, stats_title = get_stats(driver)
        
        if not years or not stats_url:
            print("No data available")
            return
        
        selected_years = inquirer.checkbox(
            message="Select years:",
            choices=years
        ).execute()
        
        selected_stats = inquirer.checkbox(
            message="Select statistics:",
            choices=[{'name': title, 'value': url} for title, url in zip(stats_title, stats_url)]
        ).execute()
        
        scrap_data(driver, selected_years, selected_stats)
        
    finally:
        driver.quit()

if __name__ == '__main__':
    main()