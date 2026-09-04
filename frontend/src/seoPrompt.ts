import type { Site } from "./api/types";

// Fixed instructional text, not live GrowthPilot data — unlike Digest.tsx's
// prompt, this doesn't depend on keywords/articles/audit state. Meant to be
// pasted into a fresh Claude Code session running in the target site's own
// repo to kick off a full programmatic-SEO architecture pass.
const SEO_PROMPT_BODY = `Audit and refactor the entire codebase as a senior full-stack engineer and SEO architect with the explicit goal of safely scaling to 100,000+ programmatic SEO pages.

Design a programmatic SEO system built on structured data that enables scalable page templates, dynamic routing, and unique intent-matched content per page, including titles, headings, descriptions, and FAQs, while avoiding thin content, duplication, and keyword cannibalization.

Implement advanced SEO foundations such as fully dynamic metadata (title, description, canonical, Open Graph, Twitter), appropriate schema markup (Article, FAQ, Breadcrumb, Product, or context-specific types), and intelligent internal linking using hub-and-spoke structures, related pages, and breadcrumbs.

Optimize the application for performance and scalability by prioritizing Core Web Vitals, leveraging static generation or incremental regeneration where possible, minimizing bundle size, and ensuring fast builds and effective caching even at very large page counts.

Refactor the codebase for clarity, modularity, and long-term maintainability by introducing clean abstractions for SEO logic, data fetching, and page templates, with safeguards and conventions that allow future pages to be added at scale without regressions.

If you need more info, use these programmatic SEO playbooks. Layer multiple together where it makes sense (locations + personas: "marketing agencies for startups in austin"; curation + locations: "best coworking spaces in san diego"; integrations + personas: "slack for sales teams"; glossary + translations: multi-language educational content).

1. Templates
Pattern: [type] template, free [type] template
Example searches: resume template, invoice template, pitch deck template
What it is: downloadable or interactive templates users can immediately use
Why it works: high intent, shareable assets, strong fit for product-led growth
Value requirements: usable templates, multiple variations, paid-level quality, frictionless usage
URL structure: /templates/[type]/, /templates/[category]/[type]/

2. Curation
Pattern: best [category], top [number] [things]
Example searches: best website builders, top 10 crm software, best free design tools
What it is: curated lists ranking or recommending products or services
Why it works: high commercial intent, decision-stage traffic, evergreen with updates
Value requirements: clear criteria, real testing, visible updates, non-affiliate bias
URL structure: /best/[category]/, /[category]/best/

3. Conversions
Pattern: [x] to [y], [amount] [unit] in [unit]
Example searches: 10 usd to gbp, 100 kg to lbs, pdf to word
What it is: tools or pages that convert formats, units, or values
Why it works: instant utility, massive volume, repeat usage
Value requirements: accurate data, fast tool, related conversions, mobile-first
URL structure: /convert/[from]-to-[to]/, /[from]-to-[to]-converter/

4. Comparisons
Pattern: [x] vs [y], [x] alternative
Example searches: webflow vs wordpress, notion vs coda, figma alternatives
What it is: side-by-side comparisons between products or solutions
Why it works: high purchase intent, clear search behavior, scalable
Value requirements: honest analysis, real feature data, use-case recommendations, frequent updates
URL structure: /compare/[x]-vs-[y]/, /[x]-vs-[y]/

5. Examples
Pattern: [type] examples, [category] inspiration
Example searches: saas landing page examples, email subject line examples, portfolio website examples
What it is: collections of real-world examples for inspiration or research
Why it works: research-phase traffic, highly shareable, strong creative appeal
Value requirements: real examples, screenshots or embeds, filters, explanation
URL structure: /examples/[type]/, /[type]-examples/

6. Locations
Pattern: [service] in [location]
Example searches: coworking spaces in san diego, dentists in austin, best restaurants in brooklyn
What it is: location-specific pages for services or businesses
Why it works: massive local intent, geographic scalability
Value requirements: real local data, actual listings, location insights, maps
URL structure: /[service]/[city]/, /locations/[city]/[service]/

7. Personas
Pattern: [product] for [audience], [solution] for [role or industry]
Example searches: payroll software for agencies, crm for real estate, project management for freelancers
What it is: persona-specific landing pages
Why it works: higher relevance, better conversion, scalable by audience
Value requirements: tailored messaging, relevant features, persona testimonials, real use cases
URL structure: /for/[persona]/, /solutions/[industry]/

8. Integrations
Pattern: [product] [product] integration, [product] + [product]
Example searches: slack asana integration, zapier airtable, hubspot salesforce sync
What it is: pages explaining how tools work together
Why it works: captures users of other tools, very high intent
Value requirements: real integrations, setup steps, use cases, visuals
URL structure: /integrations/[product]/, /connect/[product]/

9. Glossary
Pattern: what is [term], [term] definition
Example searches: what is pseo, api definition, what does crm stand for
What it is: educational pages explaining industry terms
Why it works: top-of-funnel traffic, authority building, internal linking
Value requirements: clear definitions, examples, related terms, depth
URL structure: /glossary/[term]/, /learn/[term]/

10. Translations
Pattern: localized versions of existing queries
Example searches: qué es pseo, was ist seo, マーケティングとは
What it is: translated and localized content for new markets
Why it works: new demand, lower competition, multiplied reach
Value requirements: high-quality translation, localization, hreflang, native review
URL structure: /[language]/[page]/, /es/, /de/, /fr/
Consider lingo.dev for this.

11. Directory
Pattern: [category] tools, [category] software
Example searches: ai copywriting tools, email marketing software, crm companies
What it is: structured directories listing tools or companies
Why it works: research traffic, backlink magnet, evergreen
Value requirements: comprehensive coverage, filters, detailed listings, updates
URL structure: /directory/[category]/, /[category]-directory/

12. Profiles
Pattern: [name], [entity] + [attribute]
Example searches: stripe ceo, airbnb founding story, elon musk companies
What it is: profile pages for people, companies, or entities
Why it works: informational demand, topical authority, long-tail coverage
Value requirements: accurate data, sourcing, unique insights, freshness
URL structure: /people/[name]/, /companies/[name]/`;

export function buildSeoPrompt(site: Site | null): string {
  const header = site
    ? `This is for ${site.name} (${site.url}). This session's working directory should be that site's own codebase, not the GrowthPilot tool.\n\n`
    : "";
  return header + SEO_PROMPT_BODY;
}
