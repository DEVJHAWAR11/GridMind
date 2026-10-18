/**
 * Offline data for demo mode. A simulated agent "researches" against this table so the app
 * works with no backend. It is a small, hand-written snapshot and may be out of date, and the UI says so.
 */
import type { Confidence, Source, Step } from '../types'

type Topic = 'hiring' | 'stack' | 'funding' | 'hq' | 'founded' | 'ceo' | 'product'
type Fact = [answer: string, confidence: Confidence, detail: string]
interface Company {
  name: string
  domain: string
  wiki: string
  facts: Record<Topic, Fact>
}

const TOPICS: [Topic, RegExp][] = [
  ['hiring', /hir|fresher|graduate|new.?grad|intern|entry.?level|junior/i],
  ['ceo', /\bceo\b|founder|who (runs|leads|founded)|chief exec/i],
  ['stack', /stack|tech|language|framework|built with|engineering/i],
  ['funding', /fund|raise|valuation|series|investor|round|ipo|stage/i],
  ['hq', /headquarter|\bhq\b|based|located|where|office|city/i],
  ['founded', /founded|what year|started|when|launch/i],
  ['product', /product|make|do they|does it|what does|offer|sell|build/i],
]

export const COMPANIES: Record<string, Company> = {
  openai: {
    name: 'OpenAI',
    domain: 'openai.com',
    wiki: 'OpenAI',
    facts: {
      hiring: ['Yes, residency and early-career roles', 'medium', 'The careers site lists early-career openings, and the Residency program takes people moving into AI research and engineering.'],
      stack: ['Python, TypeScript, Kubernetes', 'medium', 'Job posts point to Python for research and backend services, TypeScript for product surfaces, and very large Kubernetes clusters for training and serving.'],
      funding: ['$40B round (2025)', 'medium', 'Reported as a $40B round led by SoftBank in 2025.'],
      hq: ['San Francisco, USA', 'high', 'Headquartered in San Francisco, California.'],
      founded: ['2015', 'high', 'Founded in December 2015, originally as a non-profit research lab.'],
      ceo: ['Sam Altman', 'high', 'Sam Altman is co-founder and CEO.'],
      product: ['ChatGPT and the OpenAI API', 'high', 'Best known for ChatGPT and for selling model access through its developer API.'],
    },
  },
  anthropic: {
    name: 'Anthropic',
    domain: 'anthropic.com',
    wiki: 'Anthropic',
    facts: {
      hiring: ['Limited: fellows program, select roles', 'medium', 'Most openings target experienced hires; the Anthropic Fellows program is the main early-career path.'],
      stack: ['Python, Rust, TypeScript', 'medium', 'Engineering roles mention Python for research and infrastructure, Rust for performance-critical systems, and TypeScript for product.'],
      funding: ['Series F, $13B (2025)', 'medium', 'A $13B Series F in September 2025 valued the company at about $183B.'],
      hq: ['San Francisco, USA', 'high', 'Headquartered in San Francisco, California.'],
      founded: ['2021', 'high', 'Founded in 2021 by a group of former OpenAI researchers.'],
      ceo: ['Dario Amodei', 'high', 'Dario Amodei is co-founder and CEO.'],
      product: ['Claude models and apps', 'high', 'Builds the Claude family of models, sold through its apps and API.'],
    },
  },
  perplexity: {
    name: 'Perplexity',
    domain: 'perplexity.ai',
    wiki: 'Perplexity_AI',
    facts: {
      hiring: ['Yes, new-grad engineering roles', 'medium', 'The careers page has listed new-grad software engineering roles alongside senior positions.'],
      stack: ['Python, TypeScript, Next.js', 'low', 'Inferred from job descriptions; the company publishes little about its internal stack.'],
      funding: ['$200M at $20B (2025)', 'medium', 'Reported to have raised $200M at a $20B valuation in 2025.'],
      hq: ['San Francisco, USA', 'high', 'Headquartered in San Francisco, California.'],
      founded: ['2022', 'high', 'Founded in August 2022.'],
      ceo: ['Aravind Srinivas', 'high', 'Aravind Srinivas is co-founder and CEO.'],
      product: ['AI answer engine', 'high', 'An answer engine that searches the web and responds with cited sources.'],
    },
  },
  stripe: {
    name: 'Stripe',
    domain: 'stripe.com',
    wiki: 'Stripe,_Inc.',
    facts: {
      hiring: ['Yes, new-grad and intern programs', 'high', 'Runs recurring new-grad and internship hiring for engineering.'],
      stack: ['Ruby, Java, Go, TypeScript', 'medium', 'Ruby is the historical core of the API; Java and Go back infrastructure; TypeScript powers the dashboard.'],
      funding: ['Series I, $6.5B (2023)', 'high', 'Raised $6.5B in a Series I in March 2023.'],
      hq: ['South San Francisco and Dublin', 'high', 'Dual headquarters in South San Francisco, USA and Dublin, Ireland.'],
      founded: ['2010', 'high', 'Founded in 2010 by Patrick and John Collison.'],
      ceo: ['Patrick Collison', 'high', 'Patrick Collison is co-founder and CEO.'],
      product: ['Online payments infrastructure', 'high', 'APIs and tools for accepting payments, billing and financial operations online.'],
    },
  },
  notion: {
    name: 'Notion',
    domain: 'notion.com',
    wiki: 'Notion_(productivity_software)',
    facts: {
      hiring: ['Yes, early-career roles', 'medium', 'Lists early-career and intern roles in some cycles; most openings are experienced hires.'],
      stack: ['TypeScript, React, Postgres', 'medium', 'Engineering blog posts describe a TypeScript and React client on a sharded Postgres backend.'],
      funding: ['$275M at $10B (2021)', 'medium', 'Raised $275M at a $10B valuation in October 2021.'],
      hq: ['San Francisco, USA', 'high', 'Headquartered in San Francisco, California.'],
      founded: ['2013', 'high', 'Founded in 2013; the product as known today launched in 2016.'],
      ceo: ['Ivan Zhao', 'high', 'Ivan Zhao is co-founder and CEO.'],
      product: ['Connected workspace for docs and wikis', 'high', 'An all-in-one workspace for notes, docs, wikis and project tracking.'],
    },
  },
  linear: {
    name: 'Linear',
    domain: 'linear.app',
    wiki: 'Linear_(software)',
    facts: {
      hiring: ['Rarely; small, senior remote team', 'medium', 'Openings are few and mostly senior; the company deliberately keeps the team small.'],
      stack: ['TypeScript, React, GraphQL', 'high', 'TypeScript end to end with React on the client and a GraphQL API.'],
      funding: ['Series C, $82M (2025)', 'medium', 'Raised an $82M Series C in 2025 at a $1.25B valuation.'],
      hq: ['San Francisco (remote-first)', 'high', 'Registered in San Francisco; most of the team works remotely.'],
      founded: ['2019', 'high', 'Founded in 2019.'],
      ceo: ['Karri Saarinen', 'high', 'Karri Saarinen is co-founder and CEO.'],
      product: ['Issue tracking for software teams', 'high', 'Issue tracking, roadmaps and planning for product and engineering teams.'],
    },
  },
  vercel: {
    name: 'Vercel',
    domain: 'vercel.com',
    wiki: 'Vercel',
    facts: {
      hiring: ['Selective; few junior roles', 'low', 'Openings skew senior; junior roles appear occasionally.'],
      stack: ['TypeScript, Go, Rust', 'medium', 'TypeScript for the platform and Next.js; Go and Rust for build and edge infrastructure.'],
      funding: ['Series F, $300M (2025)', 'medium', 'Raised a $300M Series F in 2025.'],
      hq: ['San Francisco (remote-first)', 'high', 'Headquartered in San Francisco with a largely remote team.'],
      founded: ['2015', 'high', 'Founded in 2015 as ZEIT; renamed Vercel in 2020.'],
      ceo: ['Guillermo Rauch', 'high', 'Guillermo Rauch is founder and CEO.'],
      product: ['Frontend cloud, maker of Next.js', 'high', 'Hosting and infrastructure for web apps; maintains the Next.js framework.'],
    },
  },
  figma: {
    name: 'Figma',
    domain: 'figma.com',
    wiki: 'Figma',
    facts: {
      hiring: ['Yes, early-career program', 'medium', 'Runs an early-career program with new-grad and intern roles.'],
      stack: ['C++/WebAssembly, TypeScript, Rust', 'high', 'The editor renders with C++ compiled to WebAssembly; TypeScript for UI; Rust in multiplayer services.'],
      funding: ['Public, NYSE: FIG (2025)', 'high', 'Listed on the New York Stock Exchange in July 2025.'],
      hq: ['San Francisco, USA', 'high', 'Headquartered in San Francisco, California.'],
      founded: ['2012', 'high', 'Founded in 2012 by Dylan Field and Evan Wallace.'],
      ceo: ['Dylan Field', 'high', 'Dylan Field is co-founder and CEO.'],
      product: ['Collaborative interface design tool', 'high', 'A browser-based tool for designing interfaces together in real time.'],
    },
  },
  supabase: {
    name: 'Supabase',
    domain: 'supabase.com',
    wiki: 'Supabase',
    facts: {
      hiring: ['Rarely; remote, senior-heavy', 'low', 'Fully remote hiring that mostly targets experienced engineers.'],
      stack: ['Postgres, Elixir, TypeScript, Go', 'high', 'Built around Postgres, with Elixir for Realtime, TypeScript for Studio and Go for parts of the tooling.'],
      funding: ['Series E, $100M (2025)', 'medium', 'Raised a $100M Series E in 2025.'],
      hq: ['Remote-first, distributed team', 'medium', 'A fully distributed company without a single main office.'],
      founded: ['2020', 'high', 'Founded in 2020.'],
      ceo: ['Paul Copplestone', 'high', 'Paul Copplestone is co-founder and CEO.'],
      product: ['Postgres development platform', 'high', 'A Postgres database with auth, storage, realtime and edge functions.'],
    },
  },
}

