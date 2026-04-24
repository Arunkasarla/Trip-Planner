/**
 * script.js — Smart AI Trip Planner Frontend Logic
 */

const API = "http://127.0.0.1:8000"; // Change to deployed backend URL for production

/* ── State ──────────────────────────────────────────────────────────────── */
let currentTrip = null;
let leafletMap  = null;
let currentModalTrip = null;

/* ── Theme ──────────────────────────────────────────────────────────────── */
(function initTheme() {
  const saved = localStorage.getItem("theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  const btn = document.getElementById("themeToggle");
  if (btn) btn.textContent = saved === "dark" ? "🌙" : "☀️";
})();

document.getElementById("themeToggle")?.addEventListener("click", () => {
  const cur = document.documentElement.getAttribute("data-theme");
  const next = cur === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
  document.getElementById("themeToggle").textContent = next === "dark" ? "🌙" : "☀️";
});

/* ── Auth UI ────────────────────────────────────────────────────────────── */
(function initAuth() {
  const token = localStorage.getItem("token");
  const name  = localStorage.getItem("userName");
  const greeting = document.getElementById("userGreeting");
  const btn      = document.getElementById("authBtn");
  if (token && name) {
    if (greeting) greeting.textContent = `Hi, ${name.split(" ")[0]}`;
    if (btn) { btn.textContent = "Logout"; btn.onclick = doLogout; }
  }
})();

function openAuthModal() {
  document.getElementById("authModal")?.classList.add("open");
}
function closeAuthModal() {
  document.getElementById("authModal")?.classList.remove("open");
}
function switchTab(tab) {
  document.getElementById("loginForm").style.display    = tab === "login"    ? "block" : "none";
  document.getElementById("registerForm").style.display = tab === "register" ? "block" : "none";
  document.getElementById("tabLogin").className    = tab === "login"    ? "btn btn-primary btn-sm" : "btn btn-outline btn-sm";
  document.getElementById("tabRegister").className = tab === "register" ? "btn btn-primary btn-sm" : "btn btn-outline btn-sm";
}

async function doLogin() {
  const email    = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  if (!email || !password) { showToast("Fill in all fields", "error"); return; }
  try {
    const res  = await fetch(`${API}/login`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Login failed");
    localStorage.setItem("token",    data.access_token);
    localStorage.setItem("userName", data.user_name);
    localStorage.setItem("userId",   data.user_id);
    closeAuthModal();
    showToast(`Welcome back, ${data.user_name}!`, "success");
    location.reload();
  } catch (e) { showToast(e.message, "error"); }
}

async function doRegister() {
  const name     = document.getElementById("regName").value.trim();
  const email    = document.getElementById("regEmail").value.trim();
  const password = document.getElementById("regPassword").value;
  if (!name || !email || !password) { showToast("Fill in all fields", "error"); return; }
  try {
    const res  = await fetch(`${API}/register`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Registration failed");
    localStorage.setItem("token",    data.access_token);
    localStorage.setItem("userName", data.user_name);
    localStorage.setItem("userId",   data.user_id);
    closeAuthModal();
    showToast(`Account created! Welcome, ${data.user_name}!`, "success");
    location.reload();
  } catch (e) { showToast(e.message, "error"); }
}

function doLogout() {
  localStorage.removeItem("token");
  localStorage.removeItem("userName");
  localStorage.removeItem("userId");
  showToast("Logged out successfully", "info");
  setTimeout(() => location.reload(), 800);
}

/* ── Chip Selection ─────────────────────────────────────────────────────── */
document.getElementById("interestChips")?.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => chip.classList.toggle("active"));
});

