# Open questions (rolling)

> Threads discussed in chat that did NOT get resolved. Surface these at
> the start of the next session. The agent appends as discussions happen
> and marks items resolved (strike-through) when they close.

## Pendientes

- (2026-06-22, ch 1) **`portaluz-coreografia` se sembró en ch 1 (la moneda), pero `seeds.md` lo agenda en `Plant in: 2`.** Avancé su `Status` a `planted` y dejé el resto del seed intacto. ¿Actualizar "Plant in: 1 / Echo in: 2, 12, 18" para que el registro cuadre, o mantener ch 2 como "plant" nominal?
- (2026-06-22, ch 1) **La skill `compile-book` referencia `scripts/build_epub.py` y `send_to_kindle.py` que no existen** en el repo (solo SKILL.md). El EPUB del ch 1 se generó con `pandoc` directo y el envío se hizo con un emisor `smtplib` ad-hoc. ¿Crear esos scripts de verdad para que la skill funcione sola?
- (2026-06-22, ch 1) `.env`: `SMTP_FROM` quedó vacío (se usó `SMTP_USER` como remitente). Verificar que `abetatos@gmail.com` está en la lista de remitentes aprobados de Amazon o el envío a Kindle se descarta en silencio.

## Resueltos (archivo)

- (none yet)
