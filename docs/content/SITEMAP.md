# Ashford & Briggs — Expanded Site Architecture

The original single scroll is broken into a real multi-page structure.
Original copy is frozen verbatim in `docs/original-snapshot/` (revert point).

## Public routes
| Route | Page | Purpose |
|-------|------|---------|
| `/` | Home | Hero, problem framing, product overview, social proof, CTA |
| `/product` | Paladin | Deep feature breakdown, the Intelligence Pane, differentiation |
| `/how-it-works` | How It Works | The 4-step live-call flow, expanded with detail |
| `/about` | About | Company story, mission, founders, Jacksonville roots |
| `/blog` | Blog index | Published posts, tag filter |
| `/blog/:slug` | Blog post | Rendered Markdown article + SEO meta |
| `/contact` | Contact / Demo | Demo request form + direct contact channels |

## Admin routes (auth-gated)
| Route | Page | Min role |
|-------|------|----------|
| `/admin/login` | Login | — |
| `/admin` | Dashboard | author |
| `/admin/posts` | Post list | author (own) / editor+ (all) |
| `/admin/posts/new` | Composer (AI-assisted) | author |
| `/admin/posts/:id` | Editor (AI-assisted) | author (own) / editor+ |
| `/admin/demo-requests` | Demo inbox | editor |
| `/admin/users` | User management | admin |

## Global
- Sticky header with primary nav + "Request a Demo" CTA
- Footer: contact, LinkedIn, legal, condensed nav
- Consistent SEO meta per route (title, description, OG)
