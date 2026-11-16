/* Cupcake Store — interações do front-end (JS puro, sem dependências) */
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const csrf = () => ($('meta[name="csrf-token"]') || {}).content || "";

  /* ---------- Toasts (feedback imediato) ---------- */
  function toast(message, kind = "success") {
    let box = $(".flashes");
    if (!box) { box = document.createElement("div"); box.className = "flashes"; document.body.appendChild(box); }
    const el = document.createElement("div");
    el.className = `alert alert-${kind}`;
    el.setAttribute("role", "status");
    el.innerHTML = `<span></span><button type="button" aria-label="Fechar">×</button>`;
    el.firstChild.textContent = message;
    box.appendChild(el);
    autoClose(el);
  }
  function autoClose(el) {
    el.querySelector("button")?.addEventListener("click", () => el.remove());
    setTimeout(() => { el.style.transition = "opacity .3s"; el.style.opacity = "0"; setTimeout(() => el.remove(), 300); }, 4500);
  }
  $$(".flashes .alert").forEach(autoClose);

  /* ---------- Menu mobile ---------- */
  $(".nav-toggle")?.addEventListener("click", () => $(".navbar").classList.toggle("open"));

  /* ---------- Seletor de quantidade ---------- */
  $$(".qty").forEach((q) => {
    const input = q.querySelector("input");
    q.querySelectorAll("button[data-step]").forEach((b) =>
      b.addEventListener("click", () => {
        const min = +input.min || 1, max = +input.max || 999;
        input.value = Math.min(max, Math.max(min, (+input.value || 1) + +b.dataset.step));
        if (q.dataset.autosubmit !== undefined) q.closest("form").requestSubmit();
      })
    );
  });

  /* ---------- Adicionar ao carrinho sem recarregar (HU-011 CA#3) ---------- */
  $$("form.js-add-cart").forEach((form) =>
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = form.querySelector("button[type=submit]");
      btn.disabled = true;
      try {
        const res = await fetch(form.action, {
          method: "POST", body: new FormData(form),
          headers: { "X-Requested-With": "fetch", "X-CSRF-Token": csrf() },
        });
        if (res.redirected) { window.location = res.url; return; }
        const data = await res.json();
        toast(data.message, data.ok ? "success" : "error");
        if (data.ok) {
          const badge = $("#cart-count");
          if (badge) { badge.textContent = data.count; badge.hidden = false; }
          btn.innerHTML = "✓ Adicionado";
          setTimeout(() => (btn.innerHTML = btn.dataset.label), 1600);
        }
      } catch (_) { form.submit(); }
      finally { btn.disabled = false; }
    })
  );

  /* ---------- Força da senha (HU-001 RN#2) ---------- */
  $$("[data-pw-meter]").forEach((input) => {
    const wrap = input.closest(".field");
    const bar = wrap.querySelector(".pw-meter span");
    const rules = wrap.querySelectorAll(".pw-rules li");
    const tests = [/.{8,}/, /[A-Z]/, /[a-z]/, /\d/, /[^A-Za-z0-9]/];
    input.addEventListener("input", () => {
      const ok = tests.map((t) => t.test(input.value));
      ok.forEach((v, i) => rules[i]?.classList.toggle("ok", v));
      const score = ok.filter(Boolean).length;
      bar.style.width = `${score * 20}%`;
      bar.style.background = score < 3 ? "#d6334a" : score < 5 ? "#c98a00" : "#1f9d55";
    });
  });
  $$("[data-toggle-pw]").forEach((b) =>
    b.addEventListener("click", () => {
      const i = b.parentElement.querySelector("input");
      i.type = i.type === "password" ? "text" : "password";
      b.setAttribute("aria-label", i.type === "password" ? "Mostrar senha" : "Ocultar senha");
    })
  );
  $$("form[data-match]").forEach((f) =>
    f.addEventListener("submit", (e) => {
      const [a, b] = f.dataset.match.split(",").map((n) => f.elements[n]);
      if (a.value !== b.value) { e.preventDefault(); toast("As senhas não conferem.", "error"); b.focus(); }
    })
  );

  /* ---------- Confirmação (HU-008 / HU-016 RNF) ---------- */
  const dlg = $("#confirm-dialog");
  $$("[data-confirm]").forEach((el) =>
    el.addEventListener("click", (e) => {
      if (!dlg) return;
      e.preventDefault();
      const form = el.closest("form");
      $("#confirm-text", dlg).textContent = el.dataset.confirm;
      const typed = $("#confirm-typed", dlg);
      const need = el.dataset.confirmType || "";
      typed.hidden = !need;
      typed.querySelector("input").value = "";
      typed.querySelector("b").textContent = need;
      dlg.showModal();
      $("#confirm-ok", dlg).onclick = () => {
        if (need) {
          const v = typed.querySelector("input").value.trim();
          if (v !== need) { toast("Digite o nome exatamente como mostrado.", "error"); return; }
          form.querySelector("[name=confirm_name]").value = v;
        }
        dlg.close();
        form.submit();
      };
    })
  );
  $("#confirm-cancel")?.addEventListener("click", () => dlg.close());

  /* ---------- Máscaras ---------- */
  $$("input[data-mask=cep]").forEach((i) =>
    i.addEventListener("input", () => {
      const d = i.value.replace(/\D/g, "").slice(0, 8);
      i.value = d.length > 5 ? `${d.slice(0, 5)}-${d.slice(5)}` : d;
    })
  );
  $$("input[data-mask=phone]").forEach((i) =>
    i.addEventListener("input", () => {
      const d = i.value.replace(/\D/g, "").slice(0, 11);
      if (d.length <= 2) i.value = d ? `(${d}` : "";
      else if (d.length <= 6) i.value = `(${d.slice(0, 2)}) ${d.slice(2)}`;
      else if (d.length <= 10) i.value = `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`;
      else i.value = `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`;
    })
  );

  /* ---------- Pré-visualização de imagem (admin) ---------- */
  $$("input[type=file][data-preview]").forEach((i) =>
    i.addEventListener("change", () => {
      const img = $(i.dataset.preview);
      if (i.files[0] && img) img.src = URL.createObjectURL(i.files[0]);
    })
  );

  /* ---------- Copiar código Pix ---------- */
  $$("[data-copy]").forEach((b) =>
    b.addEventListener("click", async () => {
      const text = $(b.dataset.copy).textContent.trim();
      try { await navigator.clipboard.writeText(text); toast("Código Pix copiado!"); }
      catch (_) { toast("Não foi possível copiar. Selecione o texto manualmente.", "error"); }
    })
  );

  /* ---------- Auto-submit de selects ---------- */
  $$("[data-autosubmit]").forEach((el) => {
    if (el.tagName === "SELECT" || el.type === "radio") el.addEventListener("change", () => el.form.submit());
  });
})();
