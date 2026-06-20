/* ===========================================================================
   script.js
   ---------------------------------------------------------------------------
   This file runs in the browser. It:
     - calls our Flask API with fetch()
     - draws the charts with Chart.js
     - handles search, sorting, CSV export, dark mode, and refresh
   Everything is plain ("vanilla") JavaScript — no frameworks.
   =========================================================================== */

// ---------------------------------------------------------------------------
// Keep references to the Chart.js chart objects so we can destroy & redraw
// them whenever the data changes (e.g. after a refresh).
// ---------------------------------------------------------------------------
let topChart, bottomChart, donutChart, deptChart;

// We store the latest reviews and current sort direction for the table.
let allReviews = [];
let scoreSortAscending = false; // false = highest score first

// Grab DOM elements once so we don't look them up repeatedly.
const statusMessage = document.getElementById("statusMessage");

// ===========================================================================
// SMALL HELPERS
// ===========================================================================

// Show a temporary message in the status line.
function setStatus(message) {
  statusMessage.textContent = message;
}

// Pick a nice color for a score: green if positive, red if negative, amber otherwise.
function colorForScore(score) {
  if (score >= 0.05) return "#22c55e";
  if (score <= -0.05) return "#ef4444";
  return "#f59e0b";
}

// ===========================================================================
// LOADING DATA
// ===========================================================================

// Fetch /stats from the backend and refresh the WHOLE dashboard.
async function loadStats() {
  setStatus("Loading dashboard…");
  try {
    const response = await fetch("/stats");
    const data = await response.json();

    // Update the three summary cards.
    document.getElementById("totalReviews").textContent = data.total_reviews;
    document.getElementById("totalProfessors").textContent = data.total_professors;
    const positivePct = data.total_reviews
      ? Math.round((data.distribution.Positive / data.total_reviews) * 100)
      : 0;
    document.getElementById("positivePct").textContent = positivePct + "%";

    // Save reviews for the table + sorting, then draw everything.
    allReviews = data.reviews;
    renderTopChart(data.top_5);
    renderBottomChart(data.bottom_5);
    renderDonutChart(data.distribution);
    renderDeptChart(data.department_averages);
    renderTable();

    setStatus("");
  } catch (error) {
    setStatus("Could not load data. Is the server running?");
    console.error(error);
  }
}

// ===========================================================================
// CHARTS
// Each function destroys the old chart (if any) and draws a fresh one, so the
// charts always re-render correctly after a data refresh.
// ===========================================================================

