// Electron Python API
export const electronPython = {
  execute: async (action: any) => {
    if (window.electronAPI) {
      return await window.electronAPI.executePython(action)
    }
    return null
  }
}
