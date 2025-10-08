// Mobile nav toggle
const hambA = document.getElementById('hambA');
const navA = document.getElementById('navA');
if (hambA) { hambA.addEventListener('click', () => { const open = getComputedStyle(navA).display === 'none'; navA.style.display = open ? 'flex' : 'none'; hambA.setAttribute('aria-expanded', String(open)); }); }

// Client-side filter
const qA = document.getElementById('qA');
const qABtn = document.getElementById('qABtn');
const gridA = document.getElementById('featuredA');
function filterA() { const q = (qA?.value || '').toLowerCase(); gridA?.querySelectorAll('.card').forEach(c => { const t = (c.querySelector('.p-title')?.textContent || '').toLowerCase(); const s = (c.querySelector('.muted')?.textContent || '').toLowerCase(); c.style.display = (t + s).includes(q) ? '' : 'none'; }); }
qABtn?.addEventListener('click', filterA); qA?.addEventListener('keydown', e => { if (e.key === 'Enter') filterA(); });

// Testimonials auto-scroll
const trowA = document.getElementById('trowA');
if (trowA) { let x = 0; setInterval(() => { x += 240; if (x > trowA.scrollWidth - trowA.clientWidth) x = 0; trowA.scrollTo({ left: x, behavior: 'smooth' }); }, 3500); }

