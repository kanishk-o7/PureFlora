(() => {
  const $=window.PF.$, result=$("#trackingResult"), form=$("#trackingForm");
  const defaultResult=result.innerHTML;
  function showOrder(id) {
    const orders=window.PF.get("orders",[]);
    const order=orders.find(o=>o.id.toUpperCase()===id.toUpperCase());
    if(id.toUpperCase()==="PF-2048") {
      result.innerHTML=defaultResult; result.classList.remove("hidden"); $("#trackingError").textContent=""; return;
    }
    if(order) {
      const products=window.PF.products();
      const orderItems=order.items.map(item=>{const p=products.find(x=>x.id===item.id);return p?`${p.name} · ${item.qty} bunches`:null;}).filter(Boolean);
      result.innerHTML=`<div class="tracking-result-top"><div><span class="eyebrow">ORDER ${order.id}</span><h2>Your order is confirmed.</h2></div><span class="status-pill status-progress">Confirmed</span></div><p class="tracking-delivery">Estimated arrival <strong>Within 2–4 business days (demo estimate)</strong></p><div class="timeline"><div class="timeline-step complete"><span class="timeline-marker">✓</span><div><strong>Order confirmed</strong><p>Your demo order has been created in this browser.</p><small>${new Date(order.created).toLocaleString()}</small></div></div><div class="timeline-step current"><span class="timeline-marker">✿</span><div><strong>Grower preparation</strong><p>Sample status — live delivery updates are not connected.</p></div></div><div class="timeline-step"><span class="timeline-marker">3</span><div><strong>Out for delivery</strong><p>Your order is on its way to you.</p></div></div><div class="timeline-step"><span class="timeline-marker">4</span><div><strong>Delivered with care</strong><p>Time to make something beautiful.</p></div></div></div><div class="tracking-order-items"><strong>In this order</strong>${orderItems.map(s=>`<div><span>${s}</span></div>`).join("")}</div>`;
      result.classList.remove("hidden"); $("#trackingError").textContent=""; return;
    }
    result.classList.add("hidden"); $("#trackingError").textContent="We couldn't find that order in this demo. Try PF-2048 or an order created from your bag in this browser.";
  }
  form.addEventListener("submit",event=>{event.preventDefault();showOrder($("#orderNumber").value.trim());});
  $("#sampleOrder").addEventListener("click",()=>{$("#orderNumber").value="PF-2048";showOrder("PF-2048");});
  const query=new URLSearchParams(location.search).get("order");
  if(query){$("#orderNumber").value=query;showOrder(query);}
  window.addEventListener("pf:products-updated", () => {
    const currentOrder = $("#orderNumber").value.trim();
    if (currentOrder) showOrder(currentOrder);
  });
})();
