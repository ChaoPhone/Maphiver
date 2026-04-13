import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/variables.css'
import Vue3Katex from 'vue3-katex'
import 'katex/dist/katex.min.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.use(Vue3Katex, {
  katexOptions: {
    throwOnError: false,
  },
})

app.mount('#app')