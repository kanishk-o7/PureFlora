document.addEventListener("click", (event) => {
  const opener = event.target.closest("[data-dialog-open]");
  if (opener) {
    const dialog = document.getElementById(opener.dataset.dialogOpen);
    if (dialog && typeof dialog.showModal === "function") dialog.showModal();
    return;
  }

  const closer = event.target.closest("[data-dialog-close]");
  if (closer) closer.closest("dialog")?.close();
});

document.querySelectorAll(".cancel-confirmation-dialog").forEach((dialog) => {
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });
});
