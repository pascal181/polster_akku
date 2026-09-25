class PolsterAkkuCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._config = {};
    this._filter = "";
  }
  static getStubConfig() {
    return { type: "custom:polster-akku-card", title: "Akkus", threshold: 20, list_entity: "sensor.akkus_kritisch" };
  }
  setConfig(config) {
    this._config = { title: "Akkus", threshold: 20, list_entity: "sensor.akkus_kritisch", show_all: true, collapse_all: 12, ...config };
    this._render();
  }
  set hass(hass) { this._hass = hass; this._render(); }
  getCardSize() { return 6; }
  _ignored() {
    const arr = this._hass?.states?.[this._config.list_entity]?.attributes?.ignoriert;
    return Array.isArray(arr) ? arr : [];
  }
  _batteries() {
    if (!this._hass) return [];
    const ignored = new Set(this._ignored());
    const skipRe = /(_battery_plus|_battery_state|_battery_low|_battery_voltage)$/i;
    const out = [];
    for (const [eid, st] of Object.entries(this._hass.states)) {
      if (st.attributes?.device_class !== "battery") continue;
      if (!eid.startsWith("sensor.")) continue;
      if (skipRe.test(eid)) continue;
      if (ignored.includes(eid)) continue;
      const lvl = Number.parseFloat(st.state);
      if (!Number.isFinite(lvl) || lvl < 0 || lvl > 100) continue;
      const name = (st.attributes.friendly_name || eid).replace(/\s*battery(\s*level)?$/i, "").replace(/\s*batterie(\s*stand)?$/i, "").trim();
      out.push({ entity_id: eid, name, level: Math.round(lvl) });
    }
    out.sort((a, b) => a.level - b.level || a.name.localeCompare(b.name, "de"));
    return out;
  }
  _color(level) {
    if (level <= 10) return "#c62828";
    if (level <= 20) return "#ef6c00";
    if (level <= 40) return "#f9a825";
    if (level <= 70) return "#7cb342";
    return "#2e7d32";
  }
  async _ignore(entityId) {
    if (!this._hass) return;
    await this._hass.callService("polster_akku", "ignore", { entity_id: entityId });
  }
  _openMore(entityId) {
    const ev = new Event("hass-more-info", { bubbles: true, composed: true });
    ev.detail = { entityId };
    this.dispatchEvent(ev);
  }
  _esc(s) {
    return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
  }
  _row(item) {
    const c = this._color(item.level);
    return `<div class="row" data-open="${this._esc(item.entity_id)}"><div class="batt" style="color:${c}"><i style="width:${item.level}%;background:${c}"></i></div><div class="name">${this._esc(item.name)}</div><div class="pct" style="color:${c}">${item.level} %</div><button class="trash" data-ignore="${this._esc(item.entity_id)}">✕</button></div><div class="barwrap"><div class="bar" style="width:${item.level}%;background:${c}"></div></div>`;
  }
  _render() {
    if (!this._config) return;
    const items = this._hass ? this._batteries() : [];
    const q = this._filter.trim().toLowerCase();
    const filtered = q ? items.filter((i) => i.name.toLowerCase().includes(q) || i.entity_id.includes(q)) : items;
    const limit = Number(this._config.threshold) || 20;
    const low = filtered.filter((i) => i.level <= limit);
    const rest = filtered.filter((i) => i.level > limit).slice(0, Number(this._config.collapse_all) || 12);
    this.shadowRoot.innerHTML = `<style>:host{display:block}ha-card{padding:16px 16px 8px}.head{display:flex;justify-content:space-between;margin-bottom:10px}.title{font-size:1.15rem;font-weight:600}.meta{font-size:.8rem;opacity:.7}.search{width:100%;box-sizing:border-box;margin:0 0 12px;border:none;border-radius:10px;padding:10px 12px;background:var(--secondary-background-color,#eee);color:var(--primary-text-color);font:inherit}.section{font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;opacity:.55;margin:14px 0 6px}.row{display:grid;grid-template-columns:28px 1fr auto 36px;align-items:center;gap:8px;min-height:44px;cursor:pointer;border-radius:10px;padding:2px 4px}.name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pct{font-variant-numeric:tabular-nums;font-weight:650;min-width:3.2em;text-align:right}.barwrap{grid-column:2/4;height:4px;border-radius:99px;background:var(--divider-color,#ddd);overflow:hidden;margin:-6px 0 8px 36px}.bar{height:100%;border-radius:99px}button.trash{border:0;background:transparent;cursor:pointer;opacity:.35;width:36px;height:36px}.empty,.hint{opacity:.55;padding:8px 2px;font-size:.8rem}.batt{width:22px;height:12px;border:2px solid currentColor;border-radius:2px;position:relative}.batt::after{content:"";position:absolute;right:-5px;top:2px;width:3px;height:6px;background:currentColor}.batt i{display:block;height:100%}</style><ha-card><div class="head"><div class="title">${this._esc(this._config.title)}</div><div class="meta">${low.length} kritisch · ${filtered.length} gesamt</div></div><input class="search" type="search" placeholder="Suchen…" value="${this._esc(this._filter)}">${low.length ? `<div class="section">Leer / kritisch (≤ ${limit} %)</div>` : ""}${low.map((i)=>this._row(i)).join("")}${rest.length ? `<div class="section">Alle anderen</div>` : ""}${rest.map((i)=>this._row(i)).join("")}<div class="hint">✕ blendet das Gerät aus (Dienst polster_akku.ignore).</div></ha-card>`;
    const input = this.shadowRoot.querySelector(".search");
    if (input) input.addEventListener("input", (e) => { this._filter = e.target.value; this._render(); const a=this.shadowRoot.querySelector(".search"); if(a){a.focus(); const n=a.value.length; a.setSelectionRange(n,n);} });
    this.shadowRoot.querySelectorAll("[data-open]").forEach((el) => el.addEventListener("click", () => this._openMore(el.dataset.open)));
    this.shadowRoot.querySelectorAll("[data-ignore]").forEach((el) => el.addEventListener("click", (ev) => { ev.stopPropagation(); this._ignore(el.dataset.ignore); }));
  }
}
customElements.define("polster-akku-card", PolsterAkkuCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "polster-akku-card", name: "Polster Akku", description: "Akku-Übersicht Zigbee & Tuya" });
