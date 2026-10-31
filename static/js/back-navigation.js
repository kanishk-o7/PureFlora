(() => {
  const mount = () => {
    if (document.querySelector('[data-site-back]')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'site-back-button';
    button.dataset.siteBack = '';
    button.setAttribute('aria-label', 'Go back to the previous page');
    button.innerHTML = '<span aria-hidden="true">←</span> Back';
    button.addEventListener('click', () => {
      let sameSiteReferrer = false;
      try {
        sameSiteReferrer = Boolean(document.referrer) && new URL(document.referrer).origin === window.location.origin;
      } catch (_) {}
      if (sameSiteReferrer && window.history.length > 1) window.history.back();
      else window.location.assign('/');
    });
    const main = document.querySelector('main');
    if (main) main.insertBefore(button, main.firstChild);
    else document.body.insertBefore(button, document.body.firstChild);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount, { once: true });
  else mount();
})();
