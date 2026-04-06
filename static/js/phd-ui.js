/**
 * Toasts e modal de confirmacao alinhados ao tema (:root --primary, --bg-card, etc.)
 */
(function () {
  "use strict";

  var STYLE_ID = "phd-ui-styles";
  var Z = 10060;

  var STYLES =
    ".phd-toast-host{position:fixed;left:50%;bottom:max(24px,env(safe-area-inset-bottom));transform:translateX(-50%);z-index:" +
    Z +
    ";display:flex;flex-direction:column-reverse;align-items:center;gap:10px;pointer-events:none;width:min(420px,calc(100vw - 32px));}" +
    ".phd-toast{display:flex;align-items:flex-start;gap:12px;padding:16px 18px;border-radius:18px;" +
    "background:var(--bg-card,#0d121b);border:1px solid var(--border,#1e293b);color:var(--text-main,#fff);" +
    "font-family:'Plus Jakarta Sans',system-ui,sans-serif;font-size:0.92rem;line-height:1.45;" +
    "box-shadow:0 18px 40px rgba(0,0,0,.55);pointer-events:auto;animation:phd-toast-in .35s ease both;}" +
    ".phd-toast.phd-toast--out{animation:phd-toast-out .28s ease both;}" +
    ".phd-toast__icon{flex-shrink:0;width:36px;height:36px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.15rem;}" +
    ".phd-toast--info .phd-toast__icon{background:rgba(0,163,255,.15);color:var(--primary,#00a3ff);}" +
    ".phd-toast--success .phd-toast__icon{background:rgba(0,230,118,.12);color:var(--success,#00e676);}" +
    ".phd-toast--warning .phd-toast__icon{background:rgba(255,193,7,.12);color:#ffc107;}" +
    ".phd-toast--error .phd-toast__icon{background:rgba(255,77,77,.12);color:var(--danger,#ff4d4d);}" +
    ".phd-toast__body{flex:1;min-width:0;}" +
    ".phd-toast__title{font-weight:700;font-size:0.8rem;text-transform:uppercase;letter-spacing:.06em;color:var(--text-muted,#94a3b8);margin-bottom:4px;}" +
    ".phd-toast__text{word-break:break-word;}" +
    "@keyframes phd-toast-in{from{opacity:0;transform:translateY(12px) scale(.96);}to{opacity:1;transform:translateY(0) scale(1);}}" +
    "@keyframes phd-toast-out{to{opacity:0;transform:translateY(8px) scale(.96);}}" +
    ".phd-modal-backdrop{position:fixed;inset:0;z-index:" +
    (Z + 1) +
    ";background:rgba(5,7,10,.72);backdrop-filter:blur(8px);" +
    "display:flex;align-items:center;justify-content:center;padding:20px;animation:phd-fade-in .2s ease both;}" +
    ".phd-modal{background:var(--bg-card,#0d121b);border:1px solid var(--border,#1e293b);border-radius:24px;" +
    "max-width:400px;width:100%;padding:28px 26px;box-shadow:0 28px 60px rgba(0,0,0,.55);" +
    "font-family:'Plus Jakarta Sans',system-ui,sans-serif;color:var(--text-main,#fff);animation:phd-modal-in .3s cubic-bezier(.22,1,.36,1) both;}" +
    ".phd-modal__title{font-size:1.15rem;font-weight:800;margin:0 0 10px;letter-spacing:-.02em;}" +
    ".phd-modal__msg{margin:0 0 24px;font-size:0.95rem;line-height:1.5;color:var(--text-muted,#94a3b8);white-space:pre-line;}" +
    ".phd-modal__actions{display:flex;flex-wrap:wrap;gap:10px;justify-content:flex-end;}" +
    ".phd-modal__btn{border:none;border-radius:14px;padding:12px 20px;font-weight:700;font-size:0.85rem;cursor:pointer;" +
    "transition:transform .2s,box-shadow .2s;font-family:inherit;text-transform:uppercase;letter-spacing:.04em;}" +
    ".phd-modal__btn:active{transform:scale(.98);}" +
    ".phd-modal__btn--ghost{background:var(--bg-accent,#161f2e);color:var(--text-main,#fff);border:1px solid var(--border,#1e293b);}" +
    ".phd-modal__btn--ghost:hover{filter:brightness(1.08);}" +
    ".phd-modal__btn--primary{background:var(--primary,#00a3ff);color:#fff;}" +
    ".phd-modal__btn--primary:hover{filter:brightness(1.08);box-shadow:0 10px 28px rgba(0,0,0,.35);}" +
    ".phd-modal__btn--danger{background:var(--danger,#ff4d4d);color:#fff;}" +
    ".phd-modal__btn--danger:hover{filter:brightness(1.08);box-shadow:0 8px 22px rgba(255,77,77,.25);}" +
    "@keyframes phd-fade-in{from{opacity:0}to{opacity:1}}" +
    "@keyframes phd-modal-in{from{opacity:0;transform:translateY(16px) scale(.97);}to{opacity:1;transform:translateY(0) scale(1);}}";

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) return;
    var s = document.createElement("style");
    s.id = STYLE_ID;
    s.textContent = STYLES;
    document.head.appendChild(s);
  }

  function iconClass(type) {
    if (type === "success") return "bi-check-circle-fill";
    if (type === "error") return "bi-exclamation-octagon-fill";
    if (type === "warning") return "bi-exclamation-triangle-fill";
    return "bi-info-circle-fill";
  }

  function titleFor(type) {
    if (type === "success") return "Sucesso";
    if (type === "error") return "Erro";
    if (type === "warning") return "Atenção";
    return "Informação";
  }

  function toast(message, type, duration) {
    ensureStyles();
    type = type || "info";
    duration = duration === undefined ? 4200 : duration;

    var host = document.getElementById("phd-toast-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "phd-toast-host";
      host.className = "phd-toast-host";
      host.setAttribute("aria-live", "polite");
      document.body.appendChild(host);
    }

    var el = document.createElement("div");
    el.className = "phd-toast phd-toast--" + type;
    el.setAttribute("role", "status");

    var icon = document.createElement("i");
    icon.className = "bi " + iconClass(type) + " phd-toast__icon";

    var body = document.createElement("div");
    body.className = "phd-toast__body";
    var t = document.createElement("div");
    t.className = "phd-toast__title";
    t.textContent = titleFor(type);
    var txt = document.createElement("div");
    txt.className = "phd-toast__text";
    txt.textContent = message;

    body.appendChild(t);
    body.appendChild(txt);
    el.appendChild(icon);
    el.appendChild(body);
    host.appendChild(el);

    var tid = setTimeout(function () {
      el.classList.add("phd-toast--out");
      setTimeout(function () {
        el.remove();
        if (host && !host.children.length) host.remove();
      }, 280);
    }, duration);

    el.addEventListener("click", function () {
      clearTimeout(tid);
      el.classList.add("phd-toast--out");
      setTimeout(function () {
        el.remove();
        if (host && !host.children.length) host.remove();
      }, 280);
    });
  }

  function confirmModal(opts) {
    ensureStyles();
    opts = opts || {};
    var title = opts.title || "Confirmar";
    var message = opts.message || "";
    var confirmText = opts.confirmText || "Confirmar";
    var cancelText = opts.cancelText || "Cancelar";
    var danger = !!opts.danger;

    return new Promise(function (resolve) {
      var backdrop = document.createElement("div");
      backdrop.className = "phd-modal-backdrop";
      backdrop.setAttribute("role", "dialog");
      backdrop.setAttribute("aria-modal", "true");

      var modal = document.createElement("div");
      modal.className = "phd-modal";

      var h = document.createElement("h2");
      h.className = "phd-modal__title";
      h.textContent = title;

      var p = document.createElement("p");
      p.className = "phd-modal__msg";
      p.textContent = message;

      var actions = document.createElement("div");
      actions.className = "phd-modal__actions";

      var btnCancel = document.createElement("button");
      btnCancel.type = "button";
      btnCancel.className = "phd-modal__btn phd-modal__btn--ghost";
      btnCancel.textContent = cancelText;

      var btnOk = document.createElement("button");
      btnOk.type = "button";
      btnOk.className =
        "phd-modal__btn " +
        (danger ? "phd-modal__btn--danger" : "phd-modal__btn--primary");
      btnOk.textContent = confirmText;

      function cleanup(result) {
        document.removeEventListener("keydown", onKey);
        if (document.body.contains(backdrop)) backdrop.remove();
        document.body.style.overflow = "";
        resolve(result);
      }

      function onKey(e) {
        if (e.key === "Escape") cleanup(false);
      }

      btnCancel.addEventListener("click", function () {
        cleanup(false);
      });
      btnOk.addEventListener("click", function () {
        cleanup(true);
      });
      backdrop.addEventListener("click", function (e) {
        if (e.target === backdrop) cleanup(false);
      });

      document.addEventListener("keydown", onKey);
      document.body.style.overflow = "hidden";

      actions.appendChild(btnCancel);
      actions.appendChild(btnOk);
      modal.appendChild(h);
      modal.appendChild(p);
      modal.appendChild(actions);
      backdrop.appendChild(modal);
      document.body.appendChild(backdrop);
      btnOk.focus();
    });
  }

  window.phdUI = { toast: toast, confirm: confirmModal };
})();
