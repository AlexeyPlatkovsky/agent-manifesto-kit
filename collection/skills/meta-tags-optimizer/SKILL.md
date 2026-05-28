---
name: meta-tags-optimizer
description: Produces title tag, meta description, Open Graph, and Twitter Card metadata for a given page so it ranks and previews well in search results and on social platforms. Use when the user asks to write or improve page meta tags, fix CTR, or fix how a URL previews when shared.
---

## Scope

- Produce a complete metadata package for a single page: title tag, meta description, canonical link, robots directive, Open Graph block, Twitter Card block, and the small set of common supporting tags (`viewport`, `author`, `article:published_time`, etc.) when relevant.
- Offer multiple title and description variants when the user wants alternatives to compare.
- Note CTR trade-offs between variants in plain language.

## Reference Versions

This skill is written against:
- **Open Graph protocol v1.0** — https://ogp.me
- **Twitter / X Cards** — current cards markup as documented at https://developer.x.com/en/docs/x-for-websites/cards/overview/abouts-cards
- **HTML Living Standard** for `<meta>` and `<link>` element semantics — https://html.spec.whatwg.org
- **Length budgets** — title ≈ 50–60 characters, meta description ≈ 150–160 characters. These are approximations of pixel-width truncation observed in major search-engine SERPs (Google in particular) and are not formal specifications; budgets shift over time. Treat them as defaults the user may override at run time.

The user may override any reference (e.g. a different SERP-budget source or a vendor-specific card spec) at run time; the skill follows the override and notes it in the output.

## Boundaries

- Single responsibility: write metadata. Do not rewrite page body copy, generate schema markup, or route to other skills.
- Do not change page URLs, slugs, or canonical targets without explicit user confirmation.

## Safety Constraints

- Do not fabricate. Titles, descriptions, brand names, product names, image URLs, ranking promises, prices, or any factual claim must come from the user-supplied content or explicit user input. Fields that cannot be sourced are emitted as `missing`, never invented. This is the canonical no-fabrication rule for the skill.
- Respect length budgets defined in `Reference Versions`. Exceeding a budget must be a deliberate trade-off the user is told about, not a silent overflow.

## Stop Conditions

- Stop and ask when page URL, primary topic, target audience, or primary keyword cannot be identified.
- Stop and report blocked when required inputs (page topic, primary keyword or angle) are missing and cannot be inferred from supplied content.
- Stop and report blocked when the user asks for metadata that would misrepresent the page.

## Procedure

If any Stop Condition fires during a step, halt and emit a `blocked` row in the output table; do not continue to later steps until the trigger is resolved. If an **optional** field cannot be sourced (e.g. no `og:image` URL, no `twitter:creator`), do not halt — emit the field as `missing` in the table per the Output Contract and continue.

1. Identify the page: URL, page type (article, product, landing, category, home), primary keyword or angle, target audience, and the page's value proposition.
2. Draft title tag(s). Target the title budget defined in `Reference Versions`, place the primary keyword early, keep brand suffix optional. Offer two or three variants when the user wants comparison.
3. Draft meta description(s). Target the description budget defined in `Reference Versions`, include the primary keyword once naturally, include a concrete value or call to action. Offer two or three variants when the user wants comparison.
4. Build the Open Graph block: `og:title`, `og:description`, `og:type`, `og:url`, `og:image`, `og:site_name`, and `og:locale` when known.
5. Build the Twitter Card block: `twitter:card` (default `summary_large_image`), `twitter:title`, `twitter:description`, `twitter:image`, and `twitter:site` / `twitter:creator` when supplied.
6. Add supporting tags as relevant: canonical link, `robots`, `viewport`, `author`, and article time tags for article pages.
7. Note the CTR trade-off between variants (e.g. "variant A leads with keyword, variant B leads with benefit") so the user can pick or A/B-test.

## Verification

Before emitting the output, verify:
- Title length within the budget defined in `Reference Versions`, primary keyword present and near the front.
- Description length within the budget defined in `Reference Versions`, primary keyword present once, concrete CTA or value statement included.
- OG and Twitter blocks reference the same canonical URL and a real image URL or `missing`.
- No-fabrication rule held (see `Safety Constraints`).
- Canonical link, if present, is absolute.

## Output Contract

Emit:

`Skill: meta-tags-optimizer - output below`

Then provide, in order:

1. A fenced ```html block containing the recommended metadata, ready to drop into the page head. If multiple title or description variants were requested, include them as adjacent HTML comments so the user can swap.
2. A table:

| Field | Value (chosen variant) | Length | Variants Offered | Notes |
| --- | --- | --- | --- | --- |

`Notes` must call out any field marked `missing`, any deliberate over-budget length, and the CTR trade-off between variants.
