const incomeInput = document.getElementById('income');
const incomeSlider = document.getElementById('income-slider');

const gbp = (n) => new Intl.NumberFormat('en-GB', {
  style: 'currency', currency: 'GBP', maximumFractionDigits: 0,
}).format(n);

const pct = (r) => `${Math.round(r * 100)}%`;

function renderTable(tbodyId, bands) {
  const tbody = document.querySelector(`#${tbodyId} tbody`);
  tbody.innerHTML = '';
  if (!bands.length) {
    tbody.innerHTML = `<tr class="empty-row"><td colspan="4">Below the Personal Allowance — no income tax due.</td></tr>`;
    return;
  }
  for (const band of bands) {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${band.name}</td>
      <td class="rate-cell">${pct(band.rate)}</td>
      <td class="mono">${gbp(band.taxed_amount)}</td>
      <td class="mono">${gbp(band.tax_due)}</td>
    `;
    tbody.appendChild(row);
  }
}

function renderRegion(prefix, tableId, result) {
  renderTable(tableId, result.bands);
  document.getElementById(`${prefix}-allowance`).textContent = gbp(result.personal_allowance);
  document.getElementById(`${prefix}-tax`).textContent = gbp(result.total_tax);
  document.getElementById(`${prefix}-takehome`).textContent = gbp(result.take_home);
}

function renderBadge(difference) {
  const badge = document.getElementById('border-badge');
  const amountEl = document.getElementById('badge-amount');
  const directionEl = document.getElementById('badge-direction');

  badge.classList.remove('favours-ruk', 'favours-scotland');

  if (Math.abs(difference) < 0.5) {
    amountEl.textContent = gbp(0);
    directionEl.textContent = 'no difference';
    return;
  }

  // difference = scotland.total_tax - ruk.total_tax
  // positive difference -> Scotland pays more -> rUK take-home wins
  if (difference > 0) {
    badge.classList.add('favours-ruk');
    amountEl.textContent = gbp(difference);
    directionEl.textContent = 'more take-home in rUK';
  } else {
    badge.classList.add('favours-scotland');
    amountEl.textContent = gbp(Math.abs(difference));
    directionEl.textContent = 'more take-home in Scotland';
  }
}

let debounceTimer = null;

async function updateCalculation(income) {
  if (Number.isNaN(income) || income < 0) return;

  try {
    const res = await fetch(`/api/calculate?income=${income}`);
    if (!res.ok) throw new Error('API error');
    const data = await res.json();

    renderRegion('ruk', 'table-ruk', data.ruk);
    renderRegion('scotland', 'table-scotland', data.scotland);
    renderBadge(data.difference);
  } catch (err) {
    console.error('Failed to fetch tax calculation:', err);
  }
}

function handleIncomeChange(value) {
  const income = parseFloat(value);
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => updateCalculation(income), 150);
}

incomeInput.addEventListener('input', (e) => {
  incomeSlider.value = Math.min(e.target.value, incomeSlider.max);
  handleIncomeChange(e.target.value);
});

incomeSlider.addEventListener('input', (e) => {
  incomeInput.value = e.target.value;
  handleIncomeChange(e.target.value);
});

// Initial render on page load
updateCalculation(parseFloat(incomeInput.value));
