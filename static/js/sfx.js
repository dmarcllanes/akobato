/**
 * Akobato SFX — cyberpunk arcade audio via Web Audio API.
 * All sounds are synthesised; no audio files required.
 */
(function () {
  'use strict';

  var _ctx = null;

  function ctx() {
    if (!_ctx) {
      _ctx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (_ctx.state === 'suspended') _ctx.resume();
    return _ctx;
  }

  /* ── Low-level helpers ─────────────────────────────────────────────── */

  function node(type, freq, t, dur, vol) {
    var c = ctx();
    var o = c.createOscillator();
    var g = c.createGain();
    o.connect(g); g.connect(c.destination);
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.start(t); o.stop(t + dur + 0.01);
    return o;
  }

  function sweep(type, f0, f1, t, dur, vol) {
    var c = ctx();
    var o = c.createOscillator();
    var g = c.createGain();
    o.connect(g); g.connect(c.destination);
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    o.frequency.exponentialRampToValueAtTime(f1, t + dur);
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.start(t); o.stop(t + dur + 0.02);
  }

  function noise(t, dur, vol) {
    var c = ctx();
    var bufSize = c.sampleRate * dur;
    var buf = c.createBuffer(1, bufSize, c.sampleRate);
    var data = buf.getChannelData(0);
    for (var i = 0; i < bufSize; i++) data[i] = Math.random() * 2 - 1;
    var src = c.createBufferSource();
    var g   = c.createGain();
    var lp  = c.createBiquadFilter();
    lp.type = 'lowpass'; lp.frequency.value = 400;
    src.buffer = buf;
    src.connect(lp); lp.connect(g); g.connect(c.destination);
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    src.start(t); src.stop(t + dur + 0.01);
  }

  /* ── Sound library ─────────────────────────────────────────────────── */

  window.SFX = {

    /* Short UI button click */
    click: function () {
      var t = ctx().currentTime;
      sweep('square', 900, 300, t, 0.055, 0.12);
      noise(t, 0.03, 0.04);
    },

    /* Softer nav / tab switch */
    nav: function () {
      var t = ctx().currentTime;
      sweep('square', 600, 250, t, 0.04, 0.07);
    },

    /* Opponent joined / match found — 3 ascending blips */
    matchFound: function () {
      var t = ctx().currentTime;
      [440, 660, 1100].forEach(function (f, i) {
        node('square', f, t + i * 0.09, 0.075, 0.18);
      });
    },

    /* Game / arena starting — cyberpunk power-up */
    arenaStart: function () {
      var t = ctx().currentTime;
      sweep('sawtooth', 80,  2200, t,       0.38, 0.22);
      sweep('sawtooth', 100, 1100, t + 0.1, 0.25, 0.12);
      node ('square',   2200, t + 0.38, 0.28, 0.18);
      noise(t, 0.15, 0.05);
    },

    /* Countdown tick (plays each second while timer > 10) */
    tick: function () {
      var t = ctx().currentTime;
      node('sine', 440, t, 0.038, 0.08);
    },

    /* Urgent warning tick (last 10 seconds) */
    warning: function () {
      var t = ctx().currentTime;
      node('square', 880, t,        0.06, 0.22);
      node('square', 880, t + 0.09, 0.06, 0.22);
    },

    /* Timer hit zero */
    timerEnd: function () {
      var t = ctx().currentTime;
      sweep('sawtooth', 700, 150, t, 0.45, 0.25);
      noise(t, 0.12, 0.08);
    },

    /* Submit argument */
    submit: function () {
      var t = ctx().currentTime;
      node('square', 440, t,        0.05, 0.18);
      node('square', 660, t + 0.06, 0.09, 0.18);
      node('sine',   880, t + 0.13, 0.12, 0.12);
    },

    /* Token spend */
    token: function () {
      var t = ctx().currentTime;
      sweep('sine', 1400, 700, t,       0.12, 0.18);
      node ('sine',  900,      t + 0.09, 0.1,  0.1);
    },

    /* Win — rising C-major arpeggio */
    win: function () {
      var t = ctx().currentTime;
      [523, 659, 784, 1047].forEach(function (f, i) {
        node('square', f, t + i * 0.11, 0.13, 0.22);
      });
      node('sine', 1047, t + 0.55, 0.65, 0.18);
      sweep('sawtooth', 200, 800, t, 0.3, 0.08);
    },

    /* Lose — descending sweep with noise */
    lose: function () {
      var t = ctx().currentTime;
      sweep('sawtooth', 550, 80, t, 0.6, 0.22);
      noise(t + 0.05, 0.2, 0.07);
      node ('square', 220, t + 0.3, 0.3, 0.12);
    },

    /* Tie — two neutral pulses */
    tie: function () {
      var t = ctx().currentTime;
      node('sine', 440, t,       0.18, 0.18);
      node('sine', 440, t + 0.22, 0.18, 0.18);
    },

    /* Room created / code copied */
    roomCreated: function () {
      var t = ctx().currentTime;
      sweep('square', 300, 900, t,       0.15, 0.14);
      node ('square', 900, t + 0.15, 0.12, 0.14);
    },

    /* Arcade boot / coin-insert — landing & login page intro */
    boot: function () {
      var t = ctx().currentTime;
      // Descending coin-ping
      sweep('sine', 1400, 500, t, 0.09, 0.22);
      noise(t + 0.06, 0.04, 0.07);
      // Rising power-up sweep
      sweep('sawtooth', 90, 1600, t + 0.12, 0.38, 0.16);
      sweep('sawtooth', 120, 800,  t + 0.18, 0.28, 0.08);
      // Confirmation arpeggio
      [440, 554, 659, 880].forEach(function (f, i) {
        node('square', f, t + 0.52 + i * 0.07, 0.065, 0.16);
      });
    },

    /* Big dramatic CTA press — "PRESS START" energy */
    enter: function () {
      var t = ctx().currentTime;
      noise(t, 0.06, 0.07);
      sweep('sawtooth', 120, 1100, t + 0.02, 0.22, 0.26);
      node ('square',   1100, t + 0.22, 0.18, 0.22);
      node ('square',   1320, t + 0.34, 0.14, 0.18);
      node ('sine',     660,  t + 0.42, 0.22, 0.14);
    },

    /* Card reveal — soft blip as element scrolls into view */
    reveal: function () {
      var t = ctx().currentTime;
      sweep('sine', 280, 560, t,        0.11, 0.09);
      node ('sine',  560, t + 0.1, 0.07, 0.07);
    },

    /* Typewriter key — ultra-short mechanical tap */
    type: function () {
      var t = ctx().currentTime;
      noise(t, 0.013, 0.055);
      node('square', 2800, t, 0.010, 0.04);
    },

  };

  /* ── Global interaction sounds ─────────────────────────────────────── */

  var _lastClick = 0;
  document.addEventListener('click', function (e) {
    var now = Date.now();
    if (now - _lastClick < 60) return;   // debounce
    _lastClick = now;

    var el = e.target;
    // Nav links — softer sound
    if (el.closest('.nav-link, .dm-nav-btn, .mh-tab, .jr-tab')) {
      SFX.nav(); return;
    }
    // Token-spending actions — coin sound
    if (el.closest('[data-sfx="token"]')) {
      SFX.token(); return;
    }
    // Major CTA buttons — dramatic enter sound
    if (el.closest('.lp-cta-btn, .login-google-btn')) {
      SFX.enter(); return;
    }
    // Anything button-like
    if (el.closest('button, [role="button"], .btn, .dm-card, .rl-card, .ar-btn, .tp-btn, .cat-card, .pf-cat-card')) {
      SFX.click();
    }
  }, { passive: true });

})();
