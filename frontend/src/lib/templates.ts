export interface Template {
  slug: string
  title: string
  blurb: string
  audience: string
  entities: string[]
  questions: string[]
}

export const TEMPLATES: Template[] = [
  {
    slug: 'startup-research',
    title: 'Startup research',
    audience: 'Job seekers',
    blurb: 'Who is hiring, what they build with, and how well funded they are.',
    entities: ['OpenAI', 'Anthropic', 'Perplexity', 'Stripe', 'Notion', 'Linear', 'Vercel', 'Figma'],
    questions: ['Are they hiring freshers?', 'What is their tech stack?', 'What is their latest funding stage?', 'Where are they headquartered?'],
  },
  {
    slug: 'competitor-scan',
    title: 'Competitor scan',
    audience: 'Product teams',
    blurb: 'Position, leadership and momentum for every company in your market map.',
    entities: ['Vercel', 'Supabase', 'Linear', 'Notion', 'Figma'],
    questions: ['What do they build?', 'Who is the CEO?', 'When were they founded?', 'What is their latest funding?'],
  },
  {
    slug: 'lead-qualification',
    title: 'Lead qualification',
    audience: 'Sales and growth',
    blurb: 'Qualify accounts before the first call: location, stack and growth signals.',
    entities: ['Stripe', 'Notion', 'Linear', 'Supabase', 'Vercel'],
    questions: ['Where are they headquartered?', 'What is their tech stack?', 'Are they hiring engineers?'],
  },
  {
    slug: 'investor-diligence',
    title: 'Investor diligence',
    audience: 'Analysts and VCs',
    blurb: 'First-pass diligence: founders, founding year, capital raised.',
    entities: ['Perplexity', 'Anthropic', 'OpenAI', 'Supabase'],
    questions: ['Who is the CEO?', 'When were they founded?', 'What is their latest funding round?', 'What product do they sell?'],
  },
  {
    slug: 'tech-stack-audit',
    title: 'Tech stack audit',
    audience: 'Engineers and recruiters',
    blurb: 'Map languages and infrastructure across companies you are studying or targeting.',
    entities: ['Figma', 'Stripe', 'Linear', 'Supabase', 'Vercel', 'Notion'],
    questions: ['What is their tech stack?', 'Are they hiring engineers?'],
  },
]

export const templateBySlug = (slug: string) => TEMPLATES.find((t) => t.slug === slug)
