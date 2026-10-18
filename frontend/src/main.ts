import '@fontsource-variable/archivo/wdth.css'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
import '@fontsource/ibm-plex-mono/600.css'
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import './styles/tokens.css'
import './styles/base.css'
import './lib/theme.svelte'
import './lib/motion'
import { mount } from 'svelte'
import App from './App.svelte'
import { startRouter } from './lib/router.svelte'

startRouter()
mount(App, { target: document.getElementById('app')! })
