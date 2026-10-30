(() => {
  const $ = window.PF.$;
  const grid = $("#allProducts"), search = $("#productSearch"), range = $("#priceRange"), priceValue = $("#priceValue");
  const stock = $("#inStockOnly"), sort = $("#sortSelect"), count = $("#resultCount");
  const getCategory = () => document.querySelector('input[name="category"]:checked')?.value || "All";
  function render() {
    let list = window.PF.products();
    const query = (search.value || "").trim().toLowerCase();
    const category = getCategory(), maxPrice = Number(range.value);
    list = list.filter(p => {
      const matchesText = [p.name,p.category,p.grower,p.description].join(" ").toLowerCase().includes(query);
      return matchesText && (category === "All" || p.category === category) && p.price <= maxPrice && (!stock.checked || p.stock > 0);
    });
    if (sort.value === "price-asc") list.sort((a,b) => a.price-b.price);
    if (sort.value === "price-desc") list.sort((a,b) => b.price-a.price);
    if (sort.value === "name") list.sort((a,b) => a.name.localeCompare(b.name));
    grid.innerHTML = list.map(p => window.PF.productCard(p)).join("");
    count.textContent = `Showing ${list.length} ${list.length === 1 ? "flower" : "flowers"}`;
    $("#emptyProducts").classList.toggle("hidden", list.length > 0);
    grid.classList.toggle("hidden", list.length === 0);
    window.PF.bindProductActions(grid);
  }
  function clear() {
    search.value = ""; range.value = 1000; priceValue.textContent = window.PF.format(1000);
    stock.checked = false; sort.value = "featured";
    document.querySelector('input[name="category"][value="All"]').checked = true;
    render();
  }
  search.addEventListener("input", render);
  range.addEventListener("input", () => { priceValue.textContent = window.PF.format(Number(range.value)); render(); });
  stock.addEventListener("change", render); sort.addEventListener("change", render);
  document.querySelectorAll('input[name="category"]').forEach(input => input.addEventListener("change", render));
  $("#clearFilters").addEventListener("click", clear); $("#emptyClear").addEventListener("click", clear);
  const params = new URLSearchParams(location.search), category = params.get("category");
  if (category) {
    const option = document.querySelector(`input[name="category"][value="${CSS.escape(category)}"]`);
    if (option) option.checked = true;
  }
  if (location.hash === "#catalog") $("#productSearch").focus();
  render();
  window.addEventListener("pf:products-updated", render);
})();
