// Filtros + paginación por proveedor
(function () {
  const searchInput = document.getElementById("searchInput");
  const providerFilter = document.getElementById("providerFilter");

  // Inicializar paginación por proveedor
  document.querySelectorAll(".provider-block").forEach(block => {
    const table = block.querySelector(".provider-table");
    if (!table) return;

    const rows = Array.from(table.querySelectorAll("tbody tr"));
    const pageSize = parseInt(table.dataset.pageSize || "10", 10);
    const controls = block.querySelector(".pagination-controls");
    if (!rows.length || !controls) return;

    const prevBtn = controls.querySelector(".prev-page");
    const nextBtn = controls.querySelector(".next-page");
    const pageInfo = controls.querySelector(".page-info");

    const state = {
      rows,
      pageSize,
      currentPage: 1,
      totalPages: Math.max(1, Math.ceil(rows.length / pageSize)),
    };

    function renderPage() {
      const { rows, pageSize, currentPage } = state;

      rows.forEach((row, idx) => {
        const pageIndex = Math.floor(idx / pageSize) + 1;
        row.style.display = pageIndex === currentPage ? "" : "none";
      });

      pageInfo.textContent = `Página ${state.currentPage} de ${state.totalPages}`;
      prevBtn.disabled = state.currentPage === 1;
      nextBtn.disabled = state.currentPage === state.totalPages;
    }

    prevBtn.addEventListener("click", () => {
      if (state.currentPage > 1) {
        state.currentPage -= 1;
        renderPage();
      }
    });

    nextBtn.addEventListener("click", () => {
      if (state.currentPage < state.totalPages) {
        state.currentPage += 1;
        renderPage();
      }
    });

    // Guardar referencia
    block._pagination = { state, renderPage, controls };
    renderPage();
  });

  // Filtro principal (búsqueda + proveedor)
  function applyFilters() {
    const term = (searchInput?.value || "").toLowerCase().trim();
    const selectedProvider = providerFilter?.value || "";

    document.querySelectorAll(".provider-block").forEach(block => {
      const blockProvider = block.dataset.provider || "";
      const matchProvider = !selectedProvider || selectedProvider === blockProvider;

      // Mostrar/ocultar bloque por proveedor
      block.style.display = matchProvider ? "" : "none";
      if (!matchProvider) return;

      const rows = Array.from(block.querySelectorAll("tbody tr"));
      const pagination = block._pagination;

      // -------------- SIN BÚSQUEDA --------------
      if (!term) {
        rows.forEach(r => (r.style.display = "")); // reset

        if (pagination) {
          pagination.controls.style.display = "flex"; // mostrar paginación normal
          pagination.state.totalPages = Math.max(1, Math.ceil(rows.length / pagination.state.pageSize));
          pagination.state.currentPage = 1;
          pagination.renderPage();
        }
        return;
      }

      // -------------- CON BÚSQUEDA --------------
      rows.forEach(r => {
        const text = r.innerText.toLowerCase();
        r.style.display = text.includes(term) ? "" : "none";
      });

      // ocultar completamente la paginación
      if (pagination) {
        pagination.controls.style.display = "none";
      }
    });
  }

  searchInput?.addEventListener("input", applyFilters);
  providerFilter?.addEventListener("change", applyFilters);
})();
