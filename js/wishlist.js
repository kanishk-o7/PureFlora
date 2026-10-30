(() => {
  const grid=document.getElementById("wishlistProducts"), empty=document.getElementById("wishlistEmpty");
  function render() {
    const ids=window.PF.wishlist(), products=window.PF.products().filter(p=>ids.includes(p.id));
    grid.innerHTML=products.map(p=>window.PF.productCard(p)).join("");
    empty.classList.toggle("hidden",products.length>0);
    grid.classList.toggle("hidden",products.length===0);
    window.PF.bindProductActions(grid);
    grid.querySelectorAll("[data-wishlist]").forEach(button=>button.addEventListener("click",()=>setTimeout(render,0)));
  }
  render();
  window.addEventListener("pf:products-updated", render);
})();
