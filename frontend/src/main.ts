import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
// @ts-ignore  // 临时忽略类型声明缺失，建议后续添加 vue3-katex 的类型声明文件
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