(() => {
  const $ = window.PF.$;
  const itemsEl = $("#cartItems");
  function render() {
    const cart = window.PF.cart(), products = window.PF.products();
    const items = cart.map(item => ({...item, product:products.find(p=>p.id===item.id)})).filter(x=>x.product);
    const quantity = items.reduce((sum,item)=>sum+item.qty,0);
    $("#cartItemCount").textContent = `(${quantity} ${quantity===1?"item":"items"})`;
    if (!items.length) {
      itemsEl.innerHTML = `<div class="empty-cart"><span>✿</span><h3>Your bag is waiting for a little beauty.</h3><p>Explore the collection and add flowers you love.</p><a class="button button-dark" href="products.html">Browse flowers ↗</a></div>`;
    } else {
      itemsEl.innerHTML = items.map(({product,qty}) => `<article class="cart-item"><img src="${product.image}" alt="${product.name}" onerror="this.style.opacity='.2'"><div class="cart-item-info"><span class="eyebrow">${product.category}</span><h3>${product.name}</h3><p>${product.unit} · ${product.grower}</p><button class="remove-link" data-remove="${product.id}">Remove</button></div><div class="cart-item-price"><strong>${window.PF.format(product.price*qty)}</strong><div class="quantity-control"><button data-qty="${product.id}" data-delta="-1" aria-label="Decrease quantity">−</button><span>${qty}</span><button data-qty="${product.id}" data-delta="1" aria-label="Increase quantity">＋</button></div></div></article>`).join("");
    }
    const subtotal = items.reduce((sum,item)=>sum+item.product.price*item.qty,0);
    const delivery = subtotal === 0 || subtotal >= 3000 ? 0 : 120;
    const savings = subtotal >= 5000 ? Math.round(subtotal*.05) : 0;
    $("#cartSubtotal").textContent = window.PF.format(subtotal);
    $("#cartDelivery").textContent = delivery ? window.PF.format(delivery) : "Free";
    $("#cartSavings").textContent = "−"+window.PF.format(savings);
    $("#cartTotal").textContent = window.PF.format(subtotal+delivery-savings);
    $("#checkoutButton").disabled = !items.length;
    window.PF.updateCartCount();
    itemsEl.querySelectorAll("[data-qty]").forEach(btn => btn.addEventListener("click",()=>{
      const id=btn.dataset.qty, delta=Number(btn.dataset.delta), cart=window.PF.cart(), item=cart.find(x=>x.id===id);
      if (!item) return;
      const product=products.find(p=>p.id===id);
      item.qty=Math.min(product.stock,item.qty+delta);
      if(item.qty<1) { window.PF.updateCart(cart.filter(x=>x.id!==id)); } else window.PF.updateCart(cart);
      render();
    }));
    itemsEl.querySelectorAll("[data-remove]").forEach(btn=>btn.addEventListener("click",()=>{
      window.PF.updateCart(window.PF.cart().filter(x=>x.id!==btn.dataset.remove)); render(); window.PF.toast("Flower removed from your bag.");
    }));
  }
  $("#checkoutButton").addEventListener("click",()=>{
    const cart=window.PF.cart();
    if(!cart.length) return;
    const orderId="PF-"+Math.floor(3000+Math.random()*6000);
    const order={id:orderId,items:cart,created:new Date().toISOString(),status:"confirmed"};
    const orders=window.PF.get("orders",[]); orders.unshift(order); window.PF.set("orders",orders);
    window.PF.set("lastOrder",order);
    window.PF.updateCart([]);
    window.PF.toast(`Demo order placed! Your ID is ${orderId}`);
    setTimeout(()=>location.href="tracking.html?order="+encodeURIComponent(orderId),900);
    render();
  });
  render();
  window.addEventListener("pf:products-updated", render);
})();