/* ── Generate Trip ──────────────────────────────────────────────────────── */
async function generateTrip() {
  const budget    = parseFloat(document.getElementById("budget").value);
  const days      = parseInt(document.getElementById("days").value);
  const travelers = parseInt(document.getElementById("travelers").value);
  const month     = document.getElementById("month").value;
  const style     = document.getElementById("style").value;
  const starting  = document.getElementById("startLocation")?.value || "India";

  const chips = [...document.querySelectorAll(".chip.active")].map(c => c.dataset.val);
  if (!chips.length) { showToast("Select at least one interest", "error"); return; }
  if (!budget || !days) { showToast("Enter budget and days", "error"); return; }

  showLoading("🤖 AI is analyzing your preferences...");

  try {
    const res  = await fetch(`${API}/generate-trip`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ budget, days, travelers, month, style, interests: chips, starting_location: starting }),
    });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || "Failed to generate trip");

    currentTrip = json.data;
    renderResults(currentTrip);
    loadWeather(currentTrip.destination);
    loadMap(currentTrip.destination);
    showToast(`✈️ Trip to ${currentTrip.destination} ready!`, "success");

    // Update sidebar summary
    const box = document.getElementById("tripSummaryBox");
    if (box) {
      box.style.display = "block";
      document.getElementById("tripSummaryText").innerHTML =
        `📍 <b>${currentTrip.destination}</b><br>📅 ${days} days · 👥 ${travelers} travelers<br>💰 ₹${currentTrip.total_cost.toLocaleString()}`;
    }
  } catch (e) {
    hideLoading();
    showToast("Error: " + e.message, "error");
  }
}

/* ── Render Results ─────────────────────────────────────────────────────── */
function renderResults(trip) {
  hideLoading();
  document.getElementById("placeholderState").style.display = "none";
  document.getElementById("resultsState").style.display     = "block";

  // Banner
  document.getElementById("destName").textContent  = `📍 ${trip.destination}`;
  document.getElementById("destMeta").textContent  = `${trip.itinerary?.length || 0} Days · ${trip.hotels?.[0]?.name || ""}`;
  document.getElementById("totalCost").textContent = `💰 Total: ₹${trip.total_cost?.toLocaleString()} · Daily: ₹${trip.daily_budget?.toLocaleString()}`;

  // Attractions
  const attrEl = document.getElementById("attractionsList");
  if (attrEl && trip.attractions) {
    attrEl.innerHTML = trip.attractions.map(a =>
      `<span class="attraction-badge">🏛 ${a}</span>`).join("");
  }

  // Hotels
  const hotelsEl = document.getElementById("hotelsList");
  if (hotelsEl && trip.hotels) {
    hotelsEl.innerHTML = trip.hotels.map(h => `
      <div class="hotel-card">
        <div class="hotel-name">🏨 ${h.name}</div>
        <div class="hotel-meta">
          <span class="stars">${"⭐".repeat(Math.round(h.rating || 4))}</span>
          <span class="hotel-cost">₹${(h.cost_per_night||0).toLocaleString()}/night</span>
        </div>
      </div>`).join("");
  }

  // Tips
  const tipsEl = document.getElementById("tipsList");
  if (tipsEl && trip.tips) {
    tipsEl.innerHTML = trip.tips.map(t => `<span class="tip-badge">💡 ${t}</span>`).join("");
  }

  // Itinerary
  renderItinerary(trip.itinerary || []);
}

function renderItinerary(itinerary) {
  const container = document.getElementById("itineraryCards");
  if (!container) return;
  container.innerHTML = itinerary.map(day => `
    <div class="glass day-card fade-in">
      <div class="day-header">
        <div class="day-title">Day ${day.day} — ${day.theme}</div>
        <div class="day-cost-badge">₹${(day.day_cost||0).toLocaleString()}</div>
      </div>
      <div class="day-body">
        ${(day.slots || []).map(slot => `
          <div class="slot">
            <div class="slot-time">${slot.time}</div>
            <div class="slot-content">
              <div class="slot-activity">${slot.activity}</div>
              <div class="slot-meta">
                <span>📍 ${slot.place}</span>
                <span>⏱ ${slot.duration}</span>
                <span class="slot-cost">₹${(slot.cost||0).toLocaleString()}</span>
              </div>
              ${slot.notes ? `<div style="font-size:.8rem;color:var(--text-muted);margin-top:.25rem">💬 ${slot.notes}</div>` : ""}
            </div>
          </div>`).join("")}
        <div style="padding:.75rem 0;border-top:1px solid var(--card-border);font-size:.85rem;color:var(--text-muted)">
          📝 ${day.notes || ""}
        </div>
      </div>
    </div>`).join("");
}

