# Sicherheitsanalyse pool-backend

Stand: Oktober 2026, Branch `claude/intelligent-edison-qgr8fz`.

Untersucht wurden alle Routen in `server.go`, die Handler in `handlers/`, die Berechtigungsprüfungen in `models/` und `dao/` sowie die genutzten Teile von `vcago` v1.5.20 (Auth, Cookies, Filter, GridFS). Es gibt keine automatisierten Tests im Repository. Die Fixes sind deshalb nur kompiliert (`go build`, `go vet`) und nicht gegen eine Datenbank getestet.

Rollen-Begriffe:
- **Mitarbeitende**: System-Rollen `admin`, `employee` und `pool_employee`
- **ASP**: Inhaber einer Pool-Rolle wie `asp`, `finance`, `network`, `operation` usw.

Jede Fundstelle mit Fix hat einen eigenen Commit.

## Übersicht

| # | Schwere | Fundstelle | Commit |
|---|---|---|---|
| 1 | Kritisch | Standard-Secrets `JWT_SECRET` / `API_KEY` = `secret` | `0217aac` |
| 2 | Kritisch | Admin-Routen ohne Authentifizierung bei `API_TEST_LOGIN` | `05e118b` |
| 3 | Hoch | Pool-Rollen crew-übergreifend vergeben und entziehen | `79bdfdc` |
| 4 | Hoch | Deposits: fremde Crews, Selbstbestätigung, fremde Units | `fb9bb2b` |
| 5 | Hoch | Belege (Receipts) aller Crews lesbar, anlegbar, löschbar | `deb70fd` |
| 6 | Hoch | Avatar-Endpunkt liefert beliebige GridFS-Dateien (auch Belege) | `210431c` |
| 7 | Hoch | Takings: Sources fremder Crews ändern oder löschen | `515124c` |
| 8 | Hoch | Teilnahmen: jeder kann jede Teilnahme ändern | `2ce5b58` |
| 9 | Hoch | Rundmails: Absender frei wählbar, fremde Events anschreibbar | `42c53bd` |
| 10 | Mittel | Crew-Filter „fail-open“ für Nutzer ohne Crew | `606170a` |
| 11 | Mittel | `GET /users/:id`: ASPs lesen Profildaten aller Crews | `a4609a9` |
| 12 | Mittel | Öffentliches `GET /organisations` zeigt Geburtsdatum | `6b3fd11` |
| 13 | Mittel | Validierungsfehler werden ignoriert | `462c181` |
| 14 | Mittel (Bug) | `ActiveReject` setzt NVM des ASP statt des Nutzers zurück | `d09fee7` |
| 15 | Niedrig | Token-Refresh stellt Token für leeren Nutzer aus | `cb7500f` |
| 16 | Niedrig | Mass-Assignment bei Adresse und Crew-Wechsel | `a8ccd33` |
| 17 | Niedrig | Nil-Pointer-Panic in Goroutine beendet den Server | `91dbe08` |
| 18–25 | Hinweis | Empfehlungen ohne Commit | – |

---

## 1. Kritisch: Standard-Secrets für JWT und API-Key

**Wo:** `vcago/auth_token.go`, `vcago/key_auth.go`. Wenn die Variablen fehlen, gilt `Settings.String("JWT_SECRET", "w", "secret")` bzw. `"API_KEY"`.

**Problem:** Sind `JWT_SECRET` oder `API_KEY` nicht gesetzt, nutzt vcago den Wert `secret` und gibt nur eine Warnung aus. In `example.env` fehlen beide Variablen.

**Angriff:** Mit dem Secret `secret` signiert ein Angreifer ein eigenes `access_token`-Cookie (HS256) mit `system_roles: [{name: "admin"}]`. Damit hat er vollen Admin-Zugriff. Mit `Authorization: Bearer secret` erreicht er die Import-Routen und `GET /v1/users/api_key/:id` (vollständige Nutzerdaten inklusive Adresse).

**Fix (`0217aac`):** Der Server startet nicht, wenn eines der beiden Secrets fehlt, `secret` lautet oder kürzer als 32 Zeichen ist. Beide Variablen sind jetzt in `example.env` dokumentiert.

**Zusätzlich empfohlen:**
- Den Default in vcago selbst auf „Fehler“ (`"e"`) umstellen.
- Für Access- und Refresh-Token getrennte Secrets verwenden.

