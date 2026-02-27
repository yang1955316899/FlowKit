// Electron System API
export const electronSystem = {
  showNotification: (title: string, body: string) => {
    if (window.electronAPI) {
      window.electronAPI.showNotification(title, body)
    }
  }
}