/* ── Loading Helpers ────────────────────────────────────────────────────── */
function showLoading(msg = "Loading...") {
  document.getElementById("placeholderState").style.display = "none";
  document.getElementById("resultsState").style.display     = "none";
  const ls = document.getElementById("loadingState");
  if (ls) { ls.style.display = "flex"; document.getElementById("loadingText").textContent = msg; }
}
function hideLoading() {
  const ls = document.getElementById("loadingState");
  if (ls) ls.style.display = "none";
}

/* ── Weather ────────────────────────────────────────────────────────────── */
async function loadWeather(city) {
  const el = document.getElementById("weatherWidget");
  if (!el) return;
  try {
    const res  = await fetch(`${API}/weather/${encodeURIComponent(city)}`);
    const data = await res.json();
    el.innerHTML = `
      <div class="weather-main">
        <div class="weather-temp">${data.temperature}°C</div>
        <div class="weather-info">
          <h3>${data.condition}</h3>
          <p>💧 ${data.humidity}% · 💨 ${data.wind_speed} km/h · Feels ${data.feels_like}°C</p>
          <p style="margin-top:.25rem;font-size:.8rem;color:var(--text-muted)">📍 ${data.city}</p>
        </div>
      </div>
      <div class="weather-forecast">
        ${(data.forecast || []).map(f => `
          <div class="forecast-item">
            <div style="font-size:.7rem;color:var(--text-muted)">${f.date?.slice(0,10) || f.date}</div>
            <div class="forecast-temp">${f.temp}°</div>
            <div style="font-size:.7rem">${f.condition}</div>
            <div style="font-size:.7rem;color:var(--secondary)">🌧 ${f.rain_chance}%</div>
          </div>`).join("")}
      </div>`;
  } catch { el.innerHTML = `<div class="loader-text">Weather unavailable</div>`; }
}

/* ── Map (Leaflet.js) ───────────────────────────────────────────────────── */
async function loadMap(city) {
  try {
    const res  = await fetch(`${API}/map-data/${encodeURIComponent(city)}`);
    const data = await res.json();
    initLeafletMap(data.lat, data.lon, data.attractions || [], data.hotels || [], city);
  } catch { initLeafletMap(20.5937, 78.9629, [], [], city); }
}

function initLeafletMap(lat, lon, attractions, hotels, city) {
  if (!window.L) return;
  const mapEl = document.getElementById("map");
  if (!mapEl) return;
  if (leafletMap) { leafletMap.remove(); leafletMap = null; }
  leafletMap = L.map("map").setView([lat, lon], 12);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors"
  }).addTo(leafletMap);

  const pinIcon = (color, emoji) => L.divIcon({
    html: `<div style="background:${color};width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3)">${emoji}</div>`,
    className: "", iconSize: [32, 32], iconAnchor: [16, 32],
  });

  L.marker([lat, lon], { icon: pinIcon("#6366f1", "📍") })
    .addTo(leafletMap).bindPopup(`<b>${city}</b>`).openPopup();

  attractions.slice(0, 8).forEach(a => {
    L.marker([a.lat, a.lon], { icon: pinIcon("#f59e0b", "🏛") })
      .addTo(leafletMap).bindPopup(`<b>${a.name}</b><br>Attraction`);
  });
  hotels.slice(0, 4).forEach(h => {
    L.marker([h.lat, h.lon], { icon: pinIcon("#10b981", "🏨") })
      .addTo(leafletMap).bindPopup(`<b>${h.name}</b><br>Hotel`);
  });
}

