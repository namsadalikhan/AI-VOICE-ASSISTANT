const pingButton = document.getElementById("ping-button");
const statusLabel = document.getElementById("status");
const results = document.getElementById("results");

const setStatus = (message) => {
  statusLabel.textContent = message;
};

const renderResults = (items) => {
  results.innerHTML = "";

  if (!items.length) {
    results.innerHTML = '<p class="error">No responding hosts found.</p>';
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "result";

    const host = document.createElement("span");
    host.textContent = item.host;

    const badge = document.createElement("span");
    badge.className = `badge ${item.alive ? "up" : "down"}`;
    badge.textContent = item.alive ? "ONLINE" : "OFFLINE";

    card.appendChild(host);
    card.appendChild(badge);
    results.appendChild(card);
  });
};

const renderError = (message) => {
  results.innerHTML = `<p class="error">${message}</p>`;
};

pingButton.addEventListener("click", async () => {
  const ip = document.getElementById("ip").value.trim();
  const subnet = document.getElementById("subnet").value.trim();

  if (!ip || !subnet) {
    renderError("Please enter both an IP address and subnet prefix.");
    return;
  }

  pingButton.disabled = true;
  setStatus("Scanning... deploying probes.");
  results.innerHTML = "";

  try {
    const response = await fetch("/api/ping", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ip, subnet }),
    });

    const payload = await response.json();

    if (!response.ok) {
      renderError(payload.error || "Ping sweep failed.");
      setStatus("Awaiting command...");
      return;
    }

    renderResults(payload.results || []);
    setStatus(
      `Sweep complete for ${payload.network} (${payload.alive_count || 0} up)`
    );
  } catch (error) {
    renderError("Unable to reach the ping service.");
    setStatus("Awaiting command...");
  } finally {
    pingButton.disabled = false;
  }
});
