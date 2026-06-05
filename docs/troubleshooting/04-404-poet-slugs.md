# Troubleshooting 04: 404 Poet Slugs — Finding Correct Aldiwan.net URLs

## The Problem

When adding poets to `poets.yaml`, some poets return a 404 Error (Not Found) when the scraper runs.

Example:
```bash
2026-06-02 18:11:37,538 - diwanic.scraper.fetcher - ERROR - Failed to fetch https://www.aldiwan.net/cat-poet-Al-shafi-i: 404 Client Error
```

## Why This Happens

Aldiwan.net slugs for poets are inconsistent. 

- Some are transliterated: `Mutanabi`
- Some are English: `ahmed-shawqi`
- Some have extra prefixes: `al-shafie`
- Case sensitivity: Sometimes `Mutanabi` works, but `mutanabi` fails.

You cannot guess the slug just by the poet's name.

## The Solution

We created a **Discovery Script** (`scripts/discover_poet.py`) that extracts the correct metadata from the URL itself.

### How it works

1. It takes the full Aldiwan.net URL as input.
2. It fetches the page.
3. It uses a combination of techniques to find the slug, Arabic name, and era.

```python
# scripts/discover_poet.py logic
slug = poet_url.split('cat-poet-')[-1].strip('/')

# Find name in <title> or breadcrumbs
title_text = soup.find('title').get_text()
name = re.search(r'ديوان (.*?) -', title_text).group(1)

# Find era in breadcrumbs
links = soup.find('h2', class_='breadcrumbs').find_all('a')
era = links[-2].get_text()
```

## Real World Fixes

We discovered these mapping corrections:

| Poet | Our Guess (Failed) | Correct Slug (Works) |
|------|---------------------|----------------------|
| الإمام الشافعي | `Al-shafi-i` | `al-shafie` |
| الأصمعي | `Al-Asmai` | `al-asmaee` |
| أحمد شوقي | `Ahmad-Shawqi` | `ahmed-shawqi` |
| المتنبي | `Mutanabi` | `Mutanabi` |

## Updated Workflow

**Stop guessing slugs.** Always use the discovery script:

```bash
# 1. Browse Aldiwan.net and click a poet
# 2. Copy the URL from the browser
# 3. Discover
./venv/bin/python scripts/discover_poet.py https://www.aldiwan.net/cat-poet-al-shafie

# 4. Use the command it outputs to add the poet
./venv/bin/python scripts/add_poet.py "al-shafie" "الإمام الشافعي" "العصر العباسي"
```

## Lessons Learned

1. **URL-first data entry**: Trust the URL over manual name translation.
2. **Metadata extraction**: Use the breadcrumbs (`الديوان » العصر العباسي » المتنبي`)—they are the most reliable source for Name and Era.
3. **Automate everything**: Even adding a poet to a YAML file should be scripted to avoid typos.

---

## See Also
- `scripts/discover_poet.py` — The discovery engine
- `scripts/add_poet.py` — The config manager
- `configs/poets.yaml` — Our poet database
