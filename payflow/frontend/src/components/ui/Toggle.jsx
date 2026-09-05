export default function Toggle({ checked, onChange, label }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-10 shrink-0 items-center rounded-full transition-colors duration-150 ${
        checked ? 'bg-[var(--color-success-600)]' : 'bg-[var(--color-line)]'
      }`}
    >
      <span
        className={`inline-block h-4.5 w-4.5 transform rounded-full bg-white shadow transition-transform duration-150 ${
          checked ? 'translate-x-[19px]' : 'translate-x-[3px]'
        }`}
      />
    </button>
  );
}