## 2. Kritisch: Admin-Routen und Test-Login

**Wo:** `server.go` und `handlers/token/login.go` (`LoginAPI`).

**Problem:** Mit `API_TEST_LOGIN=true` werden zwei Dinge aktiv:
- `POST /v1/auth/testlogin` meldet jeden Nutzer nur anhand seiner E-Mail-Adresse an, ohne Passwort.
- `/admin/users`, `/admin/users/role` und `/admin/crews` sind ohne jede Authentifizierung erreichbar. Darüber lassen sich Nutzer anlegen, lesen und löschen sowie Pool-Rollen vergeben.

**Angriff:** Ist das Flag versehentlich in Stage oder Produktion gesetzt, reicht die E-Mail-Adresse eines Admins für eine vollständige Übernahme.

**Fix (`05e118b`):**
- Die Admin-Routen erfordern jetzt den API-Key.
- Beim Start erscheint eine deutliche Warnung, wenn der Test-Login aktiv ist.

Der Test-Login selbst bleibt als Entwicklungswerkzeug bestehen. Das Flag darf außerhalb lokaler Umgebungen nie gesetzt werden. Am besten prüft die Deploy-Pipeline das.

## 3. Hoch: Pool-Rollen crew-übergreifend vergeben und entziehen

**Wo:** `models/role.go` (`RolesPermission`, `RolesDeletePermission`), `models/role_history.go` (`RolesHistoryPermission`), `dao/role.go`.

**Problem:** Geprüft wurde nur, ob der Ausführende die Rolle selbst hat. Die Crew des Zielnutzers spielte keine Rolle.

