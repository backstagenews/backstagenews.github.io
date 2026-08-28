ADD A NEW STORY
===============
1. Copy _TEMPLATE.json to a new file named after the story, e.g.
     _data/new/asuu-suspends-strike.json
2. Fill it in.  "cat" is one of: news, entertainment, sports, business
   "date" format: "August 28, 2026"  (leave "" to use today)
3. From the site folder run:  python3 rebuild.py
   The story gets its own page, a designed cover, and appears on the
   homepage, ticker, its section, search and the RSS feed — newest first.

Add a photo (optional): put an image at  photos/<slug>.jpg  before rebuilding.
Files starting with "_" (like _TEMPLATE.json) are ignored.
