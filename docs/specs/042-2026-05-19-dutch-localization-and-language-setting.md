# 042 - Dutch Localization and Language Setting

## Summary
Add Dutch localization to the frontend application and expose language selection from the Admin screen. English remains the default language. The first implementation should translate the visible application chrome, page labels, form labels, table headers, buttons, status labels, empty states, and toast copy while preserving existing URLs, API contracts, database values, and user-entered data.

This spec intentionally includes a Dutch terminology draft. The product owner can review and adjust the wording before implementation; Dutch copy should be treated as product language, not just a mechanical translation.

## Goals
- Support English and Dutch in the frontend UI.
- Add a persistent language selector to the Admin screen.
- Keep language selection local to the browser through `localStorage`.
- Keep backend APIs, schemas, database contents, and routes unchanged.
- Use Dutch date/time formatting when Dutch is selected.

## Non-Goals
- Do not translate cat names, uploaded filenames, backup filenames, API response payloads, database values, or diagnostic event payload JSON.
- Do not add localized routes such as `/bezoeken` or `/katten`.
- Do not translate firmware/e-paper display copy in this pass unless it is already rendered by the frontend.
- Do not introduce a heavy i18n dependency unless the lightweight approach becomes hard to maintain.

## Key Changes
- Add a small frontend i18n layer with:
  - supported languages: `en`, `nl`
  - translation dictionaries
  - `LanguageProvider`
  - `useLanguage()` or equivalent hook
  - `t(key)` lookup helper
- Store the selected language in `localStorage` using `cat-health-monitor-language`.
- Wrap the app shell with the language provider.
- Add an Admin section for language selection.
- Translate navigation labels, page titles, subtitles, filters, table headers, buttons, modals, status labels, form labels, empty states, alerts, and toast messages.
- Format dates with `en-GB` for English and `nl-NL` for Dutch.
- Keep measurements in `kg` and duration units compact unless a screen needs full prose.

## Admin Language Selector
Add a new Admin section:

English copy:
- Section title: `Language`
- Description: `Choose the language used in this browser.`
- Options: `English`, `Nederlands`

Dutch copy:
- Section title: `Taal`
- Description: `Kies de taal voor deze browser.`
- Options: `English`, `Nederlands`

Behavior:
- Changing the language updates the UI immediately.
- The selection persists after reload.
- The setting is browser-local and does not affect other users/devices.

## Dutch Terminology Draft
These are proposed translations for review before implementation.

### Navigation and Pages
| English | Dutch |
| --- | --- |
| Cat health monitor | Kattengezondheidsmonitor |
| litterbox insights | inzichten |
| Dashboard | Dashboard |
| Visits | Bezoeken |
| Cats | Katten |
| Diagnostics | Diagnostiek |
| Admin | Beheer |
| Full history of litterbox visits | Volledige geschiedenis van kattenbakbezoeken |
| Manage cats and their reference weights | Beheer katten en hun referentiegewichten |
| Operational state for polling, visits, Tuya reconciliation and the e-paper display | Operationele status voor polling, bezoeken, Tuya-reconciliatie en het e-paperdisplay |
| Create portable backups and restore application data from a validated archive | Maak  back-ups en herstel applicatiegegevens uit een gevalideerd archief |

### Common Actions
| English | Dutch |
| --- | --- |
| Add | Toevoegen |
| Add visit | Bezoek toevoegen |
| Add cat | Kat toevoegen |
| Edit | Bewerken |
| Edit visit | Bezoek bewerken |
| Edit cat | Kat bewerken |
| Delete | Verwijderen |
| Delete visit | Bezoek verwijderen |
| Save | Opslaan |
| Save visit | Bezoek opslaan |
| Save cat | Kat opslaan |
| Cancel | Annuleren |
| Retry | Opnieuw proberen |
| Previous | Vorige |
| Next | Volgende |
| Download backup | Back-up downloaden |
| Restore backup | Back-up herstellen |
| Choose backup archive | Back-uparchief kiezen |
| Copy | Kopiëren |

### Visit Fields
| English | Dutch |
| --- | --- |
| ID | ID |
| Cat | Kat |
| Started | Gestart |
| Duration | Duur |
| Weight | Gewicht |
| Source | Bron |
| Actions | Acties |
| Confidence | Betrouwbaarheid |
| Unidentified / visitor | Onbekend / bezoeker |
| Visitor cat | Bezoekende kat |
| Started at | Gestart om |
| Weight (kg) | Gewicht (kg) |
| Duration minutes | Duur in minuten |
| Duration seconds | Duur in seconden |
| Page | Pagina |
| No visits recorded yet | Nog geen bezoeken geregistreerd |
| No visits match this filter | Geen bezoeken voor dit filter |

### Cat Fields
| English | Dutch |
| --- | --- |
| Name | Naam |
| Reference weight | Referentiegewicht |
| Reference weight (kg) | Referentiegewicht (kg) |
| Birthday | Verjaardag |
| Adoption date | Adoptiedatum |
| Active | Actief |
| Inactive | Inactief |
| Profile | Profiel |
| Lifecycle events | Levensloopgebeurtenissen |
| Photo | Foto |
| Change photo | Foto wijzigen |
| Remove photo | Foto verwijderen |
| No cats yet | Nog geen katten |