const ALIASES: Record<string, string> = { 'stripe inc': 'stripe', 'perplexity ai': 'perplexity', 'notion labs': 'notion' }

export function findCompany(entity: string): Company | undefined {
  const k = entity.toLowerCase().replace(/[.,]|\b(inc|ltd|llc|corp)\b/g, '').trim()
  return COMPANIES[ALIASES[k] ?? k] ?? COMPANIES[k.split(/\s+/)[0]]
}

export function topicOf(question: string): Topic | undefined {
  return TOPICS.find(([, re]) => re.test(question))?.[0]
}

function sourcesFor(c: Company, topic: Topic): Source[] {
  const wiki = { url: `https://en.wikipedia.org/wiki/${c.wiki}`, title: `${c.name} - Wikipedia` }
  const site = { url: `https://${c.domain}/`, title: `${c.name} official site` }
  const careers = { url: `https://${c.domain}/careers`, title: `Careers at ${c.name}` }
  switch (topic) {
    case 'hiring':
      return [careers, site]
    case 'stack':
      return [careers, wiki]
    case 'funding':
      return [wiki, site]
    default:
      return [wiki, site]
  }
}

export interface Script {
  steps: { delay: number; step: Step }[]
  result: { answer: string; detail: string; confidence: Confidence; sources: Source[] }
}

