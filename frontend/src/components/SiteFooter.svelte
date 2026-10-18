<script lang="ts">
  import Icon from './Icon.svelte'
  import Logo from './Logo.svelte'
  import Mark from './Mark.svelte'
  import ThemeToggle from './ThemeToggle.svelte'

  const cols = [
    {
      title: 'Product',
      links: [
        ['Live demo', '/#product'],
        ['How a cell works', '/#inside'],
        ['Use cases', '/use-cases'],
        ['Pricing', '/pricing'],
      ],
    },
    {
      title: 'Build',
      links: [
        ['Docs', '/docs'],
        ['API reference', '/docs#api'],
        ['Self-hosting', '/docs#self-host'],
        ['Architecture', '/docs#architecture'],
      ],
    },
    {
      title: 'App',
      links: [
        ['Your sheets', '/app'],
        ['New sheet', '/app/new'],
        ['Start from a template', '/use-cases#templates'],
      ],
    },
  ]
</script>

<footer class="footer">
  <div class="frame">
    <div class="top">
      <div class="brand">
        <Logo />
        <p class="muted">A spreadsheet that researches for you. Rows are things, columns are questions, and every cell is answered by an agent that cites its sources.</p>
      </div>
      {#each cols as c}
        <nav aria-label={c.title}>
          <p class="label">{c.title}</p>
          <ul>
            {#each c.links as [label, href]}
              <li><a {href}>{label}</a></li>
            {/each}
          </ul>
        </nav>
      {/each}
    </div>
    <div class="wordmark" aria-hidden="true">
      <span>GRIDMIND</span>
      <Mark size={22} accent class="wm-mark" />
    </div>
    <div class="bottom">
      <span class="label">© {new Date().getFullYear()} GridMind · An independent project</span>
      <div class="right">
        <ThemeToggle />
        <button class="btn btn-ghost btn-sm" onclick={() => scrollTo({ top: 0, behavior: 'smooth' })}>
          Back to top <Icon name="arrow" size={14} />
        </button>
      </div>
    </div>
  </div>
</footer>

<style>
  .footer {
    margin-top: var(--s-9);
    border-top: 1px solid var(--ink);
    padding-top: var(--s-8);
  }
  .top {
    display: grid;
    grid-template-columns: 2fr repeat(3, 1fr);
    gap: var(--s-6);
  }
  .brand p {
    margin-top: var(--s-4);
    max-width: 36ch;
    font-size: var(--fs-sm);
  }
  ul {
    list-style: none;
    padding: 0;
    margin-top: var(--s-3);
    display: grid;
    gap: var(--s-2);
  }
  nav a {
    font-size: var(--fs-sm);
    color: var(--ink-2);
    background: linear-gradient(var(--accent), var(--accent)) 0 100% / 0 1px no-repeat;
    transition: background-size var(--t-med) var(--ease), color var(--t-fast);
  }
  nav a:hover {
    color: var(--ink);
    background-size: 100% 1px;
  }
  .wordmark {
    position: relative;
    margin-top: var(--s-8);
    font-family: var(--font-display);
    font-stretch: 75%;
    font-weight: 900;
    font-size: clamp(4rem, 19vw, 16.5rem);
    line-height: 0.8;
    letter-spacing: -0.03em;
    color: transparent;
    -webkit-text-stroke: 1px var(--line);
    user-select: none;
    overflow: hidden;
  }
  .wordmark :global(.wm-mark) {
    position: absolute;
    right: 0;
    top: 0;
  }
  .bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    padding: var(--s-5) 0;
    border-top: 1px solid var(--line);
    flex-wrap: wrap;
  }
  .right {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  @media (max-width: 860px) {
    .top {
      grid-template-columns: 1fr 1fr;
    }
    .brand {
      grid-column: 1 / -1;
    }
  }
</style>
