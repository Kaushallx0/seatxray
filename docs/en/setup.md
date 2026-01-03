# SeatXray ⚡️ Setup Guide

To use SeatXray, you need to acquire and configure an Amadeus API Key. Please follow the steps below.

## 1. Create an Amadeus Developers Account
1. Access [Amadeus for Developers](https://developers.amadeus.com/).
2. Create a free account (Sign Up) for "Self-Service APIs".

## 2. Register Your App and Get Keys
1. After logging in, open the [My Apps](https://developers.amadeus.com/my-apps) page.
2. Click "Create New App", enter an app name (e.g., `MySeatXray`), and save.
3. On the app details page, click **"Get production environment"** to start the upgrade process.

### Steps to Request Production Environment
To obtain production keys, you must complete these four steps:
1. **Personal & Billing info**: Enter your billing information.
2. **Payment method**: Register a payment method.
3. **Sign agreement & confirm**: Review and agree to the Terms of Service.

> When moving to the production environment, you need to sign an agreement and register payment information. You will not be charged as long as you stay within the free usage limits.

### Question Regarding API Validation
During the application process, you will be asked if you are using APIs that require validation.

**"Does your app use an API that requires validation?"**

Please select **"No"**. SeatXray only performs searches and displays seat maps; it does not use booking functions or other features that require additional validation. Your production keys will be issued immediately.

4. After the procedure is complete, copy the **API Key** and **API Secret** from the My Apps page.

## 3. Configure the App
1. Launch SeatXray.
2. Click the settings icon ⚙️ in the top right.
3. Enter your acquired `API Key` and `API Secret`.
4. Click "Save" and perform a "Connection Test".

## Notes
- A **FREE REQUEST QUOTA** is set, with monthly limits (e.g., 2,000 searches, 1,000 seat maps). Please check the [Official Pricing Page](https://developers.amadeus.com/pricing) for details.
- Acquired keys are recorded only on your device or your specified storage locations and are never sent to or collected by external parties (including the developers).