**Angriff:**
- Ein `asp` aus Crew A macht über `POST /v1/users/role/bulk` beliebige Nutzer aus Crew B zu `asp`.
- Ein `finance`-ASP aus Crew A entzieht dem Finanz-ASP aus Crew B die Rolle.
- Ein `DELETE /v1/users/role` ohne `user_id` traf den ersten Nutzer und die erste passende Rolle in der Collection, weil leere Filterwerte verworfen werden (siehe #10).

**Fix (`79bdfdc`):**
- Nicht-Mitarbeitende dürfen Rollen und ASP-Nominierungen nur für Mitglieder der eigenen Crew ändern.
- Anfragen ohne `user_id` oder `role` werden abgelehnt.

## 4. Hoch: Deposits

**Wo:** `dao/deposit.go` (`DepositInsert`, `DepositUpdate`), `models/deposit.go`.

**Probleme:**
- `DepositUpdate` lud das Deposit nur per ID, ohne Crew-Filter. `crew_id` und `organisation_id` kamen aus dem Request. Ein `finance`-ASP konnte so Deposits anderer Crews ändern.
- Nicht-Mitarbeitende konnten `status: "confirmed"` selbst setzen. Bisher wurde nur verhindert, ein bereits bestätigtes Deposit zu ändern. Die Bestätigung schließt die Events und überträgt Event, Taking und Teilnahmen ins CRM.
- Deposit-Units wurden nur per `_id` aktualisiert. Units fremder Deposits ließen sich verschieben (`deposit_id`) und Beträge ändern.
- `DepositInsert` prüfte die Crew nur über die Units. Ein Deposit ohne Units ließ sich für jede Crew anlegen und führte zudem zu einem Panic bei `d[0]`, weil `d != nil` immer wahr war.
- Negative Beträge wurden akzeptiert.

**Fix (`fb9bb2b`):**
- Das Deposit wird mit dem Berechtigungsfilter geladen.
- Für Nicht-Mitarbeitende werden Crew und Organisation aus der Datenbank übernommen.
- Nur Mitarbeitende dürfen `confirmed` setzen.
- Units müssen zum Deposit gehören.
- `DepositInsert` erfordert die eigene Crew.
- Negative Beträge werden abgelehnt.

**Bitte prüfen:** Der Fix nimmt an, dass `confirmed` nur von Mitarbeitenden gesetzt wird, also von der Finanzabteilung nach Geldeingang. Falls Crews ihre Deposits selbst bestätigen sollen, muss diese Zeile angepasst werden.

## 5. Hoch: Belege (Receipts)

**Wo:** `dao/receipts.go`. Im Code stand jeweils nur `//permission check`, ohne Prüfung.

**Problem:** Hochladen, Herunterladen (einzeln und als ZIP) und Löschen prüften nur die Rolle `finance`, nicht die Crew des Deposits.

**Angriff:** Ein `finance`-ASP einer beliebigen Crew lädt die Belege aller Deposits herunter, löscht sie oder fügt fremden Deposits Dateien hinzu.

**Fix (`deb70fd`):** Das Deposit des Belegs muss über den Berechtigungsfilter erreichbar sein, wie bei den Deposits selbst.

## 6. Hoch: Avatar-Endpunkt liefert beliebige Dateien

**Wo:** `handlers/token/avatar.go` (`GetByID`, `Delete`, `Upload`).

**Problem:** `GET /v1/users/avatar/img/:id` lud jede Datei des Standard-GridFS-Buckets anhand ihrer ID. Belege liegen im selben Bucket (`vmdb.Database.UploadFile`).

**Angriff:** Jeder angemeldete Nutzer, der eine Beleg-ID kennt, lädt den Beleg über den Avatar-Endpunkt herunter. Die IDs stehen in den Deposit-Antworten.

**Weitere Fehler:**
- `Delete` filterte das Nutzerdokument nach `_id = Avatar-ID` und `user_id`. Das trifft nie, deshalb schlug Löschen immer fehl.
- `Upload` hatte kein Größenlimit, keine Typprüfung und schrieb die Avatar-Referenz, bevor die Datei gespeichert war.

**Fix (`210431c`):**
- Es werden nur Dateien ausgeliefert, die der Avatar eines Nutzers sind.
- Der Löschfilter ist korrigiert.
- Uploads sind auf 5 MB und Bilddateien begrenzt.
- Die Referenz wird erst nach erfolgreichem Upload gespeichert.

## 7. Hoch: Takings und Sources

**Wo:** `dao/taking.go` (`TakingInsert`, `TakingUpdate`).

**Probleme:**
- In `TakingUpdate` wurden Sources nur per ID geändert oder gelöscht. Die Sources enthalten die Einnahmebeträge. Ein `finance`-ASP konnte Sources fremder Takings ändern oder löschen und über `taking_id` umhängen.
- `crew_id` und `organisation_id` kamen aus dem Request. Ein Taking ließ sich so in eine andere Crew verschieben.
- `TakingInsert` akzeptierte jede Crew.

**Fix (`515124c`):**
- Source-Änderungen sind auf Sources des geladenen Takings beschränkt.
- Crew und Organisation bleiben für Nicht-Mitarbeitende unverändert.
- Beim Anlegen ist die eigene Crew Pflicht.

## 8. Hoch: Teilnahmen (Participations)

**Wo:** `models/participation.go` (`ParticipationUpdatePermission`).

**Probleme:**
- Der `switch` hatte keinen `default`-Zweig. Bei jedem anderen Status, zum Beispiel einem leeren, gab es keine Prüfung. Jeder angemeldete Nutzer konnte so jede Teilnahme überschreiben, mitsamt Status und Kommentar (`PUT /v1/events/participation`).
- Inhaber von `network`, `operation` oder `education` konnten Teilnahmen an Events aller Crews bestätigen oder ablehnen.

**Fix (`2ce5b58`):**
- Unbekannte Status dürfen nur Mitarbeitende setzen.
- Crew-ASPs entscheiden nur über Events der eigenen Crew.

**Nebenbefund ohne Fix:** `ParticipationUpdate.PermittedFilter` prüft `token.PoolRoles.Validate("admin;employee;pool_employee")`. Pool-Rollen enthalten diese Namen nie, der Filter ist also falsch. Er wird derzeit aber nicht verwendet.

## 9. Hoch: Rundmails mit falschem Absender

**Wo:** `dao/message.go` (`MessageUpdate`), `models/message.go` (`MessageEventPermission`).

**Probleme:**
- Beim Anlegen setzt der Server für Nicht-Mitarbeitende Absender und Postfach fest auf die Crew. `MessageUpdate` übernahm danach aber alle Felder aus dem Request, also `from`, `mailbox_id`, `user_id` und `type`.
- Ein ASP konnte so einen Entwurf auf einen beliebigen Absender ändern, etwa eine Adresse der Geschäftsstelle, und per `GET /v1/mails/message/send_cycular/:id` verschicken. Das ermöglicht Phishing im Namen von Viva con Agua.
- Jeder ASP konnte die Teilnehmenden beliebiger Events aller Crews anschreiben.

**Fix (`42c53bd`):**
- Für Nicht-Mitarbeitende bleiben Absender, Postfach, Eigentümer und Typ aus der Datenbank erhalten.
- Crew-ASPs schreiben nur an Events der eigenen Crew.

**Empfehlung:** Bereits versendete Nachrichten (`type: outbox`) lassen sich erneut versenden. `SendCycular` sollte nur Entwürfe (`draft`) akzeptieren.

## 10. Mittel: Crew-Filter versagen offen („fail-open“)

**Wo:** Alle `PermittedFilter` mit `filter.EqualString(..., token.CrewID)`.

**Problem:** `vmdb.Filter.EqualString` verwirft leere Werte. Für Nutzer ohne Crew (`token.CrewID == ""`) fiel die Crew-Einschränkung dadurch komplett weg, und der Filter traf alle Dokumente. Betroffen waren unter anderem:
- `GET /v1/users/crew/public` hat keine Rollenprüfung. Jeder Nutzer ohne Crew konnte alle Nutzer auflisten und über `email=` prüfen, ob E-Mail-Adressen existieren.
- `GET /v1/crews/:id` und `/crews/own` lieferten die erste Crew der Collection.
- Die Role-History aller Crews.
- Bei ASPs ohne Crew (z. B. veraltetes Token nach Crew-Austritt): Deposits, Takings, Events, Teilnahmen und Rundmail-Empfänger aller Crews. In `$or`-Filtern machte das leere Teildokument `{}` den ganzen Filter wirkungslos.

**Fix (`606170a`):** Die neue Funktion `models.CrewFilter` trifft bei leerer Crew nichts. Sie wird in allen Crew-Einschränkungen für Nicht-Mitarbeitende verwendet.

## 11. Mittel: `GET /users/:id` crew-übergreifend

**Wo:** `dao/users.go` (`UsersUserGetByID`).

**Problem:** ASPs dürfen Nutzer auflisten, die Liste ist auf ihre Crew beschränkt. Der Einzelabruf filterte dagegen nur per ID.

**Angriff:** Ein ASP liest E-Mail, Telefon, Geschlecht und Geburtsdatum beliebiger Nutzer aller Crews. Das ist ein DSGVO-relevantes Datenleck.

**Fix (`a4609a9`):** Nicht-Mitarbeitende sehen nur Nutzer der eigenen Crew.

## 12. Mittel: Geburtsdatum am öffentlichen Endpunkt

**Wo:** `models/organisation.go` (`OrganisationPipeline`). Die Route `GET /v1/organisations` ist ohne Login erreichbar.

**Problem:** Die Antwort enthält den Default-ASP jeder Organisation als `UserContact`, mit Profil und damit dem Geburtsdatum.

**Fix (`6b3fd11`):** Die Geburtsdatums-Felder werden in der Pipeline entfernt.

**Bitte prüfen:** E-Mail-Adresse und Name des Default-ASP bleiben öffentlich. Das ist vermutlich als Kontaktangabe gewollt.

## 13. Mittel: Ignorierte Validierungsfehler

**Wo:** `handlers/admin/admin_roles.go`, `handlers/token/roles.go`, `handlers/token/role_history.go`, `handlers/token/login.go`.

**Problem:** `if c.BindAndValidate(body); err != nil` weist den Fehler nicht zu, die Bedingung ist also nie wahr. Ungültige oder fehlerhafte Requests wurden verarbeitet.

**Fix (`462c181`):** `if err = c.BindAndValidate(body); err != nil`.

## 14. Mittel (Logikfehler): `ActiveReject` trifft den Falschen

**Wo:** `dao/user_active.go` (`ActiveReject`).

**Problem:** `nvmReject(ctx, token.ID)` setzt die NVM des ablehnenden ASP zurück. Die NVM des abgelehnten Nutzers bleibt bestehen.

**Fix (`d09fee7`):** `nvmReject(ctx, i.UserID)`.

## 15. Niedrig: Token-Refresh bei Datenbankfehlern

**Wo:** `handlers/token/login.go` (`Refresh`).

**Problem:** `err != nil && vmdb.ErrNoDocuments(err)` brach nur bei „nicht gefunden“ ab. Bei jedem anderen Datenbankfehler wurden neue Tokens für einen leeren Nutzer ausgestellt und der Fehler verschluckt.

**Fix (`cb7500f`):** Jeder Fehler beendet den Refresh.

## 16. Niedrig: Mass-Assignment bei Adresse und Crew-Wechsel

**Wo:** `dao/address.go` (`AddressUpdate`), `dao/user_crew.go` (`UserCrewUpdate`).

**Probleme:**
- `user_id` kam aus dem Request. Ein Nutzer konnte seine Adresse einem anderen Nutzer zuordnen.
- Crew-Name und Crew-E-Mail kamen aus dem Request und landeten im Nutzerdokument und im Access-Token.
- Ein leeres `crew_id` traf die erste Crew der Collection.

**Fix (`a8ccd33`):**
- Bei der Adresse wird `user_id` immer auf den eigenen Nutzer gesetzt.
- Name und E-Mail werden aus der Crew übernommen.
- `crew_id` ist Pflicht.

## 17. Niedrig: Server-Absturz durch Panic in Goroutine

**Wo:** `dao/deposit.go` (`DepositUpdate`, `DepositSync`).

**Problem:** Schlägt `TakingGetByID` fehl, wird trotzdem `taking.EditorID` gesetzt. Das ist ein Nil-Pointer-Zugriff. `net/http` fängt Panics in Handlern ab, aber nicht in Goroutinen. Der ganze Prozess würde beendet.

**Fix (`91dbe08`):** Bei Fehlern wird das Taking übersprungen.

---

## Empfehlungen ohne Commit

18. **MongoDB ohne Authentifizierung.**
    - `.k8s/mongodb_deployment.yml` startet MongoDB ohne Benutzer und Passwort. Der Schutz hängt allein an der Netzwerk-Isolation im Cluster.
    - `docker-compose.dev.yml` veröffentlicht Port 27017 auf dem Host.
    - Empfehlung: Auth aktivieren (`MONGO_INITDB_ROOT_USERNAME/PASSWORD` über Infisical), eine NetworkPolicy für den DB-Service setzen und den Port in der Dev-Umgebung nur an `127.0.0.1` binden.

19. **Nicht widerrufbare Tokens.**
    - Access-Tokens gelten 15 Minuten und enthalten Rollen und Crew. Entzogene Rollen oder ein Crew-Wechsel wirken also erst nach Ablauf.
    - Refresh-Tokens gelten 24 Stunden und lassen sich nicht widerrufen. Logout löscht nur die Cookies.
    - Zugriff und Refresh nutzen dasselbe Secret.
    - Empfehlung: Rollen für kritische Aktionen (Finanzen, Rollen) aus der Datenbank laden und eine Token-Version pro Nutzer speichern.

20. **Event-Update übernimmt alle Felder.** `EventUpdate` übernimmt sämtliche Felder aus dem Request (`crew_id`, `event_asp_id`, `creator_id` usw.). Ein Event-ASP könnte das Event so einer anderen Crew zuordnen. Felder, die nur Mitarbeitende ändern dürfen, sollten aus dem gespeicherten Event übernommen werden.

21. **Teilnahme an nicht veröffentlichten Events.** `ParticipationInsert` prüft weder den Event-Status noch den Bewerbungszeitraum. Bewerbungen auf nicht veröffentlichte Events sind möglich.

22. **Data Races.** Goroutinen schreiben in die benannte Rückgabe `err` des Handlers, z. B. `go func() { if err = dao.IDjango.Post(...) ... }()`, nachdem der Handler schon zurückgekehrt ist. Sie sollten lokale Variablen verwenden.

23. **vcago-Server.**
    - `NewServer` setzt `Debug = true` und registriert keine `Recover`-Middleware.
    - Fehlt `COOKIE_SECURE`, ist der Default zwar `true`, aber nur mit Warnung.

24. **GridFS-Löschen unvollständig.** `DeleteFile` in vcago und `Avatar.Delete` löschen nur einen Chunk (`DeleteOne`). Dateien über 255 KB hinterlassen verwaiste Chunks.

25. **Fehlende Tests.** Für Berechtigungslogik gibt es keine Tests. Gerade die `PermittedFilter`-Funktionen in `models/` sind rein und ohne Datenbank testbar. Tabellentests pro Rolle (Mitarbeitende, ASP der eigenen bzw. fremden Crew, Nutzer ohne Crew) hätten #3, #8, #10 und #11 verhindert.
