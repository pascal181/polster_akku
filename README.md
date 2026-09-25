# Polster Akku

Eigene Home-Assistant-Integration für Zigbee- und Tuya-Batterien.

- Findet automatisch alle Sensoren mit `device_class: battery`
- Dashboard-Karte mit Suche, Balken und Farbe
- Gerät per ✕ aus der Liste nehmen (persistenter Speicher, kein 255-Zeichen-Limit)
- Event + optionale Push-Nachricht, wenn ein Akku neu unter die Schwelle fällt
- Dienste: `polster_akku.ignore` / `restore` / `restore_all`

Keine Abhängigkeit von Battery Notes oder anderen HACS-Karten.

## Installation über HACS

1. HACS → drei Punkte → **Custom repositories**
2. URL: `https://github.com/pascal181/polster_akku`
3. Kategorie: **Integration**
4. Polster Akku installieren, Home Assistant neu starten
5. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Polster Akku**

## Karte

Nach dem Start der Integration ist die Karte unter

`/polster_akku/polster-akku-card.js`

erreichbar. Einmalig als Dashboard-Ressource vom Typ **JavaScript-Modul** eintragen.

```yaml
type: custom:polster-akku-card
title: Akkus
threshold: 20
```

Alternativ die Datei nach `/config/www/` kopieren und `/local/polster-akku-card.js` nutzen.

## Manuell ohne HACS

Ordner `custom_components/polster_akku` nach `/config/custom_components/` kopieren, Core neu starten, Integration hinzufügen.

## Dienste

| Dienst | Zweck |
|---|---|
| `polster_akku.ignore` | Entity aus der Liste nehmen |
| `polster_akku.restore` | Eine Entity wieder einblenden |
| `polster_akku.restore_all` | Ignore-Liste leeren |

Ignore-Liste liegt in `.storage/polster_akku_ignored`.

## Events

- `polster_akku_low` – Gerät rutscht neu unter die Schwelle (`name`, `level`, `entity_id`)
- `polster_akku_ok` – Gerät ist wieder darüber