const jitter = (base: number) => base + Math.random() * base * 0.8

/** A believable agent trace shaped exactly like the backend's: plan, search, (read), answer, maybe a second pass. */
export function script(entity: string, question: string): Script {
  const c = findCompany(entity)
  const topic = topicOf(question)
  const q1 = `${entity} ${question}`
  const now = () => Date.now() / 1000
  const steps: Script['steps'] = []
  const push = (delay: number, node: Step['node'], summary: string, data: Record<string, unknown> = {}) =>
    steps.push({ delay: jitter(delay), step: { node, summary, data, ts: now() } })

  push(350, 'plan', `Planned search: ${q1}`, { queries: [q1] })

  if (c && topic) {
    const [answer, confidence, detail] = c.facts[topic]
    const sources = sourcesFor(c, topic)
    push(800, 'search', `Found ${sources.length} sources`, { sources })
    if (confidence !== 'high') push(700, 'read', `Read ${sources[0].url}`, { url: sources[0].url, chars: 3800 + Math.floor(Math.random() * 1800) })
    push(650, 'answer', `Answered (${confidence} confidence): ${answer}`, { sufficient: true, missing: '' })
    return { steps, result: { answer, detail: `${detail} (Demo data: an offline snapshot that may be out of date.)`, confidence, sources } }
  }

  // Not in the demo table: show the refinement loop, then give up honestly.
  const generic = [
    { url: `https://en.wikipedia.org/wiki/Special:Search?search=${encodeURIComponent(entity)}`, title: `Search results for ${entity}` },
  ]
  push(800, 'search', 'Found 1 source', { sources: generic })
  push(650, 'answer', 'Answered (low confidence): Unknown', { sufficient: false, missing: `a primary source about ${entity}` })
  const q2 = `${entity} official ${topic ?? 'information'}`
  push(500, 'plan', `Planned search: ${q2}`, { queries: [q2] })
  push(800, 'search', 'Found 1 source', { sources: generic })
  push(600, 'answer', 'Answered (low confidence): Not in demo data', { sufficient: false, missing: 'live web search' })
  return {
    steps,
    result: {
      answer: 'Not in demo data',
      detail: `This was a simulated run. Demo mode only has offline data for a few sample companies (${Object.values(COMPANIES)
        .slice(0, 4)
        .map((x) => x.name)
        .join(', ')} and others) and common questions about them. Connect the GridMind API to research "${entity}" on the live web.`,
      confidence: 'low',
      sources: generic,
    },
  }
}
