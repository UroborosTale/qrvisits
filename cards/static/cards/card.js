document.addEventListener('DOMContentLoaded', () => {
  const share = document.querySelector('[data-share]');
  const status = document.querySelector('.share-status');
  share?.addEventListener('click', async () => {
    const url = share.dataset.share;
    try {
      if (navigator.share) {
        await navigator.share({title: share.dataset.name + ' · КМЗ', url});
      } else if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(url);
        status.textContent = 'Ссылка скопирована';
      } else {
        status.textContent = 'Скопируйте ссылку: ' + url;
      }
    } catch (error) {
      if (error.name !== 'AbortError') status.textContent = 'Скопируйте ссылку: ' + url;
    }
  });
  const dialog = document.querySelector('#qr-dialog');
  document.querySelector('[data-open-qr]')?.addEventListener('click', () => dialog.showModal());
  document.querySelector('[data-close-qr]')?.addEventListener('click', () => dialog.close());
});
