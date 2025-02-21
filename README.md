# conference-crawler

## Overview

`conference-crawler` is a Python project designed to scrape conference event data from the Researchr website, filter the events based on user-defined criteria, and upload the filtered events to a Google Calendar. The project is automated using GitHub Actions to run daily and update the calendar with the latest conference events.

## Features

- Scrapes conference event data from the Researchr website.
- Filters events based on user-defined criteria in `filter_config.json`.
- Uploads filtered events to a Google Calendar.
- Automated daily updates using GitHub Actions.
- Automated notifies when there are new conferences in the calendar or new items in the filter.

## Prerequisites

- Python 3.12
- Google Cloud service account with access to Google Calendar API.
- GitHub repository with GitHub Actions enabled.

## Usage

### **1. Fork this repository**

### **2. Enable Google Calendar API**
1. Visit the [Google Calendar API page](https://console.cloud.google.com/marketplace/product/google/calendar-json.googleapis.com?q=search&referrer=search&inv=1&invt=AbpKbg&authuser=1) and enable the API, and click manage.
2. Navigate to the **Credentials** section.
3. Create a **Service Account** (fill in *Service account ID* then *Done*).
4. At the **Service Accounts** tab, click in the newly created email. Visit the **Keys** tab, then **Add key**, **Create new key**. Select **JSON** option and create.
5. The process will automatically download the key which will have a format like this:

    ```json
    {
        "type": "service_account",
        "project_id": "<PROJECT_ID>",
        "private_key_id": "<PRIVATE_KEY_ID>",
        "private_key": "-----BEGIN PRIVATE KEY-----\n<PRIVATE_KEY>\n-----END PRIVATE KEY-----\n",
        "client_email": "<CLIENT_EMAIL>",
        "client_id": "<CLIENT_ID>",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/<CLIENT_EMAIL>",
        "universe_domain": "googleapis.com"
    }
    ```

5. Visit **Settings > Secrets and variables > Actions** of the repository on GitHub then create a **New repository secret** with:
    - *Name*: **SERVICE_CLIENT**
    - *Secret*: the content of the downloaded JSON file.

### **3. Configure Google Calendar**
1. Open [Google Calendar](https://calendar.google.com).
2. Create a **new calendar**.
3. Retrieve the **Calendar ID** from the newly created calendar's setting. Update the `CALENDAR_ID` in `utils.py` with your **Calendar ID**
   - Example **Calendar ID**:
     ```
     c1c3cc42b9be97acffa4fb3bcb785cd4f57aa914fbbdf8698b349c429ebf17c3@group.calendar.google.com
     ```
5. Also at the your calendar's setting, grant necessary permissions:
    - Visit **Share with specific people or groups** tab.
    - Add **<CLIENT_EMAIL>** (from the .json file in step 2) and grant **"Make changes to events"** permission.

### **4. Update GitHub Workflow Configuration**
1. Modify `.github/workflows/main.yml`:
    - Update the **user name** and **user email** to match your GitHub account.
2. Ensure **Read and write permissions** are enabled:
    - Go to **Settings > Actions > General** in your GitHub repository.
    - Set **Workflow permissions** to **Read and write permissions**.

### **5. Update `filter.json` (Optional)**

The `filter.json` file allows you to customize event filtering based on specific criteria.

1. Open the `filter.json` file in the project directory.
2. Modify the filtering parameters as needed, such as event types, excluded keywords, or time ranges.
3. Save the changes.

This step is optional, but it helps refine the events that get added to the `.ics` file and Google Calendar.


### **6. Test the Setup**
To verify everything is set up correctly:
1. Navigate to the **Actions** tab in your GitHub repository.
2. Manually trigger a **Daily Runs** workflow.
3. After execution, check:
    - A `.ics` file should be generated in the `results` folder.
    - Events should be added to your Google Calendar.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

