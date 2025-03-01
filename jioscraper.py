import time
import logging
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO)

# Set up Chrome WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run in headless mode (optional)
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)

# Open the website
url = "https://www.jiopay.in/business/help-center"  # Change if needed
driver.get(url)

output_folder = 'scraped_data'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Wait for the page to load
wait = WebDriverWait(driver, 10)

# Get all clickable questions
question_selector = ".css-175oi2r.r-lrvibr.r-1awozwy"  # Selector for questions
questions = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, question_selector)))

faq_data = []

# Loop through each question and click it
for index in range(len(questions)):
    try:
        # Re-fetch the questions list (since elements might refresh after clicking)
        questions = driver.find_elements(By.CSS_SELECTOR, question_selector)

        # Scroll to the question
        driver.execute_script("arguments[0].scrollIntoView();", questions[index])
        time.sleep(1)  # Delay for smooth execution

        # Extract question text
        question_text = questions[index].text

        # Click to expand the answer
        questions[index].click()
        time.sleep(2)  # Allow answer to load

        # Locate the expanded answer **inside the same parent div**
        parent_div = questions[index].find_element(By.XPATH, "./ancestor::div[contains(@class, 'r-14lw9ot')]")
        answer = parent_div.find_element(By.XPATH, ".//div[contains(@class, 'css-1rynq56 r-1xt3ije r-8jdrp')]")

        # Store the question and answer
        faq_data.append({"Question": question_text, "Answer": answer.text})

        # Click again to collapse (optional, depends on site behavior)
        questions[index].click()
        time.sleep(1)

    except Exception as e:
        logging.warning(f"Skipping a question due to an error: {str(e)}")

# Save data to CSV
csv_filename = os.path.join(output_folder, "scraped_faq_data.csv")
df = pd.DataFrame(faq_data)
df.to_csv(csv_filename, index=False)
logging.info(f"Data saved to CSV file: {csv_filename}")

# Save the data into a TXT file (line by line)
txt_filename = os.path.join(output_folder, 'scraped_faq_data.txt')
with open(txt_filename, 'w', encoding='utf-8') as f:
    for index, row in df.iterrows():
        question = row['Question']
        answer = row['Answer']
        # Write each question and answer on a new line
        f.write(f"Question: {question}\nAnswer: {answer}\n\n")
logging.info(f"Data saved to TXT file: {txt_filename}")


# Close the browser
driver.quit()
