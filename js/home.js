(() => {
  const grid = document.getElementById("featuredProducts");
  function render() {
    if (!grid) return;
    const featured = window.PF.products().filter(p => ["rose-blush", "lily-white", "marigold-gold", "tulip-pink"].includes(p.id));
    grid.innerHTML = featured.map(p => window.PF.productCard(p)).join("");
    window.PF.bindProductActions(grid);
  }
  if (grid) {
    render();
    window.addEventListener("pf:products-updated", render);
  }
  const form = document.getElementById("newsletterForm");
  if (form) form.addEventListener("submit", event => {
    event.preventDefault();
    const email = document.getElementById("newsletterEmail").value.trim();
    const subscribers = window.PF.get("subscribers", []);
    if (!subscribers.includes(email)) subscribers.push(email);
    window.PF.set("subscribers", subscribers);
    document.getElementById("newsletterMessage").textContent = "You're on the list — thanks for growing with us!";
    form.reset();
  });
})();
