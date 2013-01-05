Here's a list of required features. If they aren't in this list, they won't be implemented.

# Admin interface:
- Posts must be assigned one category (or subcategory) to be filed under (e.g. for Woove, News/Sports/Weather) OR be static pages. Dynamic pages (e.g. for quicktrack) are not modifiable by users.
- Posts may optionally be added to the front page, which aggregates content of all sections, sorted by date
- Posts may be either published or unpublished, and this state may change at any time
- Need a way to bulk-import everything from Joomla (preferably including users)

# Main site:
- The front page is sorted by date (with most recent posts first), and paginated
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
- How to handle subcategories on the side nav
- Our logo - I can't find a vector image. Does someone have one? Which version should we use (should it show "radio for everyone"/"90.7 fm" or not)?
- "Read more" links
- Donation link - Our current site has one, but there wasn't one in the new design. Do we need one, if so, where? Between the logo and side nav would not be too difficult.
- Web player
- "Mobile"
- How mouseover / currently selected links appear in each navigation bar.
- How will users be handled? 
- Program guide - this is currently a horrible image and should be an HTML table.
- How should pagination be displayed at the bottom of the page?
- Should copyright info be at the bottom of the page?
- Should posts have publication dates visible? What about static pages?
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
