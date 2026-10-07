# Profile widgets

## Research showcase artwork

`build_showcase.py` generates bilingual problem/method/result cards, five
evidence-backed milestones, an original developer vignette and conceptual
AdsMind workflow GIFs. It runs locally on Windows with Pillow and system fonts;
it does not fetch data or publish anything. README `picture` sources select
stacked artwork at 600px or less, and static story artwork when reduced motion
is requested. SVGs adapt to dark color schemes; text uses dark ink on warm
white in the light scheme. Approved Nagato artwork and capsule header/footer
are reused unchanged. GIF timing is illustrative, never benchmark timing.

Milestone links point to the upstream merged PR and version-specific arXiv
records. Public code and software releases are linked separately; no repository
publication date is invented. Keep the confirmed-paper updater and its review
statuses independent of this presentation layer.

## Confirmed paper metadata

`update_papers.py` refreshes only the owner-confirmed arXiv IDs in
`CONFIRMED_IDS`. Add a new ID only after confirming authorship; author-name and
topic matches are not identity evidence. Both README tables use one HTTPS
request with default certificate validation. Missing papers, changed author
names, malformed feeds or missing README markers stop the update with a nonzero
exit status, preserving the existing tables on source/validation failure.
Review statuses remain manually maintained by the owner; arXiv does not verify
submission, review or acceptance status. Dates used for ordering are first
submission dates, not revision dates. Run the updater checks with:

```text
python -m unittest discover -s .github/scripts -p "test_update_papers.py"
```

Daily Update proposes changes through a single reusable draft PR from
`automation/daily-readme` to `main`, limited to the two README files. It never
pushes directly to the protected main branch or merges its own proposal.
GitHub Actions must be allowed to create pull requests in the repository's
workflow settings; normal review requirements still apply. The draft PR contains
the actual generated tables and quotes for inspection, and its URL appears in
the workflow summary. A source failure stops the workflow before PR publication.

The profile workflow writes generated files only to `profile-live`. The main
branch holds the bilingual README, approved artwork and widget source code.

- Notes: inspect the latest ten commits in each configured public note repository;
  skip README, changelog, hidden and removed files; select one changed note per
  repository and display the three most recently updated repositories. Dates are
  commit timestamps. `notes.md` contains immutable file links at those commits.
- History: save anonymous counts for the current UTC calendar quarter only when
  there are real participants. Keep eight quarters. A quarter retains its latest
  snapshot; unchanged votes do not change its date. Withdrawing all current votes
  removes the current quarter's snapshot. Older quarters remain historical.
- Coding time: `wakatime_username` in `profile-widgets.json` is intentionally null
  until the owner supplies a public account. The connector requests only public
  `last_7_days` statistics, without credentials. Private/unavailable or still
  processing data produces an explicit status card, never invented hours.
  Language and editor shares have separate denominators; only their top four
  entries are shown. API failures do not replace the existing note snapshot.

Run tests with:

```text
python -m unittest discover -s .github/scripts -p "test_profile*.py"
```

After configuring a public WakaTime username, run **Profile interactive widgets**
manually or wait for its daily run. No WakaTime key should be committed.


Collection widgets:
- `profile_collection.py` fetches the latest 100 public stars, grouped by primary
  repository language in `collection.md`. These are bookmarks, not endorsements.
- At most five PR/release events, one per repository, from the latest 100 public
  events. Exclude profile automation, bots, unmerged closures and prereleases.
  This bounded event feed is not lifetime contribution statistics.
- Contributor portraits are GitHub commit-attributed users in AdsMind/CatDT,
  up to 100 per repository. Attribution does not imply paper authorship.
- Source failure retains each previous successful dataset and labels it stale.
- New SVG cards have a dark color-scheme variant; approved artwork is unchanged.
- Weekly humor is an original three-item rotation, not a scraped third-party feed.
- The paper gallery reuses verified preprint illustrations. It does not invent
  book covers, talks, models, personal reading preferences or a newsletter.

Curated research showroom and chemistry blog bookshelf:
- `.github/profile-showroom.json` is the shared source for both README blocks.
  It contains confirmed blog ownership, article titles/dates, project links and
  immutable repository references. This is a curated archive, not a live feed.
- Run `python .github/scripts/build_showroom.py` to regenerate showroom SVGs,
  project showcase cards, individual clickable book covers, and the
  `SHOWROOM` / `BLOG-BOOKSHELF` / `VISUAL-NAV` blocks. This does not modify paper
  or quote blocks. The first project story image is replaced by the showcase;
  existing workflow illustrations, results and animations remain available.
  The existing artwork helper requires Pillow in the local Python environment.
- `assets/pt111-example.xyz` preserves the source coordinates linked in the
  manifest. Its SVG is a coordinate projection, not a new experiment.
- CatDT gallery images use the committed AdsorbDiff module example PNGs at a
  fixed commit. They do not demonstrate a new run or complete pipeline validation.
- Bookshelf covers are original decorative vectors for 2021 Chinese study posts.
- Each cover is an independent image link; inline images wrap naturally on small
  screens. Project showcase cards use separate mobile SVGs. Existing header,
  footer and approved Nagato assets are unchanged.
- The research-question issue form is a public discussion entry; private
  collaboration uses the Gmail contact. Project bugs belong in their own repos.

Visual finishing pass:
- Run `python .github/scripts/build_visual_polish.py` for the complete design.
  It first builds the showroom, then applies chapter dividers, scroll timelines,
  and consistent contact/project button styling. The command is repeatable.
- Design language: solid `#ECE9E0` warm paper, `#A4ABD6` lavender lines and nodes,
  `#353247` ink; sparse gold `#C39B65` crescent and red `#A83F55` knot details
  echo the approved Nagato icon. Header/footer colors and character assets stay
  untouched. Dark surfaces use `#22212D` / `#343145` and white primary text.
- Book covers use spine, page-edge and shadow layers. Research diagrams keep
  coordinate/source labels, result scopes and the existing contribution wording.
- Slow six-second opacity pulses appear only on navigation/diagram/timeline
  nodes. `prefers-reduced-motion: reduce` disables these pulses. Timeline dates
  and independently clickable source links stay synchronized in UTC order.
