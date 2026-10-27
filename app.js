const $ = (id) => document.getElementById(id);
let token = localStorage.getItem("jvm_token") || "";
let currentUser = null;
let currentChatId = null;
let mode = "chat";
let authMode = "login";
let busy = false;

$("year").textContent = new Date().getFullYear();

function toast(message) {
  const node = $("toast");
  node.textContent = message;
  node.classList.add("show");
  setTimeout(() => node.classList.remove("show"), 3200);
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function showAuth(show=true) { $("authModal").classList.toggle("hidden", !show); if(show) $("authEmail").focus(); }
function setAuthMode(value) {
  authMode = value;
  const registering = value === "register";
  $("authTitle").textContent = registering ? "Create your account" : "Welcome back";
  $("authSubtitle").textContent = registering ? "Set up your JVM AI workspace." : "Sign in to continue to your AI workspace.";
  $("nameField").classList.toggle("hidden", !registering);
  $("authName").required = registering;
  $("authPassword").autocomplete = registering ? "new-password" : "current-password";
  $("authSubmit").textContent = registering ? "Create account" : "Sign in";
  $("switchText").textContent = registering ? "Already have an account?" : "New to JVM AI?";
  $("switchAuth").textContent = registering ? "Sign in" : "Create account";
  $("authError").textContent = "";
}
async function api(path, options={}) {
  const headers = {...(options.headers || {})};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body) headers["Content-Type"] = "application/json";
  const response = await fetch(path, {...options, headers});
  let data = {};
  try { data = await response.json(); } catch (_) {}
  if (!response.ok) {
    if (response.status === 401 && token) { signOut(false); }
    throw new Error(data.detail || `Request failed (${response.status})`);
  }
  return data;
}
function signOut(showMessage=true) {
  token = ""; currentUser = null; currentChatId = null;
  localStorage.removeItem("jvm_token");
  $("userBadge").textContent = "Guest";
  $("authOpen").textContent = "Sign in";
  $("chatList").innerHTML = '<p class="muted small">Sign in to save chats.</p>';
  $("messages").innerHTML = ""; $("messages").classList.add("hidden"); $("welcome").classList.remove("hidden");
  $("accountModal").classList.add("hidden");
  if (showMessage) toast("You have signed out.");
}
async function loadMe() {
  if (!token) return;
  try {
    currentUser = await api("/api/auth/me");
    $("userBadge").textContent = currentUser.name + (currentUser.is_admin ? " · Admin" : "");
    $("authOpen").textContent = "Account";
    await loadChats();
  } catch (_) { signOut(false); }
}
async function loadChats() {
  if (!token) return;
  try {
    const chats = await api("/api/chats");
    $("chatList").innerHTML = "";
    if (!chats.length) {
      $("chatList").innerHTML = '<p class="muted small">No saved conversations yet.</p>';
      return;
    }
    chats.forEach(chat => {
      const button = document.createElement("button");
      button.className = "chat-item" + (chat.id === currentChatId ? " selected" : "");
      button.textContent = chat.title || "Conversation";
      button.title = chat.title || "Conversation";
      button.onclick = () => openChat(chat.id);
      $("chatList").appendChild(button);
    });
  } catch (error) { toast(error.message); }
}
function appendMessage(role, content, extraClass="") {
  $("welcome").classList.add("hidden");
  $("messages").classList.remove("hidden");
  const row = document.createElement("div");
  row.className = `message ${role} ${extraClass}`;
  const avatar = document.createElement("div"); avatar.className = "avatar"; avatar.textContent = role === "user" ? "Y" : "J";
  const bubble = document.createElement("div"); bubble.className = "bubble"; bubble.textContent = content;
  row.append(avatar, bubble); $("messages").appendChild(row);
  $("messages").scrollTop = $("messages").scrollHeight;
  return row;
}
async function openChat(id) {
  if (!token) { showAuth(); return; }
  try {
    const data = await api(`/api/chats/${id}`);
    currentChatId = id;
    $("messages").innerHTML = "";
    $("welcome").classList.add("hidden"); $("messages").classList.remove("hidden");
    data.messages.forEach(m => appendMessage(m.role, m.content));
    await loadChats();
    if (window.innerWidth <= 760) $("sidebar").classList.remove("open");
  } catch (error) { toast(error.message); }
}
function newChat() {
  currentChatId = null; $("messages").innerHTML = "";
  $("messages").classList.add("hidden"); $("welcome").classList.remove("hidden");
  loadChats();
}
async function sendMessage(text) {
  text = text.trim();
  if (!text || busy) return;
  if (!token) { toast("Please sign in to start a conversation."); showAuth(); return; }
  busy = true; $("sendBtn").disabled = true; $("prompt").value = ""; resizePrompt();
  appendMessage("user", text);
  const waiting = appendMessage("assistant", "Thinking…", "typing");
  try {
    const data = await api("/api/chat", {method:"POST", body:JSON.stringify({chat_id:currentChatId, message:text, mode})});
    currentChatId = data.chat_id;
    waiting.querySelector(".bubble").textContent = data.reply;
    waiting.classList.remove("typing");
    await loadChats();
  } catch (error) {
    waiting.querySelector(".bubble").textContent = error.message;
    waiting.classList.remove("typing");
  } finally { busy = false; $("sendBtn").disabled = false; $("prompt").focus(); }
}
function resizePrompt() {
  const p = $("prompt"); p.style.height = "auto"; p.style.height = Math.min(p.scrollHeight, 180) + "px";
}
$("composer").addEventListener("submit", e => { e.preventDefault(); sendMessage($("prompt").value); });
$("prompt").addEventListener("input", resizePrompt);
$("prompt").addEventListener("keydown", e => { if(e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("composer").requestSubmit(); } });
$("newChatBtn").onclick = newChat;
$("chatMode").onclick = () => { mode="chat"; $("chatMode").classList.add("active"); $("codeMode").classList.remove("active"); $("prompt").placeholder="Message JVM AI..."; };
$("codeMode").onclick = () => { mode="code"; $("codeMode").classList.add("active"); $("chatMode").classList.remove("active"); $("prompt").placeholder="Ask JVM Code Assistant to write or debug code..."; };
document.querySelectorAll(".suggestion").forEach(btn => btn.addEventListener("click", () => { $("prompt").value = btn.dataset.prompt; resizePrompt(); $("prompt").focus(); if(!token) showAuth(); else sendMessage(btn.dataset.prompt); }));
$("authOpen").onclick = () => currentUser ? openAccount() : showAuth();
$("authClose").onclick = () => showAuth(false);
$("switchAuth").onclick = () => setAuthMode(authMode === "login" ? "register" : "login");
$("authForm").addEventListener("submit", async e => {
  e.preventDefault(); $("authError").textContent = "";
  const payload = {email:$("authEmail").value.trim(), password:$("authPassword").value};
  if (authMode === "register") payload.name = $("authName").value.trim();
  const endpoint = authMode === "register" ? "/api/auth/register" : "/api/auth/login";
  $("authSubmit").disabled = true;
  try {
    const data = await api(endpoint, {method:"POST", body:JSON.stringify(payload)});
    token = data.access_token; currentUser = data.user; localStorage.setItem("jvm_token", token);
    $("userBadge").textContent = currentUser.name + (currentUser.is_admin ? " · Admin" : "");
    $("authOpen").textContent = "Account"; showAuth(false); newChat(); await loadChats();
    toast(currentUser.is_admin ? "Welcome! Your account has administrator access." : "Signed in successfully.");
  } catch(error) { $("authError").textContent = error.message; }
  finally { $("authSubmit").disabled = false; }
});
async function openAccount() {
  $("accountInfo").textContent = `${currentUser.name} · ${currentUser.email}${currentUser.is_admin ? " · Administrator" : ""}`;
  $("adminInfo").classList.add("hidden");
  if (currentUser.is_admin) {
    try {
      const data = await api("/api/admin/summary");
      $("adminInfo").innerHTML = `<strong>Admin overview</strong><br>Registered users: ${data.users}<br>Conversations: ${data.chats}<br>Messages: ${data.messages}`;
      $("adminInfo").classList.remove("hidden");
    } catch (_) {}
  }
  $("accountModal").classList.remove("hidden");
}
$("settingsBtn").onclick = () => currentUser ? openAccount() : showAuth();
$("accountClose").onclick = () => $("accountModal").classList.add("hidden");
$("signOutBtn").onclick = () => signOut();
$("mobileMenu").onclick = () => $("sidebar").classList.toggle("open");
document.addEventListener("keydown", e => { if(e.key==="Escape"){showAuth(false);$("accountModal").classList.add("hidden");$("sidebar").classList.remove("open");} });
(async () => {
  try {
    const status = await fetch("/api/health").then(r=>r.json());
    $("providerLabel").textContent = `AI provider: ${status.ai_provider} · ${status.model}`;
  } catch (_) {}
  setAuthMode("login");
  await loadMe();
})();
