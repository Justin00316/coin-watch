# Coin Watch: setup guide

About 15 minutes on your laptop, then 5 minutes on each phone. Everything is free.

**What you're setting up**

| Part | Where it lives | What it does |
|---|---|---|
| The app | A free GitHub website | Live prices, charts, cycles, news (spoken), alarms while the app is open |
| The cloud checker | GitHub, running every 10 minutes | Checks prices even when every phone is locked, and sends the alarm |
| ntfy | Free app on the phone | Receives that alarm: loud sound and vibration on the lock screen |

Nothing personal goes online. "My coins" amounts stay on the phone they're typed into.

---

## Part 1: Your laptop (once)

### 1. Make a GitHub account
1. Go to **github.com** and choose **Sign up**. Use your personal email (not school).
2. Pick a username. It appears in the app's web address, e.g. `https://yourname.github.io/coin-watch/`.

### 2. Make an empty project ("repository")
1. Signed in, click **+** (top right), then **New repository**.
2. Name: `coin-watch`
3. Choose **Public**. Free websites need public projects. Only prices and alert levels are in it, nothing personal.
4. Leave everything else as it is, then click **Create repository**.

### 3. Put the files in
**Easiest:** tell Claude "the repository is github.com/YOURNAME/coin-watch, please upload it". A GitHub sign-in window opens once, and Claude does the rest.

**Or by hand:** on the new repository page, click **uploading an existing file**. Open the `Coin Watch` folder in File Explorer, select **everything inside it** (including the `.github` and `checker` folders), drag it all onto the page, then click **Commit changes**.

### 4. Switch on the website
1. In the repository, click **Settings**, then **Pages** (left menu).
2. Under **Branch**, choose **main** and **/ (root)**, then click **Save**.
3. Wait about 1 minute and refresh. The page shows your link: `https://YOURNAME.github.io/coin-watch/`

### 5. Connect the phone alarms
1. Still in **Settings**: **Secrets and variables**, then **Actions**, then **New repository secret**.
2. Name: `NTFY_TOPIC`
3. Secret: the private channel name Claude gave you in the chat (it starts `coinwatch-`).
4. Click **Add secret**.

> Keep that channel name private. Anyone who knows it can see the alerts. Don't post it anywhere.

### 6. Start the cloud jobs
1. Click the **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and enable them**.
2. Click **Update news and price history**, then **Run workflow** and **Run workflow**. This fetches the first news and history (green tick after about a minute).
3. Click **Price alerts**, then **Run workflow**. Leave "Send a test alert" ticked and click **Run workflow**. Once the phone is set up (Part 2), it rings with a test alert.

From now on both jobs run by themselves: prices every 10 minutes, news every hour.

---

## Part 2: Each phone (yours first, to check it)

### A. Install the app (no store needed)
1. Open the link in **Chrome**.
2. Tap **⋮** (top right), then **Add to Home screen** (or **Install app**). It now has its own icon.
3. Open it and tap **Turn on alarm**. When asked, **Allow** notifications.
4. Tap **한국어** for Korean. The words, the spoken alarms and the news all switch.

### B. Install ntfy (for alarms when the phone is locked)
1. In the **Play Store**, install **ntfy** (by Philipp Heckel, free).
2. Open it and tap **+**. Type the private channel name, leave **Use another server** off, turn **Instant delivery** on, then tap **Subscribe**.
3. Tap the new subscription, then **⋮**, **Settings** (notification settings):
   - **Keep alerting for highest priority**: turn on. The phone keeps ringing until tapped, like an alarm clock.
   - Pick a loud **sound**.
4. Samsung battery saver can silence apps. Go to **Settings, Apps, ntfy, Battery** and choose **Unrestricted**.
5. Back on the laptop, run the **Price alerts** test again (Part 1, step 6.3). The phone should ring within a minute.

---

## Changing things later

**Alarms on the phone screen:** add, pause or delete them in the app itself, on that phone.

**Lock-screen alerts (the cloud ones):** these are in the file `alerts.json`. Either ask Claude to change them, or on GitHub open `alerts.json`, click the pencil, edit the numbers and click **Commit changes**. Types you can use:
- `"below"`: price falls below a number
- `"above"`: price rises above a number
- `"drop24h"`: falls by this many percent within 24 hours

Each lock-screen alert repeats every 6 hours while the price stays past the level (`repeatHours` in the same file).

## Good to know
- GitHub's timer can run a few minutes late when it's busy, so lock-screen alerts arrive within roughly 10 to 20 minutes of a move.
- Alarms on the app screen only ring while the app is open. Use **Keep screen on** if it's left on a stand.
- Prices come from CoinGecko, with Coinbase as a backup. Korean prices come from Upbit. News comes from Google News, filtered to established outlets.
- The app shows prices and history only. It is not financial advice.