/* ── Chatbot ────────────────────────────────────────────────────────────── */
function toggleChat() {
  document.getElementById("chatPanel")?.classList.toggle("open");
}

async function sendChatMessage() {
  const input = document.getElementById("chatInput");
  const msg   = input?.value.trim();
  if (!msg) return;
  if (!currentTrip) { showToast("Generate a trip first!", "error"); return; }

  addChatMsg(msg, "user");
  input.value = "";
  const sendBtn = document.getElementById("chatSend");
  if (sendBtn) sendBtn.disabled = true;

  addChatMsg("🤖 Analyzing your request...", "bot", "thinking");

  try {
    // Step 1: Get intent
    const intentRes  = await fetch(`${API}/chat-intent`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_message: msg, current_trip_data: currentTrip }),
    });
    const intentData = await intentRes.json();
    const intent     = intentData.intent;

    // Remove "thinking" message
    document.querySelector(".msg[data-id='thinking']")?.remove();
    addChatMsg(`📋 Intent: ${JSON.stringify(intent, null, 2)}`, "intent");

    if (intent.action === "unknown") {
      addChatMsg("❓ I didn't understand that. Try: 'Remove beach from day 2' or 'Make it cheaper'", "bot");
      return;
    }

    // Step 2: Apply intent
    const updateRes  = await fetch(`${API}/update-itinerary`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent_json: intent, current_trip_data: currentTrip }),
    });
    const updateData = await updateRes.json();

    currentTrip = updateData.data;
    renderItinerary(currentTrip.itinerary || []);
    document.getElementById("totalCost").textContent =
      `💰 Total: ₹${currentTrip.total_cost?.toLocaleString()} · Daily: ₹${currentTrip.daily_budget?.toLocaleString()}`;

    addChatMsg(`✅ Done! Applied: <b>${intent.action.replace(/_/g," ")}</b>. Itinerary updated below ↓`, "bot");
    showToast("Itinerary updated!", "success");
  } catch (e) {
    document.querySelector(".msg[data-id='thinking']")?.remove();
    addChatMsg("⚠️ Error: " + e.message, "bot");
    showToast("Chat error: " + e.message, "error");
  } finally {
    if (sendBtn) sendBtn.disabled = false;
  }
}

