/** 
 * Simple persistent session ID helper for ML demo.
 * Uses localStorage to persist the ID across page reloads.
 */
export const getSessionId = () => {
  let sid = localStorage.getItem('streamsync_session_id')
  if (!sid) {
    sid = `sess_${Math.random().toString(36).slice(2, 10)}_${Date.now().toString(36)}`
    localStorage.setItem('streamsync_session_id', sid)
  }
  return sid
}
