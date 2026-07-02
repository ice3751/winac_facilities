/*
 * تقویم شمسی سبک و خودکفا (بدون وابستگی) برای استفاده روی شبکهٔ داخلی.
 *
 * روی هر input با کلاس "jalali-date" فعال می‌شود. مقدار واقعیِ ارسالی به سرور
 * همان میلادیِ ISO (YYYY-MM-DD) باقی می‌ماند تا Django بدون تغییر کار کند؛ کاربر
 * تاریخ را به‌صورت شمسی می‌بیند و انتخاب می‌کند.
 *
 * الگوریتم تبدیل برگرفته از jalaali-js (نسخهٔ عمومی، MIT).
 */
(function () {
  "use strict";

  function div(a, b) { return ~~(a / b); }
  function mod(a, b) { return a - ~~(a / b) * b; }

  function g2d(gy, gm, gd) {
    var d = div((gy + div(gm - 8, 6) + 100100) * 1461, 4) +
      div(153 * mod(gm + 9, 12) + 2, 5) + gd - 34840408;
    d = d - div(div(gy + 100100 + div(gm - 8, 6), 100) * 3, 4) + 752;
    return d;
  }
  function d2g(jdn) {
    var j = 4 * jdn + 139361631;
    j = j + div(div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908;
    var i = div(mod(j, 1461), 4) * 5 + 308;
    var gd = div(mod(i, 153), 5) + 1;
    var gm = mod(div(i, 153), 12) + 1;
    var gy = div(j, 1461) - 100100 + div(8 - gm, 6);
    return { gy: gy, gm: gm, gd: gd };
  }
  function jalCal(jy) {
    var breaks = [-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
      1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178];
    var bl = breaks.length, gy = jy + 621, leapJ = -14, jp = breaks[0];
    var jm, jump, leap, leapG, march, n, i;
    for (i = 1; i < bl; i += 1) {
      jm = breaks[i]; jump = jm - jp;
      if (jy < jm) break;
      leapJ = leapJ + div(jump, 33) * 8 + div(mod(jump, 33), 4);
      jp = jm;
    }
    n = jy - jp;
    leapJ = leapJ + div(n, 33) * 8 + div(mod(n, 33) + 3, 4);
    if (mod(jump, 33) === 4 && jump - n === 4) leapJ += 1;
    leapG = div(gy, 4) - div((div(gy, 100) + 1) * 3, 4) - 150;
    march = 20 + leapJ - leapG;
    if (jump - n < 6) n = n - jump + div(jump + 4, 33) * 33;
    leap = mod(mod(n + 1, 33) - 1, 4);
    if (leap === -1) leap = 4;
    return { leap: leap, gy: gy, march: march };
  }
  function j2d(jy, jm, jd) {
    var r = jalCal(jy);
    return g2d(r.gy, 3, r.march) + (jm - 1) * 31 - div(jm, 7) * (jm - 7) + jd - 1;
  }
  function d2j(jdn) {
    var gy = d2g(jdn).gy, jy = gy - 621, r = jalCal(jy);
    var jdn1f = g2d(gy, 3, r.march), jd, jm, k;
    k = jdn - jdn1f;
    if (k >= 0) {
      if (k <= 185) { jm = 1 + div(k, 31); jd = mod(k, 31) + 1; return { jy: jy, jm: jm, jd: jd }; }
      k -= 186;
    } else { jy -= 1; k += 179; if (r.leap === 1) k += 1; }
    jm = 7 + div(k, 30); jd = mod(k, 30) + 1;
    return { jy: jy, jm: jm, jd: jd };
  }
  function isLeapJalaali(jy) { return jalCal(jy).leap === 0; }
  function jMonthLen(jy, jm) {
    if (jm <= 6) return 31;
    if (jm <= 11) return 30;
    return isLeapJalaali(jy) ? 30 : 29;
  }
  function toJalaali(gy, gm, gd) { return d2j(g2d(gy, gm, gd)); }
  function toGregorian(jy, jm, jd) { return d2g(j2d(jy, jm, jd)); }

  var MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"];
  var WEEK = ["ش", "ی", "د", "س", "چ", "پ", "ج"];

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function isoFromJ(jy, jm, jd) {
    var g = toGregorian(jy, jm, jd);
    return g.gy + "-" + pad(g.gm) + "-" + pad(g.gd);
  }
  function jStr(jy, jm, jd) { return jy + "/" + pad(jm) + "/" + pad(jd); }

  function parseIso(v) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || "");
    if (!m) return null;
    return { gy: +m[1], gm: +m[2], gd: +m[3] };
  }

  function buildPicker(hidden, display) {
    var pop = document.createElement("div");
    pop.className = "jdp-pop";
    pop.style.display = "none";
    document.body.appendChild(pop);

    var view;  // {jy, jm}
    var selected = null;

    function openView() {
      var iso = parseIso(hidden.value);
      var base = iso ? toJalaali(iso.gy, iso.gm, iso.gd)
        : (function () { var t = new Date(); return toJalaali(t.getFullYear(), t.getMonth() + 1, t.getDate()); })();
      view = { jy: base.jy, jm: base.jm };
      selected = iso ? toJalaali(iso.gy, iso.gm, iso.gd) : null;
    }

    function render() {
      var firstIso = isoFromJ(view.jy, view.jm, 1);
      var p = parseIso(firstIso);
      var startDay = new Date(p.gy, p.gm - 1, p.gd).getDay(); // 0=Sun
      var col = (startDay + 1) % 7; // 0=Sat
      var len = jMonthLen(view.jy, view.jm);
      var now = new Date();
      var todayJ = toJalaali(now.getFullYear(), now.getMonth() + 1, now.getDate());

      var html = '<div class="jdp-head">' +
        '<button type="button" class="jdp-nav" data-act="next">‹</button>' +
        '<span>' + MONTHS[view.jm - 1] + ' ' + view.jy + '</span>' +
        '<button type="button" class="jdp-nav" data-act="prev">›</button></div>';
      html += '<div class="jdp-grid">';
      WEEK.forEach(function (w, wi) {
        html += '<div class="jdp-w' + (wi === 6 ? ' jdp-fri' : '') + '">' + w + '</div>';
      });
      for (var i = 0; i < col; i++) html += '<div></div>';
      for (var d = 1; d <= len; d++) {
        var weekday = (col + d - 1) % 7;
        var sel = selected && selected.jy === view.jy && selected.jm === view.jm && selected.jd === d;
        var isToday = todayJ.jy === view.jy && todayJ.jm === view.jm && todayJ.jd === d;
        var cls = 'jdp-day' + (weekday === 6 ? ' jdp-fri' : '') +
          (isToday ? ' jdp-today-cell' : '') + (sel ? ' jdp-sel' : '');
        html += '<div class="' + cls + '" data-d="' + d + '">' + d + '</div>';
      }
      html += '</div>';
      html += '<div class="jdp-foot"><button type="button" class="jdp-today">امروز</button>' +
        '<button type="button" class="jdp-clear">پاک کردن</button></div>';
      pop.innerHTML = html;
    }

    function place() {
      var r = display.getBoundingClientRect();
      pop.style.position = "absolute";
      pop.style.top = (window.scrollY + r.bottom + 4) + "px";
      pop.style.left = (window.scrollX + r.left) + "px";
    }

    function show() { openView(); render(); place(); pop.style.display = "block"; }
    function hide() { pop.style.display = "none"; }

    function pick(jy, jm, jd) {
      hidden.value = isoFromJ(jy, jm, jd);
      display.value = jStr(jy, jm, jd);
      hide();
    }

    display.addEventListener("focus", show);
    display.addEventListener("click", show);

    pop.addEventListener("click", function (e) {
      var t = e.target;
      if (t.dataset.act === "prev") {
        view.jm++; if (view.jm > 12) { view.jm = 1; view.jy++; } render();
      } else if (t.dataset.act === "next") {
        view.jm--; if (view.jm < 1) { view.jm = 12; view.jy--; } render();
      } else if (t.classList.contains("jdp-day")) {
        pick(view.jy, view.jm, +t.dataset.d);
      } else if (t.classList.contains("jdp-today")) {
        var now = new Date(); var j = toJalaali(now.getFullYear(), now.getMonth() + 1, now.getDate());
        pick(j.jy, j.jm, j.jd);
      } else if (t.classList.contains("jdp-clear")) {
        hidden.value = ""; display.value = ""; hide();
      }
    });

    document.addEventListener("click", function (e) {
      if (e.target !== display && !pop.contains(e.target)) hide();
    });
  }

  function enhance(input) {
    // ورودی اصلی به hidden تبدیل می‌شود و مقدار ISO را نگه می‌دارد
    input.type = "hidden";
    var display = document.createElement("input");
    display.className = input.className.replace("jalali-date", "") + " jdp-display";
    display.setAttribute("autocomplete", "off");
    display.setAttribute("placeholder", "انتخاب تاریخ (شمسی)");
    display.readOnly = true;
    var iso = parseIso(input.value);
    if (iso) {
      var j = toJalaali(iso.gy, iso.gm, iso.gd);
      display.value = jStr(j.jy, j.jm, j.jd);
    }
    input.parentNode.insertBefore(display, input.nextSibling);
    buildPicker(input, display);
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("input.jalali-date").forEach(enhance);
  });
})();
