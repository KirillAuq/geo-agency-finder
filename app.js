/* GEO Agency Finder — filtering, sorting, rendering. No dependencies. */
(function () {
  'use strict';

  var state = {
    q: '',
    region: 'all',
    type: 'all',
    budget: 'any',
    focus: 'any',
    publishedOnly: false,
    sort: 'best'
  };

  var els = {};

  function $(id) { return document.getElementById(id); }

  function fmtPrice(a) {
    if (a.priceMonthlyUSD) {
      return 'From $' + a.priceMonthlyUSD.toLocaleString('en-US') + '/mo';
    }
    return 'Pricing on request';
  }

  function matches(a) {
    if (state.q) {
      var q = state.q.toLowerCase();
      var hay = (a.name + ' ' + (a.city || '') + ' ' + (a.country || '')).toLowerCase();
      if (hay.indexOf(q) === -1) return false;
    }
    if (state.region !== 'all' && a.region !== state.region) return false;
    if (state.type === 'specialist' && !a.specialist) return false;
    if (state.type === 'wider' && a.specialist) return false;
    if (state.publishedOnly && !a.priceMonthlyUSD) return false;
    if (state.budget !== 'any') {
      var cap = parseInt(state.budget, 10);
      // Agencies without a published price stay visible under every budget,
      // same as the filter being about published prices only when toggled.
      if (a.priceMonthlyUSD && a.priceMonthlyUSD > cap) return false;
    }
    if (state.focus !== 'any' && a.services.indexOf(state.focus) === -1) return false;
    return true;
  }

  function sortList(list) {
    var sorted = list.slice();
    if (state.sort === 'priceAsc' || state.sort === 'priceDesc') {
      sorted.sort(function (a, b) {
        var pa = a.priceMonthlyUSD, pb = b.priceMonthlyUSD;
        if (pa == null && pb == null) return a.name.localeCompare(b.name);
        if (pa == null) return 1; // unpublished prices sink to the bottom
        if (pb == null) return -1;
        return state.sort === 'priceAsc' ? pa - pb : pb - pa;
      });
    } else {
      // Best match: specialists first, then breadth of GEO services, then name.
      sorted.sort(function (a, b) {
        if (a.specialist !== b.specialist) return a.specialist ? -1 : 1;
        var sa = a.services.length, sb = b.services.length;
        if (sa !== sb) return sb - sa;
        return a.name.localeCompare(b.name);
      });
    }
    return sorted;
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function card(a) {
    var loc = [a.city, a.country].filter(Boolean).join(', ') || a.region;
    var tags = a.services.map(function (s) {
      return '<span class="tag">' + esc(s) + '</span>';
    }).join('');
    var clients = a.clients && a.clients.length
      ? '<p class="clients"><span class="mono-label">Clients include</span> ' + esc(a.clients.join(', ')) + '</p>'
      : '';
    var badge = a.specialist ? '<span class="badge">GEO specialist</span>' : '';
    var disclosure = a.disclosure ? '<span class="badge badge-note">' + esc(a.disclosure) + '</span>' : '';
    var profileUrl = 'agencies/' + esc(a.slug) + '/';
    return '<article class="card">' +
      '<div class="card-top">' +
        '<div>' +
          '<h3><a class="card-title" href="' + profileUrl + '">' + esc(a.name) + '</a></h3>' +
          '<p class="loc">' + esc(loc) + '</p>' +
        '</div>' +
        '<div class="card-badges">' + badge + disclosure + '</div>' +
      '</div>' +
      '<p class="price">' + esc(fmtPrice(a)) + '</p>' +
      '<p class="desc">' + esc(a.description) + '</p>' +
      '<div class="tags">' + tags + '</div>' +
      clients +
      '<div class="card-foot">' +
        '<a class="visit" href="' + profileUrl + '">Profile &rarr;</a>' +
        '<a class="visit" href="' + esc(a.website) + '" target="_blank" rel="noopener nofollow">Visit site &nearr;</a>' +
      '</div>' +
    '</article>';
  }

  function render() {
    var list = sortList(AGENCIES.filter(matches));
    els.count.textContent = list.length + ' of ' + AGENCIES.length + ' agencies';
    if (!list.length) {
      els.results.innerHTML = '<div class="empty"><p>No agencies match these filters.</p>' +
        '<p class="caption">Loosen the budget or focus filter. Agencies without published prices are hidden when "Published prices only" is on.</p></div>';
      return;
    }
    els.results.innerHTML = list.map(card).join('');
  }

  function populateRegions() {
    var counts = {};
    AGENCIES.forEach(function (a) { counts[a.region] = (counts[a.region] || 0) + 1; });
    var order = ['United States', 'Canada', 'United Kingdom', 'Europe', 'Asia-Pacific',
                 'Latin America', 'Africa & Middle East', 'Remote / no HQ listed'];
    order.forEach(function (r) {
      if (!counts[r]) return;
      var o = document.createElement('option');
      o.value = r;
      o.textContent = r + ' (' + counts[r] + ')';
      els.region.appendChild(o);
    });
    var sp = AGENCIES.filter(function (a) { return a.specialist; }).length;
    els.type.options[1].textContent = 'GEO specialists (' + sp + ')';
    els.type.options[2].textContent = 'Wider agencies (' + (AGENCIES.length - sp) + ')';
    // Focus counts
    Array.prototype.forEach.call(els.focus.options, function (o) {
      if (o.value === 'any') return;
      var n = AGENCIES.filter(function (a) { return a.services.indexOf(o.value) !== -1; }).length;
      o.textContent = o.value + ' (' + n + ')';
    });
    var total = document.getElementById('total-count');
    if (total) total.textContent = String(AGENCIES.length);
  }

  function bind() {
    els.q.addEventListener('input', function () { state.q = this.value.trim(); render(); });
    els.region.addEventListener('change', function () { state.region = this.value; render(); });
    els.type.addEventListener('change', function () { state.type = this.value; render(); });
    els.budget.addEventListener('change', function () { state.budget = this.value; render(); });
    els.focus.addEventListener('change', function () { state.focus = this.value; render(); });
    els.sort.addEventListener('change', function () { state.sort = this.value; render(); });
    els.published.addEventListener('change', function () { state.publishedOnly = this.checked; render(); });
    els.clear.addEventListener('click', function () {
      state = { q: '', region: 'all', type: 'all', budget: 'any', focus: 'any', publishedOnly: false, sort: 'best' };
      els.q.value = ''; els.region.value = 'all'; els.type.value = 'all';
      els.budget.value = 'any'; els.focus.value = 'any'; els.sort.value = 'best';
      els.published.checked = false;
      render();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    els = {
      q: $('f-q'), region: $('f-region'), type: $('f-type'), budget: $('f-budget'),
      focus: $('f-focus'), sort: $('f-sort'), published: $('f-published'),
      clear: $('f-clear'), results: $('results'), count: $('result-count')
    };
    populateRegions();
    bind();
    render();
  });
})();
