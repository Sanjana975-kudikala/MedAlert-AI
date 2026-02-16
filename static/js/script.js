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

// ========== Generic mode toggle ==========
document.querySelectorAll(".mode-toggle").forEach((toggle) => {
  const moduleName = toggle.dataset.module;
  if (!moduleName) return;

  const manualSection = document.getElementById(moduleName + "ManualSection");
  const reportSection = document.getElementById(moduleName + "ReportSection");
  if (!manualSection || !reportSection) return;

  const buttons = toggle.querySelectorAll(".mode-btn");

  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-mode");

      buttons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      if (mode === "manual") {
        manualSection.style.display = "block";
        reportSection.style.display = "none";
      } else {
        manualSection.style.display = "none";
        reportSection.style.display = "block";
      }
    });
  });
});

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
      console.log("Hospitals:", data);
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

  let html = "<h3>Hospitals within 5 km</h3>";

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

// ========== Live location hospitals ==========
function getHospitalsByLiveLocation() {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lon = position.coords.longitude;

      fetch(`/hospitals_by_coords?lat=${lat}&lon=${lon}`)
        .then((res) => res.json())
        .then((data) => {
          displayHospitals(data);
          setTimeout(scrollToHospitals, 150);
        })
        .catch((err) => {
          console.error(err);
          alert("Failed to fetch hospitals");
        });
    },
    () => {
      alert("Location access denied");
    }
  );
}

// ========== Auto scroll ==========
function scrollToHospitals() {
  const section = document.getElementById("hospitalResults");
  if (section) {
    section.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }
}
