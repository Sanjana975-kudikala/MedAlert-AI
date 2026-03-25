// ========== Mobile nav toggle ==========
const navToggle = document.getElementById("navToggle");
const navLinks = document.getElementById("navLinks");

if (navToggle && navLinks) {
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });

  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      navLinks.classList.remove("open");
    });
  });
}

// ========== Footer year ==========
const yearSpan = document.getElementById("year");
if (yearSpan) {
  yearSpan.textContent = new Date().getFullYear();
}

// ========== Demo timestamp for previews ==========
const demoSpans = document.querySelectorAll("[data-demo-time]");
if (demoSpans.length) {
  const now = new Date();
  const formatted = now.toISOString().slice(0, 16).replace("T", " ");
  demoSpans.forEach((el) => (el.textContent = formatted));
}

// ========== Hospital search by place ==========
function searchHospitalsByPlace() {
  const input = document.getElementById("placeInput");
  if (!input) {
    alert("Search input not found");
    return;
  }

  const place = input.value.trim();

  if (!place) {
    alert("Please enter a place name");
    return;
  }

  fetch(`/hospitals_by_place?place=${encodeURIComponent(place)}`)
    .then((res) => {
      if (!res.ok) throw new Error("Server returned " + res.status);
      return res.json();
    })
    .then((data) => {
      displayHospitals(data);
      setTimeout(scrollToHospitals, 150);
    })
    .catch((err) => {
      console.error("Hospital fetch error:", err);
      alert("Unable to fetch hospitals. Please try again.");
    });
}

// ========== Display hospitals ==========
function displayHospitals(hospitals) {
  let container = document.getElementById("hospitalResults");

  if (!container) {
    container = document.createElement("div");
    container.id = "hospitalResults";
    container.style.marginTop = "20px";
    document.querySelector("main").appendChild(container);
  }

  let html = "<h3>Hospitals Nearby</h3>";

  if (!Array.isArray(hospitals) || hospitals.length === 0) {
    html += "<p>No hospitals found nearby.</p>";
  } else {
    hospitals.forEach((h) => {
      html += `
        <div class="card hospital-card" style="margin-bottom:10px;">
          <div class="hospital-name">${h.name}</div>
          <div>${h.address}</div>
          <div class="hospital-distance">📍 ${h.distance} km away</div>
        </div>
      `;
    });
  }

  container.innerHTML = html;
}

// ========== Health Alert Pop-up System ==========

// Advice Arrays for the Pop-up
const lowRiskAdvice = [
    "Take care of your health! Remember to stay hydrated and eat balanced meals.",
    "Maintain a healthy lifestyle. Light walking for 20 minutes is highly recommended today.",
    "Health Tip: Rest is vital for recovery. Ensure you get 8 hours of sleep."
];

const medRiskAdvice = [
    "We remind you to be cautious. Monitor your vitals and avoid high-stress activities.",
    "Health Remedy: Include more antioxidants in your diet and follow your medication strictly.",
    "Suggestion: Your risk is moderate. We suggest visiting a hospital for a professional checkup."
];

function checkAndNotify() {
    fetch('/get_active_alerts')
        .then(res => res.json())
        .then(alerts => {
            alerts.forEach(alert => {
                const now = new Date();
                const lastNotified = new Date(alert.last_notified);
                const diffHrs = (now - lastNotified) / (1000 * 60 * 60);

                // --- TEMPORARY CHANGE FOR TESTING ---
                // Change 'diffHrs >= alert.interval_hrs' to 'true'
                if (true) { 
                    showInPagePopUp(alert);
                }
                // ------------------------------------
            });
        })
        .catch(err => console.error("Error fetching active alerts:", err));
}
function showInPagePopUp(alert) {
    const modal = document.getElementById("healthAlertModal");
    const title = document.getElementById("alertTitle");
    const body = document.getElementById("alertBody");
    const visitedBtn = document.getElementById("visitedBtn");

    if (!modal) return; // Guard if modal HTML is missing

    title.innerText = `${alert.disease_name} - ${alert.level}`;
    
    // Logic for Advice Text
    if (alert.level === "HIGH RISK") {
        body.innerHTML = `<strong>URGENT:</strong> Please take care and <strong>visit a hospital as soon as possible</strong>. Your health is priority.`;
    } else if (alert.level === "MEDIUM RISK") {
        const advice = medRiskAdvice[Math.floor(Math.random() * medRiskAdvice.length)];
        body.innerText = advice;
    } else {
        const advice = lowRiskAdvice[Math.floor(Math.random() * lowRiskAdvice.length)];
        body.innerText = advice;
    }

    modal.style.display = "block";

    // Action: Stop Alert completely (Visited Hospital)
    visitedBtn.onclick = () => {
        fetch(`/stop_alert/${alert.disease_name}`, { method: 'POST' })
        .then(() => {
            modal.style.display = "none";
            // Refresh dashboard banner if it exists
            if (typeof loadAlertBanner === "function") loadAlertBanner();
        });
    };
}

// Function for the "Remind me later" button
function dismissPopUp() {
    const titleElement = document.getElementById("alertTitle");
    if (titleElement) {
        const diseaseName = titleElement.innerText.split(' - ')[0];
        // Tell backend to update last_notified so the interval starts over
        fetch(`/update_notified_time/${diseaseName}`, { method: 'POST' })
        .then(() => {
            document.getElementById("healthAlertModal").style.display = "none";
        });
    } else {
        document.getElementById("healthAlertModal").style.display = "none";
    }
}

// Check for alert intervals every 30 seconds
setInterval(checkAndNotify, 30000);

// ========== Auto scroll helper ==========
function scrollToHospitals() {
  const section = document.getElementById("hospitalResults");
  if (section) {
    section.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}