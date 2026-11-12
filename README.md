# Israel Watch · Global News

Mobile-first PWA with headline aggregation about Israel, Jewish communities worldwide and Israeli innovation, including Bridges for Peace, FIRM and ONE FOR ISRAEL. This is a linked headline aggregator, not independent verification or an AI-authored briefing.

## Publish it for free with GitHub Pages

1. Create a **public** GitHub repository `israel-watch`, using `main` as the default branch.
2. Upload the *contents* of this package to the repository root, retaining `.github/workflows/update-news.yml` (hidden folders matter). GitHub Desktop or command-line Git is reliable for nested files.
3. Under **Settings → Pages → Build and deployment → Source**, select **GitHub Actions** (not `Deploy from a branch`).
4. Open **Actions → Update and publish Israel Watch → Run workflow → Run workflow**. If Actions needs to be enabled, enable it first. The workflow fetches feeds, writes `data/news.json` and publishes the site as one operation.
5. Check the workflow run is green. Open `https://YOUR-USERNAME.github.io/israel-watch/` or the URL under Settings → Pages. On iPhone in Safari choose Share → Add to Home Screen; on Android Chrome choose Add to Home screen/Install app.

Schedule: `04:00` and `15:00` UTC (06:00, 17:00 SAST). GitHub Action scheduled events may be delayed, skipped under load, or disabled after prolonged inactivity. The UI displays the actual last-generated timestamp. The manual browser Refresh button reloads the latest already-published data; **to force a new live source fetch**, run the workflow via GitHub Actions.

Note: If GitHub Actions says it is denied permission to write to the repository, verify repository/organisation Actions workflow policy permits `GITHUB_TOKEN` write permissions. This workflow explicitly requests `contents: write`, `pages: write`, and `id-token: write`. Also ensure Pages is configured to deploy via GitHub Actions.

## How it works

- `aggregate.py` runs on GitHub's Linux runner, fetches available publisher RSS and Google News RSS results, deduplicates titles, and writes `data/news.json`.
- `.github/workflows/update-news.yml` runs the script twice per day **and** deploys the resulting app snapshot directly to GitHub Pages. This is necessary because commits made with `GITHUB_TOKEN` do not independently trigger a new branch-based Pages deployment.
- `index.html`, `app.js`, and `styles.css` render the mobile app and its sections; `manifest.webmanifest` plus `service-worker.js` provide installability and shell caching.
- Data is fetched on app load, via the refresh button, and every 15 minutes while the app remains open.

## Local preview

```sh
python -m pip install -r requirements.txt
python aggregate.py  # needs Internet access
python -m http.server 8000
```

Open `http://localhost:8000`. Initial packaged `data/news.json` is empty until the first successful run. This app needs hosted HTTPS for full mobile installability.

## Editorial and product limitations

- Articles retain source titles, attribution, dates and original links. This app does **not** independently fact-check stories or promise balanced/in-depth synthesis. RSS can include opinion and duplicate or stale stories.
- Bridges for Peace, FIRM and ONE FOR ISRAEL first-party updates are organisation communications, not independent verification. Some RSS sources can block requests or change their feeds; the snapshot reports failures.
- Google News RSS results depend on a third-party, unofficial feed interface.
- Browser bookmarks are device-local, with no account synchronisation. No push notifications, native App Store install, or private user accounts are included.
