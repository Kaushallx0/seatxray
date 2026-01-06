# SeatXray Setup Guide

To use SeatXray, you need to acquire and configure an Amadeus API Key. Please follow the steps below.

## 1. Create an Amadeus Developers Account

1. Access [Amadeus for Developers](https://developers.amadeus.com/).
2. Proceed to the "Self-Service APIs" sign-up page and create an account.

## 2. Register Your App and Get Keys

1. After logging in, open the [My Apps](https://developers.amadeus.com/my-apps) page to view your registered applications.
2. Click "Create New App", enter a recognizable app name (e.g., `MySeatXray`), and save.
3. Navigate to the app details page and copy the API Key and API Secret from 'App Keys'.
If you want access to all data, click **"Get production environment"** to perform an upgrade.

### Steps to Request Production Environment

To obtain production keys, you need to complete the procedure by entering the following information.
1. Enter your billing information (Personal & Billing info)
2. Register a payment method
3. Review the Terms of Service and agree to them to conclude the contract

> When moving to the production environment, you need to sign an agreement and register payment information, but you will not be charged as long as you stay within the free usage limits.

If you are asked `Does your app use an API that requires validation?` during the application process, please select **"No"**.
SeatXray only performs searches and displays seat maps; it does not use booking functions or other features that require additional validation, so your keys will be issued immediately.

4. After completing the procedure, copy the `API Key` and `API Secret` displayed on the My Apps page.

## 3. Configure the App

1. Launch SeatXray to display the initial screen.
2. Click the settings icon located on the left side (Windows version) or bottom right (Android version) to open the settings view.
3. Paste the acquired `API Key` and `API Secret` into their respective input fields.
4. Click the "Save & Test Connection" button and confirm that communication is successful.

## Notes
A **FREE REQUEST QUOTA** is set for the Amadeus API, with monthly limits on the number of searches and seat map retrievals.
Please check the [Official Pricing Page](https://developers.amadeus.com/pricing) for details.
Acquired keys are recorded only on your device or your specified storage locations and are never sent to or collected by external parties.
