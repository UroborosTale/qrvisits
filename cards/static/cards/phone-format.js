(() => {
  const format = (value) => {
    value = value.replace(/\u00a0/g, ' ').trim();
    if (!value) return '';
    if (!/^\+?[0-9 ()-]+$/.test(value)) return null;
    let digits = value.replace(/[^0-9]/g, '');
    if (digits.length === 10 && !value.startsWith('+')) digits = '7' + digits;
    else if (digits.length === 11 && digits.startsWith('8') && !value.startsWith('+')) digits = '7' + digits.slice(1);
    if (digits.length !== 11 || !digits.startsWith('7')) return null;
    return `+7 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7, 9)}-${digits.slice(9)}`;
  };
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-phone-format]').forEach(input => {
      const update = () => {
        const formatted = format(input.value);
        if (formatted !== null) input.value = formatted;
        return formatted;
      };
      update();
      input.addEventListener('input', () => {
        input.setCustomValidity('');
        const raw = input.value.trim();
        // Do not interpret a partially typed 11-digit trunk number as 10 digits.
        if (!raw.startsWith('+') && /^[78]/.test(raw) && raw.replace(/\D/g, '').length === 10) return;
        update();
      });
      input.addEventListener('paste', event => {
        const text = event.clipboardData?.getData('text');
        if (!text) return;
        const combined = input.value.slice(0, input.selectionStart) + text + input.value.slice(input.selectionEnd);
        const formatted = format(combined);
        if (formatted !== null) {
          event.preventDefault(); input.value = formatted; input.setCustomValidity('');
        }
      });
      input.addEventListener('blur', () => {
        input.setCustomValidity(update() === null ? 'Введите полный номер: +7 (XXX) XXX-XX-XX.' : '');
      });
    });
  });
})();
