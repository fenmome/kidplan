import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')

  // Getters
  const isAuthenticated = computed(() => !!token.value)

  // Actions
  async function login(credentials) {
    const data = await authApi.login(credentials.username, credentials.password)
    token.value = data.access_token
    username.value = credentials.username
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('username', credentials.username)
    return true
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return {
    token,
    username,
    isAuthenticated,
    login,
    logout
  }
})
