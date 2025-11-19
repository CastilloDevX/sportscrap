function init(){
  const search = document.getElementById("searchInput");
  const select = document.getElementById("leagueFilter");
  const table = document.getElementById("eventsTable");
  const refresh = document.getElementById("refreshBtn");
  const loader = document.getElementById("loader");

  const matches = (row, term, league) => {
    const text = row.innerText.toLowerCase();
    const okText = !term || text.includes(term);
    const okLeague = !league || (row.dataset.league || "").toLowerCase() === league;
    return okText && okLeague;
  };

  function applyFilters(){
    const term = (search?.value || "").toLowerCase().trim();
    const league = (select?.value || "").toLowerCase();
    const rows = table?.querySelectorAll("tbody tr") || [];
    rows.forEach(r => {
      r.style.display = matches(r, term, league) ? "" : "none";
    });
  }

  search?.addEventListener("input", applyFilters);
  select?.addEventListener("change", applyFilters);

  // Refrescar (vía fetch a /api/events y re-render rápido)
  refresh?.addEventListener("click", async () => {
    try{
      if (loader) loader.style.display = "flex";
      const res = await fetch("/api/events");
      const data = await res.json();

      const tbody = table.querySelector("tbody");
      tbody.innerHTML = "";

      data.forEach(ev => {
        const tr = document.createElement("tr");
        tr.dataset.league = ev.league || "";
        tr.innerHTML = `
          <td>${formatUtc(ev.start_time)}</td>
          <td>${ev.league || ""}</td>
          <td>${ev.home || ""} vs ${ev.away || ""}</td>
          <td class="text-center">
            ${
              (ev.streams || []).map(s => {
                const lang = (s.language || "").toUpperCase();
                return `
                  <a
                    class="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-2"
                    href="/stream?url=${encodeURIComponent(s.url)}&source=${encodeURIComponent(s.source || "")}"
                  >
                    <span>${escapeHtml(s.name || "Canal")}</span>
                    ${ lang ? `<span class="badge text-bg-dark border">${lang}</span>` : "" }
                  </a>
                `;
              }).join(" ")
            }
          </td>
        `;
        tbody.appendChild(tr);
      });

      applyFilters();
    }catch(e){
      console.error(e);
    }finally{
      if (loader) loader.style.display = "none";
    }
  });

  function formatUtc(ms){
    const d = new Date(Number(ms));
    const pad = n => String(n).padStart(2,"0");
    return `${d.getUTCFullYear()}-${pad(d.getUTCMonth()+1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
  }

  // Pequeña utilidad para evitar inyecciones en nombres de canal
  function escapeHtml(str){
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&alt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
}

window.addEventListener("DOMContentLoaded", init)