### Status and Badges
| English | Dutch |
| --- | --- |
| auto | automatisch |
| manual | handmatig |
| unidentified | onbekend |
| ignored | genegeerd |
| suspect | verdacht |
| normal | normaal |
| active | actief |
| inactive | inactief |
| healthy | gezond |
| disconnected | verbroken |
| stale | verouderd |
| backup v1 | back-up v1 |

### Dashboard and Metrics
| English | Dutch |
| --- | --- |
| Visits today | Bezoeken vandaag |
| Latest weight | Laatste gewicht |
| Weight trend | Gewichtstrend |
| Recent visits | Recente bezoeken |
| No recent visits | Geen recente bezoeken |
| Poller is disconnected. Dashboard data may be stale. | Poller is niet verbonden. Dashboardgegevens kunnen verouderd zijn. |
| review in Visits | bekijken bij Bezoeken |
| All | Alles |
| 7 days | 7 dagen |
| 30 days | 30 dagen |
| 90 days | 90 dagen |

### Admin and Backup
| English | Dutch |
| --- | --- |
| Create backup | Back-up maken |
| Restore backup | Back-up herstellen |
| Database records and uploaded files are bundled into one zip archive. | Databasegegevens en geuploade bestanden worden gebundeld in een zip-archief. |
| Upload a backup archive, review its contents, then confirm the restore. | Upload een back-uparchief, controleer de inhoud en bevestig daarna het herstel. |
| No backup archive selected | Geen back-uparchief geselecteerd |
| Created | Aangemaakt |
| Schema | Schema |
| Uploads | Uploads |
| I understand this will replace the current database and uploads. | Ik begrijp dat dit de huidige database en uploads vervangt. |
| Backup download started | Back-updownload gestart |
| Backup archive validated | Back-uparchief gevalideerd |
| Restore completed | Herstel voltooid |

### Diagnostics
| English | Dutch |
| --- | --- |
| Diagnostics summary | Diagnostiekoverzicht |
| Visit diagnostics | Bezoekdiagnostiek |
| Recent visit diagnostics | Recente bezoekdiagnostiek |
| Open visits | Open bezoeken |
| Poller | Poller |
| Event type | Gebeurtenistype |
| Recorded at | Vastgelegd op |
| Payload | Payload |
| No visit diagnostics recorded yet | Nog geen bezoekdiagnostiek vastgelegd |
| Diagnostics summary unavailable | Diagnostiekoverzicht niet beschikbaar |
| Showing recent diagnostics for visit | Recente diagnostiek voor bezoek |

### Toasts and Errors
| English | Dutch |
| --- | --- |
| Failed to load cats. Please try again. | Katten laden is mislukt. Probeer het opnieuw. |
| Failed to delete visit. Please try again. | Bezoek verwijderen is mislukt. Probeer het opnieuw. |
| Failed to load dashboard data | Dashboardgegevens laden is mislukt |
| Visit updated | Bezoek bijgewerkt |
| Visit deleted | Bezoek verwijderd |
| Cat saved | Kat opgeslagen |
| Event deleted | Gebeurtenis verwijderd |
| Please enter a valid date, duration and weight. | Vul een geldige datum, duur en gewicht in. |

## Public Interfaces
- No backend API changes.
- No database migration.
- No route changes.
- Adds a browser-local `localStorage` key: `cat-health-monitor-language`.

## Implementation Notes
- Prefer translation keys over inline strings for visible UI copy.
- Keep enum-like API values unchanged in code and translate only at render time.
- Keep tests stable by using English as the default language.
- Where tests assert visible text, update them to either use the default English copy or wrap with a test language provider when asserting Dutch copy.
- Avoid translating technical endpoint paths such as `/diagnostics/summary` or `/visits/{visit_id}/diagnostics`.

## Test Plan
- Default render uses English when no language is stored.
- Admin language selector changes the UI to Dutch immediately.
- Selected language persists in `localStorage` and is restored after reload.
- Navigation labels render in Dutch after selecting `Nederlands`.
- Visits table headers and action labels render in Dutch.
- Edit visit form renders Dutch field labels, including `Kat`, `Gestart`, `Duur`, `Gewicht`, and `Betrouwbaarheid`.
- Date formatting uses `nl-NL` when Dutch is active.
- Existing page tests remain green with English as the default.

## Review Questions
- Should `Visits` be translated as `Bezoeken`, `Kattenbakbezoeken`, or something else in navigation? 
  SvA Bezoeken
- Should `Diagnostics` be `Diagnostiek`, `Diagnose`, or remain `Diagnostics`? 
  SvA Diagnostiek is goed
- Is `Betrouwbaarheid` the right label for weight confidence, or is `Zekerheid` friendlier? 
  SvA Betrouwbaarheid is beter
- Should `unidentified` be `onbekend`, `niet herkend`, or `ongeidentificeerd`?
  niet herkend
- Should `litterbox insights` be translated, kept English, or replaced with a more natural Dutch tagline?
  inzichten
