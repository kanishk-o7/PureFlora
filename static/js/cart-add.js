document.addEventListener("submit", async (event) => {
  const form = event.target.closest('form[action*="/cart/add/"]');
  if (!form) return;

  event.preventDefault();
  const button = form.querySelector('button[type="submit"], button:not([type])');
  if (button?.disabled) return;
  if (button) button.disabled = true;

  try {
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { "X-Requested-With": "XMLHttpRequest" },
      credentials: "same-origin",
    });
    if (response.redirected) {
      window.location.assign(response.url);
      return;
    }
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.message || "Could not add this flower.");

    document.querySelectorAll("[data-cart-count]").forEach((badge) => {
      badge.textContent = result.cart_count;
    });
    const toast = document.getElementById("toast");
    if (toast) {
      toast.textContent = result.message;
      toast.classList.add("show");
      window.setTimeout(() => toast.classList.remove("show"), 2200);
    }
  } catch (error) {
    const toast = document.getElementById("toast");
    if (toast) {
      toast.textContent = error.message;
      toast.classList.add("show");
      window.setTimeout(() => toast.classList.remove("show"), 3000);
    }
  } finally {
    if (button?.isConnected) button.disabled = false;
  }
});
