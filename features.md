# Post model
- An article is a "blog post".
- Belongs to exactly one category (displayed on left)
- Has a date attached to it
- May or may not be on the front page (? - consult with staff)
- May be published (publically accessible) or unpublished (e.g. drafts). This may change at any time
- The date on the post should be the date at which it was first published. Posts can be optionally flagged as "front page". "front page" posts are displayed on wuvt.vt.edu, sorted reverse-chronologically
- Has author attached to it
- Has HTML content
- Has ASCII title

# Page model
- Static pages that need to be quickly accessible, e.g. contact/about/staff
- Has title
- Has HTML content
- Filed under exactly one top menu
- May or may not need published flag (? - consult with staff)

# Category model
- No subcategories currently (? - consult with staff)
- Posts assigned one category
- Has category name

# Show model
- May need to work on this...  will talk to FM PD
- May consist of one or two hosts (a single "DJ")
- "genres you can DJ" - for internal use
- Real name
- Airname/showname (currently this is a single field but could be separated)
- At least one contact email (maybe support two or allow comma separated addrs?)

# DJ set model
- Has start time, end time
- Has DJ ID

# Track model
- Has DJ set ID
- Title/artist/album
- Record label
- Whether the song was vinyl
- Whether the song was a request
- Which rotation bin the album was in (default: none)
- Listeners at time of play - from icecast, for internal use currently

# Rotation bin model
- Has a name
- Is "new music" rotation (New Music - Heavy, New Music - Medium, New Music - Light) or not (e.g. Metal, Recurrent vinyl, Americana, etc)
- There should be an option for tracks to not be played from rotation bin (most aren't)
- The three "new music" bins are needed for reporting, will need to do a simple DB query for reports
- These can be hard-coded in a table as they don't change
- "visible" flag - in the unlikely event a rotation bin is no longer used, toggling this should make it so DJs don't see this in the dropdown.

# User model
- People that can manage content on the site
- Users are either "admin" or non-admin. Admins can manage categories (add/edit/delete/reorder/change parent) and manage users (add/edit/delete/change password/change role/lock). Users must have: email, password, admin/non-admin flag, locked/unlocked flag, user ID (numerical, can't be changed)

# Admin interface:
- Main things: manage pages, manage posts, manage categories, manage users, manage media, "settings (catch-all for random utilities)"
- Manage posts: add, edit existing ones, delete, change category/content, toggle frontpage/published
- Pages: are either static or dynamic. Dynamic pages (e.g. for quicktrack) are not modifiable by users, but the page should appear in page/category listings. 
- Categories: may optionally have one parent. Admins must be able to manage these by add/edit/delete/reorder/change parent. If you "edit" the name of a category, all posts filed under that category should point to the same category with the new name.
- Media: users must be able to upload any images or other media and include uploaded images in their posts/pages
- Settings: Need a way to bulk-import everything from Joomla (preferably including users)
- Settings: should include a kludge "import from Joomla" utility, hopefully this will only need to be used once. Separate DB export would be nice.

# Main site interface:
- The front page is sorted by date (with most recent posts first) and paginated IF the post is published AND marked to be on the front page.
- Posts are either blog-style (Woove, News/Sports/Weather), static content (e.g. about, donate, staff info, etc), or dynamic info pulled from the new quicktrack
- Top banner pulls currently playing data from quicktrack
- There needs to be an Atom feed of some sort. 

# Trackman
* Quicktrack replacement
* DJ interface not yet implemented, but will be based on Quicktrack1
* Submits automation submission from Winamp as before
    * Submission URL has changed but everything else functions the same
* All public APIs that were in use have been reimplemented identically, others
  removed
    * Checked logs on sledge to ensure this
    * RDS updates and everything else will work fine after switchover
* Site automatically updated when track changes using events instead of polling
* New "DJ set" model to clean up handling of show start/stop times
* Playlist archive works as before, but with a calendar instead of a dropdown

# Unspecified behavior
- Donation link - Our current site has one, but there wasn't one in the new design. Do we need one, if so, where? Between the logo and side nav would not be too difficult.
- Should copyright info be at the bottom of the page?
- DJ profiles - these appear to be published in Joomla but aren't linked to from anywhere. I'd like to have these linked to from the schedule
- What content goes into the main Atom feed? All articles or just front page articles? Do there need to be more Atom feeds for each category?

# Things modified from original design
- Links moved to left side so everything fits properly. Also looks much better, actually features our logo, and is easier to use.
- Local zone was put where Woove was, since Local Zone will be static content

# Design/layout
- The top navigation will be static content (and anything that isn't "blog-style posts", including About, Community, Local Zone, Contact. Playlists will also be included and pulled from quicktrack
- Top navigation should feature dropdown menus for subcategories
- The side navigation will be categories for non-static content (Woove, News, Sports, Weather)
- The items in the robot's speech bubble are: listen live, last 15 tracks, and the program guide. This can't be changed. (You really can't fit more than 3 items)


## Important links - goes on robot
Listen live
Last 15 tracks
Program guide


## Blog categories - goes on side nav, aggregated on front page
Woove
	Editorials
	Artist profiles
	DJ Bios
	Interviews
	Music Reviews
	Lists
	Local Events
	Movie Reviews
	Literary Contest
News
Sports
Weather
Events (probably a duplicate of Woove events)
Polls*
Links*
Newsletter*
(* - these were in Candice's original design but I moved them to the static content items. They won't be on the side)


## Static content - goes on top nav
About
	WUVT
	History
	Staff
	Get involved
	DJ Profiles (?) - pages exist but aren't linked to from anywhere
Community
	Links
	Alumni
	PSAs
	Underwriting
	Mailing list
	Newsletter
Playlists
	By date
	By DJ
Local zone 
	LZ CD
	Archive
Contact
	Mailing list
	Newsletter
	Staff
