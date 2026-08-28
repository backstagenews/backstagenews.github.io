/* ============================================================
   Backstage — site enhancements  (loaded after assets/js/main.js)
   ============================================================ */
(function () {
	'use strict';

	var reduceMotion = window.matchMedia &&
		window.matchMedia('(prefers-reduced-motion: reduce)').matches;

	/* ---- Dark mode (persisted) ---- */
	try {
		if (localStorage.getItem('bs-theme') === 'dark') document.body.classList.add('dark');
	} catch (e) {}

	function wireTheme() {
		var btn = document.querySelector('.theme-toggle');
		if (!btn) return;
		var sync = function () {
			var dark = document.body.classList.contains('dark');
			btn.textContent = dark ? '☀️' : '☽';
			btn.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
		};
		sync();
		btn.addEventListener('click', function () {
			document.body.classList.toggle('dark');
			try { localStorage.setItem('bs-theme', document.body.classList.contains('dark') ? 'dark' : 'light'); } catch (e) {}
			sync();
		});
	}

	/* ---- Live "today" label in the edition bar ---- */
	function wireToday() {
		var el = document.getElementById('today');
		if (!el) return;
		var now = new Date();
		var d = now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });
		var t = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
		el.textContent = d + ' · ' + t;
	}

	/* ---- Footer year ---- */
	function wireYear() {
		Array.prototype.forEach.call(document.querySelectorAll('[data-year]'), function (el) {
			el.textContent = new Date().getFullYear();
		});
	}

	/* ---- Headline ticker: constant speed regardless of headline count ---- */
	function wireTicker() {
		var track = document.querySelector('.ticker-track');
		if (!track) return;
		if (reduceMotion) { track.style.animation = 'none'; return; }
		var loopWidth = track.scrollWidth / 2;
		var seconds = Math.max(30, Math.round(loopWidth / 55));
		track.style.animationDuration = seconds + 's';
	}

	/* ---- Highlight current section in the sidebar menu + section nav ---- */
	function wireActiveNav() {
		var page = (location.pathname.split('/').pop() || 'index.html');
		var base = page.replace(/-\d+\.html$/, '.html'); // news-3.html -> news.html
		Array.prototype.forEach.call(document.querySelectorAll('#menu a[href], .section-nav a[href]'), function (a) {
			var href = a.getAttribute('href');
			if (href === page || href === base) a.classList.add('is-active');
		});
	}

	/* ---- Back-to-top button ---- */
	function wireBackToTop() {
		var btn = document.getElementById('backtotop');
		if (!btn) return;
		var onScroll = function () { btn.classList.toggle('show', window.pageYOffset > 600); };
		window.addEventListener('scroll', onScroll, { passive: true });
		onScroll();
		btn.addEventListener('click', function () {
			window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
		});
	}

	/* ---- Copy-link button in the share row ---- */
	function wireShare() {
		var btn = document.querySelector('.share-row .copy');
		if (!btn) return;
		btn.addEventListener('click', function () {
			var url = btn.getAttribute('data-url') || location.href;
			var done = function () {
				var tag = document.createElement('span');
				tag.className = 'copied';
				tag.textContent = 'Link copied';
				btn.parentNode.appendChild(tag);
				setTimeout(function () { tag.remove(); }, 2000);
			};
			if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done);
			else done();
		});
	}

	/* ---- Newsletter form -> opens a pre-filled email ---- */
	function wireNewsletter() {
		var form = document.querySelector('.newsletter form');
		if (!form) return;
		form.addEventListener('submit', function (e) {
			e.preventDefault();
			var input = form.querySelector('input[type="email"]');
			var addr = (input && input.value.trim()) || '';
			var to = 'backstagenewsng@gmail.com';
			var body = encodeURIComponent('Please add this address to the Backstage newsletter: ' + addr);
			window.location.href = 'mailto:' + to + '?subject=' + encodeURIComponent('Newsletter signup') + '&body=' + body;
			var note = form.parentNode.querySelector('.note');
			if (note) { note.innerHTML = '<span class="ok">Thanks!</span> Your email app should open to confirm.'; }
		});
	}

	document.addEventListener('DOMContentLoaded', function () {
		wireTheme();
		wireToday();
		wireYear();
		wireTicker();
		wireActiveNav();
		wireBackToTop();
		wireShare();
		wireNewsletter();
	});
})();
