import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# Set up logging
logging.basicConfig(filename='scraping.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Set up Chrome WebDriver
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
driver = webdriver.Chrome(options=chrome_options)

# URL to scrape
url = "https://www.jiopay.in/business/help-center"

# Folder to save scraped data
output_folder = 'scraped_data'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Function to scrape the content by clicking the buttons and extracting data
def scrape_data(url):
    try:
        driver.get(url)
        logging.info(f"Started scraping: {url}")
        
        time.sleep(3)  # Allow the page to load

        all_data = []  # List to hold all scraped data
        
        # Step 1: Find and click the first button (Main Heading)
        main_buttons = driver.find_elements(By.CSS_SELECTOR, ".css-175oi2r.r-1i6wzkk.r-lrvibr.r-1loqt21.r-1otgn73")
        
        for main_button in main_buttons:
            try:
                # Ensure the main button is clickable and click it
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(main_button)
                )
                driver.execute_script("arguments[0].scrollIntoView();", main_button)
                main_button.click()
                logging.info(f"Clicked on main button: {main_button.text}")

                # Wait for main heading content to load
                time.sleep(2)

                # Step 2: Get the main heading name
                main_heading = driver.find_element(By.CSS_SELECTOR, ".css-1rynq56.r-jwli3a.r-8jdrp.r-1enofrn.r-1it3c9n.r-1xnzce8")
                main_heading_name = main_heading.text.strip()
                logging.info(f"Main heading: {main_heading_name}")
                all_data.append({"Main Heading": main_heading_name})

                # Step 3: Process second-level buttons (if they exist)
                second_buttons = driver.find_elements(By.CSS_SELECTOR, ".css-175oi2r.r-lrvibr.r-1awozwy.r-18u37iz.r-1wtj0ep.r-1loqt21.r-1otgn73")

                # Check if second-level buttons exist
                if not second_buttons:
                    logging.warning(f"No second buttons found for main heading: {main_heading_name}. Skipping to next main heading.")
                else:
                    for second_button in second_buttons:
                        try:
                            # Ensure the second button is clickable and click it
                            WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable(second_button)
                            )
                            driver.execute_script("arguments[0].scrollIntoView();", second_button)
                            second_button.click()
                            logging.info(f"Clicked on second heading: {second_button.text}")

                            # Wait for the second heading content to load
                            time.sleep(2)

                            # Step 4: Get the second heading name
                            second_heading = driver.find_element(By.CSS_SELECTOR, ".css-1rynq56.r-op4f77.r-8jdrp.r-ubezar.r-1it3c9n.r-1xnzce8")
                            second_heading_name = second_heading.text.strip()
                            logging.info(f"Second heading: {second_heading_name}")
                            all_data.append({"Second Heading": second_heading_name})

                            # Step 5: Click the second heading to reveal third-level content
                            third_content = driver.find_element(By.CSS_SELECTOR, ".css-1rynq56.r-1xt3ije.r-8jdrp.r-1b43r93.r-1it3c9n.r-rjixqe.r-1xnzce8")
                            third_content_text = third_content.text.strip()
                            logging.info(f"Third level content: {third_content_text}")
                            all_data.append({"Third Level Content": third_content_text})

                        except Exception as e:
                            logging.error(f"Error while scraping second button content: {str(e)}")
                            continue  # If error occurs, continue with the next second button
                # Move to the next main heading after scraping current one
                logging.info("Moving to the next main heading.")

            except Exception as e:
                logging.error(f"Error while scraping main button content: {str(e)}")
                continue  # Force move to next main heading if an error occurs

        return all_data
    
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None

# Scrape the data from the given URL
scraped_data = scrape_data(url)

# Save the data into a CSV file
import pandas as pd
csv_filename = os.path.join(output_folder, 'scraped_faq_data.csv')
df = pd.DataFrame(scraped_data)
df.to_csv(csv_filename, index=False)
logging.info(f"Data saved to CSV file: {csv_filename}")

# Save the data into a TXT file (optional)
txt_filename = os.path.join(output_folder, 'scraped_faq_data.txt')
with open(txt_filename, 'w', encoding='utf-8') as f:
    for entry in scraped_data:
        f.write(f"{entry}\n\n")
logging.info(f"Data saved to TXT file: {txt_filename}")

# Close the driver
driver.quit()
logging.info("Web scraping finished successfully.")
