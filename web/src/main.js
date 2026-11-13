import { createApp } from 'vue'
import '@fontsource/geist/latin-400.css'
import '@fontsource/geist/latin-500.css'
import '@fontsource/geist/latin-600.css'
import '@fontsource/geist-mono/latin-400.css'
import '@fontsource/geist-mono/latin-500.css'
import './styles/tokens.css'
import './styles/app.css'
import App from './App.vue'
import { iniciar } from './store.js'

createApp(App).mount('#app')
iniciar()
