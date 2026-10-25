(function () {
  function attach() {
    const textarea = document.querySelector('#claim-input textarea') || document.querySelector('#claim-input');
    const fileInput = document.querySelector('#image-upload input[type="file"]');
    if (!textarea || !fileInput || textarea.dataset.imagePasteReady) return;
    textarea.dataset.imagePasteReady = 'true';
    textarea.addEventListener('paste', function (event) {
      const items = Array.from((event.clipboardData || {}).items || []);
      const imageItem = items.find((item) => item.type && item.type.startsWith('image/'));
      if (!imageItem) return;
      event.preventDefault();
      const file = imageItem.getAsFile();
      if (!file) return;
      const transfer = new DataTransfer();
      transfer.items.add(file);
      fileInput.files = transfer.files;
      fileInput.dispatchEvent(new Event('change', { bubbles: true }));
      textarea.placeholder = 'Screenshot added. Add any context here, then click Check this message.';
    });
  }
  new MutationObserver(attach).observe(document.body, { childList: true, subtree: true });
  setInterval(attach, 1000);
})();