// --- Top 5 professors (vertical bar chart) --------------------------------
function renderTopChart(top5) {
  const labels = top5.map((p) => p.name);
  const scores = top5.map((p) => p.average_score);

  if (topChart) topChart.destroy();
  topChart = new Chart(document.getElementById("topChart"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Average sentiment",
        data: scores,
        backgroundColor: "#22c55e",
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

// --- Bottom 5 professors (vertical bar chart) -----------------------------
function renderBottomChart(bottom5) {
  const labels = bottom5.map((p) => p.name);
  const scores = bottom5.map((p) => p.average_score);

  if (bottomChart) bottomChart.destroy();
  bottomChart = new Chart(document.getElementById("bottomChart"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Average sentiment",
        data: scores,
        backgroundColor: "#ef4444",
      }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

// --- Overall sentiment distribution (donut chart) -------------------------
function renderDonutChart(distribution) {
  if (donutChart) donutChart.destroy();
  donutChart = new Chart(document.getElementById("donutChart"), {
    type: "doughnut",
    data: {
      labels: ["Positive", "Neutral", "Negative"],
      datasets: [{
        data: [
          distribution.Positive,
          distribution.Neutral,
          distribution.Negative,
        ],
        backgroundColor: ["#22c55e", "#f59e0b", "#ef4444"],
      }],
    },
    options: { responsive: true },
  });
}

// --- Department averages (horizontal bar chart) ---------------------------
function renderDeptChart(deptAverages) {
  const labels = deptAverages.map((d) => d.department);
  const scores = deptAverages.map((d) => d.average_score);

  if (deptChart) deptChart.destroy();
  deptChart = new Chart(document.getElementById("deptChart"), {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Average sentiment",
        data: scores,
        // Color each bar based on whether the department leans positive/negative.
        backgroundColor: scores.map(colorForScore),
      }],
    },
    options: {
      indexAxis: "y", // this makes the bars horizontal
      responsive: true,
      plugins: { legend: { display: false } },
    },
  });
}

// ===========================================================================
// REVIEWS TABLE
// ===========================================================================

// Build the table rows from allReviews (respecting the current sort order).
function renderTable() {
  const tbody = document.getElementById("reviewsBody");
  tbody.innerHTML = ""; // clear existing rows

  // Make a sorted copy so we don't mutate the original array.
  const sorted = [...allReviews].sort((a, b) =>
    scoreSortAscending
      ? a.sentiment_score - b.sentiment_score
      : b.sentiment_score - a.sentiment_score
  );

  // Create one <tr> per review.
  sorted.forEach((review) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${review.professor}</td>
      <td>${review.department}</td>
      <td>${review.text}</td>
      <td>${review.sentiment_score.toFixed(3)}</td>
      <td><span class="badge ${review.sentiment_label}">${review.sentiment_label}</span></td>
    `;
    tbody.appendChild(row);
  });
}

// ===========================================================================
// SEARCH
// ===========================================================================

async function searchProfessor() {
  const name = document.getElementById("searchInput").value.trim();
  const resultsDiv = document.getElementById("searchResults");

  if (!name) {
    resultsDiv.innerHTML = "<p>Please type a professor name first.</p>";
    return;
  }

  resultsDiv.innerHTML = "<p>Searching…</p>";

  try {
    const response = await fetch("/professors/" + encodeURIComponent(name));

    if (response.status === 404) {
      resultsDiv.innerHTML = `<p>No professor found matching "${name}".</p>`;
      return;
    }

    const data = await response.json();
    const prof = data.professor;

    // Build a small summary + a list of all their reviews.
    let html = `
      <h3>${prof.name} — ${prof.department}</h3>
      <p>${prof.review_count} reviews · average score
         <strong>${prof.average_score.toFixed(3)}</strong></p>
    `;

    data.reviews.forEach((r) => {
      html += `
        <div class="review-item">
          <div>${r.text}</div>
          <div class="meta">
            Score: ${r.sentiment_score.toFixed(3)} ·
            <span class="badge ${r.sentiment_label}">${r.sentiment_label}</span>
          </div>
        </div>
      `;
    });

    resultsDiv.innerHTML = html;
  } catch (error) {
    resultsDiv.innerHTML = "<p>Something went wrong with the search.</p>";
    console.error(error);
  }
}

// ===========================================================================
// REFRESH (re-run the scraper on the server)
// ===========================================================================

async function refreshData() {
  setStatus("Refreshing data — re-running the scraper…");
  try {
    // POST to /scrape tells the backend to re-scrape and re-analyze.
    const response = await fetch("/scrape", { method: "POST" });
    const data = await response.json();
    setStatus(data.message);

    // Reload all the charts and the table with the fresh data.
    await loadStats();
  } catch (error) {
    setStatus("Refresh failed. Check the server.");
    console.error(error);
  }
}

// ===========================================================================
// DARK MODE (saved to localStorage so it persists between visits)
// ===========================================================================

function applySavedTheme() {
  const saved = localStorage.getItem("theme");
  if (saved === "dark") {
    document.body.classList.add("dark");
    document.getElementById("themeBtn").textContent = "☀️ Light Mode";
  }
}

function toggleTheme() {
  document.body.classList.toggle("dark");
  const isDark = document.body.classList.contains("dark");

  // Remember the choice for next time.
  localStorage.setItem("theme", isDark ? "dark" : "light");
  document.getElementById("themeBtn").textContent =
    isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
}

// ===========================================================================
// WIRING UP THE BUTTONS (event listeners)
// This runs once when the page loads.
// ===========================================================================

document.getElementById("refreshBtn").addEventListener("click", refreshData);
document.getElementById("searchBtn").addEventListener("click", searchProfessor);
document.getElementById("themeBtn").addEventListener("click", toggleTheme);

// Allow pressing Enter in the search box to trigger a search.
document.getElementById("searchInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") searchProfessor();
});

// Export button just navigates to /export, which downloads the CSV file.
document.getElementById("exportBtn").addEventListener("click", () => {
  window.location.href = "/export";
});

// Clicking the Score column header flips the sort direction and redraws.
document.getElementById("scoreHeader").addEventListener("click", () => {
  scoreSortAscending = !scoreSortAscending;
  renderTable();
});

// ===========================================================================
// START EVERYTHING
// ===========================================================================
applySavedTheme(); // apply dark mode before anything is shown
loadStats();       // load the dashboard data