function addChatMsg(text, type, id = "") {
  const box = document.getElementById("chatMessages");
  if (!box) return;
  const div = document.createElement("div");
  div.className = `msg msg-${type}`;
  if (id) div.setAttribute("data-id", id);
  div.innerHTML = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

/* ── Save Trip ──────────────────────────────────────────────────────────── */
async function saveTrip() {
  if (!currentTrip) { showToast("No trip to save", "error"); return; }
  const token = localStorage.getItem("token");
  try {
    const res  = await fetch(`${API}/save-trip`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: JSON.stringify({ trip_data: currentTrip }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Save failed");
    showToast("✅ Trip saved to dashboard!", "success");
  } catch (e) { showToast("Save error: " + e.message, "error"); }
}

/* ── PDF Export ─────────────────────────────────────────────────────────── */
function downloadPDF(trip = null) {
  const t = trip || currentTrip;
  if (!t) { showToast("No trip to export", "error"); return; }
  const { jsPDF } = window.jspdf || {};
  if (!jsPDF) { showToast("PDF library not loaded", "error"); return; }

  const doc = new jsPDF();
  let y = 20;
  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.text(`Trip to ${t.destination}`, 105, y, { align: "center" }); y += 10;
  doc.setFontSize(11); doc.setFont("helvetica", "normal");
  doc.text(`Total Cost: Rs.${t.total_cost?.toLocaleString()}`, 105, y, { align: "center" }); y += 15;

  (t.itinerary || []).forEach(day => {
    if (y > 260) { doc.addPage(); y = 20; }
    doc.setFont("helvetica", "bold"); doc.setFontSize(13);
    doc.text(`Day ${day.day}: ${day.theme}`, 15, y); y += 7;
    doc.setFont("helvetica", "normal"); doc.setFontSize(10);
    (day.slots || []).forEach(slot => {
      if (y > 270) { doc.addPage(); y = 20; }
      const line = `  [${slot.time}] ${slot.activity} @ ${slot.place} - Rs.${slot.cost} (${slot.duration})`;
      const split = doc.splitTextToSize(line, 180);
      doc.text(split, 15, y); y += split.length * 5 + 2;
    });
    doc.text(`  Day Total: Rs.${day.day_cost?.toLocaleString()}`, 15, y); y += 10;
  });

  doc.save(`Trip-${t.destination}-${Date.now()}.pdf`);
  showToast("PDF downloaded!", "success");
}

/* ── Dashboard Functions ────────────────────────────────────────────────── */
async function loadTripHistory() {
  const token = localStorage.getItem("token");
  if (!token) { document.getElementById("notLoggedIn")?.style && (document.getElementById("notLoggedIn").style.display = "block"); return; }

  document.getElementById("dashLoading")?.style && (document.getElementById("dashLoading").style.display = "flex");

  try {
    const res  = await fetch(`${API}/trip-history`, { headers: { Authorization: `Bearer ${token}` } });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);
    const trips = data.trips || [];

    document.getElementById("dashLoading").style.display  = "none";
    if (!trips.length) {
      document.getElementById("emptyState").style.display   = "block";
      document.getElementById("tripsSection").style.display = "none";
    } else {
      document.getElementById("tripsSection").style.display = "block";
      document.getElementById("emptyState").style.display   = "none";
      renderTripGrid(trips);
      updateStats(trips);
    }
  } catch (e) {
    document.getElementById("dashLoading").style.display = "none";
    showToast("Error loading trips: " + e.message, "error");
  }
}

const DEST_EMOJIS = { Goa:"🏖", Manali:"🏔", Varanasi:"🛕", Andaman:"🌊", Rishikesh:"🌿",
  Jaipur:"🏰", Munnar:"🍃", Delhi:"🕌", default:"✈️" };

function renderTripGrid(trips) {
  const grid = document.getElementById("tripGrid");
  if (!grid) return;
  grid.innerHTML = trips.map(t => {
    const emoji = DEST_EMOJIS[t.destination] || DEST_EMOJIS.default;
    const date  = new Date(t.created_at).toLocaleDateString("en-IN");
    return `
      <div class="glass trip-card">
        <div class="trip-card-img">${emoji}</div>
        <div class="trip-card-body">
          <div class="trip-dest">📍 ${t.destination}</div>
          <div class="trip-meta">
            <span>📅 ${t.days} days</span>
            <span>💰 ₹${(t.budget||0).toLocaleString()}</span>
          </div>
          <div style="font-size:.78rem;color:var(--text-muted);margin-bottom:1rem">🗓 ${date}</div>
          <div class="trip-actions">
            <button class="btn btn-primary btn-sm" onclick='openTripModal(${JSON.stringify(t)})'>👁 View</button>
            <button class="btn btn-outline btn-sm" onclick='downloadPDF(${JSON.stringify(t.trip_json)})'>📄 PDF</button>
            <button class="btn btn-danger btn-sm" onclick="deleteTrip('${t.id}', this)">🗑</button>
          </div>
        </div>
      </div>`;
  }).join("");
}

function updateStats(trips) {
  const total  = trips.length;
  const dests  = new Set(trips.map(t => t.destination)).size;
  const days   = trips.reduce((s, t) => s + (t.days || 0), 0);
  const budget = trips.reduce((s, t) => s + (t.budget || 0), 0);
  const el = id => document.getElementById(id);
  if (el("statTotal"))  el("statTotal").textContent  = total;
  if (el("statDest"))   el("statDest").textContent   = dests;
  if (el("statDays"))   el("statDays").textContent   = days;
  if (el("statBudget")) el("statBudget").textContent = `₹${Math.round(budget).toLocaleString()}`;
}

function openTripModal(trip) {
  currentModalTrip = trip;
  document.getElementById("modalTitle").textContent = `📍 ${trip.destination}`;
  const tj = trip.trip_json || {};
  const content = `
    <div style="margin-bottom:1rem;padding:1rem;background:rgba(99,102,241,0.1);border-radius:10px">
      <strong>💰 Total: ₹${(trip.budget||0).toLocaleString()}</strong> &nbsp;·&nbsp;
      📅 ${trip.days} days &nbsp;·&nbsp; 🗓 ${new Date(trip.created_at).toLocaleDateString("en-IN")}
    </div>
    ${(tj.itinerary||[]).map(day => `
      <div style="margin-bottom:1rem;border:1px solid var(--card-border);border-radius:10px;overflow:hidden">
        <div style="background:var(--gradient);padding:.75rem 1rem;color:#fff;font-weight:700">
          Day ${day.day} — ${day.theme} <span style="float:right;opacity:.8">₹${(day.day_cost||0).toLocaleString()}</span>
        </div>
        <div style="padding:1rem">
          ${(day.slots||[]).map(s => `
            <div style="display:flex;gap:1rem;padding:.5rem 0;border-bottom:1px solid var(--card-border)">
              <span style="min-width:80px;font-size:.75rem;color:var(--primary);font-weight:700">${s.time}</span>
              <div>
                <div style="font-weight:600;font-size:.9rem">${s.activity}</div>
                <div style="font-size:.8rem;color:var(--text-muted)">📍 ${s.place} · ⏱ ${s.duration} · ₹${s.cost}</div>
              </div>
            </div>`).join("")}
        </div>
      </div>`).join("")}`;
  document.getElementById("modalContent").innerHTML = content;
  document.getElementById("tripModal").classList.add("open");
}

function closeTripModal() {
  document.getElementById("tripModal")?.classList.remove("open");
  currentModalTrip = null;
}

function loadTripInPlanner() {
  if (currentModalTrip?.trip_json) {
    localStorage.setItem("loadedTrip", JSON.stringify(currentModalTrip.trip_json));
    window.location.href = "planner.html";
  }
}

function exportModalPDF() {
  if (currentModalTrip?.trip_json) downloadPDF(currentModalTrip.trip_json);
}

async function deleteTripFromModal() {
  if (!currentModalTrip) return;
  await deleteTrip(currentModalTrip.id);
  closeTripModal();
}

async function deleteTrip(id, btnEl = null) {
  const token = localStorage.getItem("token");
  if (!confirm("Delete this trip?")) return;
  try {
    const res = await fetch(`${API}/trip/${id}`, {
      method: "DELETE", headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Delete failed");
    if (btnEl) btnEl.closest(".trip-card")?.remove();
    showToast("Trip deleted", "info");
    loadTripHistory();
  } catch (e) { showToast("Delete error: " + e.message, "error"); }
}

/* ── Load saved trip in planner (from dashboard) ───────────────────────── */
(function checkLoadedTrip() {
  const loaded = localStorage.getItem("loadedTrip");
  if (loaded && document.getElementById("resultsPanel")) {
    try {
      currentTrip = JSON.parse(loaded);
      localStorage.removeItem("loadedTrip");
      renderResults(currentTrip);
      loadWeather(currentTrip.destination);
      loadMap(currentTrip.destination);
      showToast("Trip loaded from dashboard!", "info");
    } catch {}
  }
})();

/* ── Toast Notifications ────────────────────────────────────────────────── */
function showToast(message, type = "info", duration = 3500) {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const icons = { success: "✅", error: "❌", info: "ℹ️" };
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || "ℹ️"}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = "0"; toast.style.transform = "translateX(100%)"; setTimeout(() => toast.remove(), 300); }, duration);
}

/* ── Hamburger Menu ─────────────────────────────────────────────────────── */
document.getElementById("hamburger")?.addEventListener("click", () => {
  document.getElementById("navLinks")?.classList.toggle("mobile-open");
});
