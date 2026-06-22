# TODO — Pagent

> Trabajo pendiente que no entra en el flujo "escribir el próximo capítulo".
> Deuda estructural a cerrar antes del Libro II, o descubierta durante el Libro I.

## Alta prioridad

### Token-growth governance — Fase C (diferida)

De la sesión de optimización del bundle. El **seam** (resumen + escena final
verbatim), el **`Realized` log** de seeds y la ventana `RECENT_DETAIL_WINDOW=6`
ya están en producción y recortan el bundle ~27% y acotan su crecimiento. Quedan
dos palancas, **deliberadamente diferidas** porque solo pagan cuando el estado es
grande (acto 2+) y conviene probarlas con datos reales, no especulativamente a
mitad de libro.

**Canon scoping por roster** (el de mayor impacto en ch ~12+, también el de más
riesgo de incongruencia silenciosa):
- [ ] `plan-chapter` emite un manifest de entidades en juego del capítulo
      (personajes/lugares/facciones/magia que el beat sheet nombra).
- [ ] `context.py` carga la ficha completa solo de esas entidades; del resto, una
      línea de roster (nombre + identidad en ~8 palabras).
- [ ] Red de seguridad: roster index SIEMPRE presente + `search-corpus` como
      escape hatch para tirar de una ficha completa on-demand.
- [ ] Activar **cuando canon pese de verdad** (≈ acto 2), para poder testear el
      recorte contra continuidad real. No meterlo dormido antes.

**Filtro de setup en fase write** (ROI modesto, ~2k palabras; baja prioridad):
- [ ] Marcar secciones en `setup.md` (identidad/prosa/POV/longitud vs.
      worldbuilding que el canon ya posee).
- [ ] `context.py` inyecta en fase write solo lo que el canon no absorbió;
      fallback graceful a setup completo si no hay marcas.

### Seeds trans-libro

En la trilogía, varios seeds del Libro I (Lectura en escena, Blanco Falso) pagan
en Libro III. El modelo actual asume `plant_in`/`payoff_in` en el **mismo** libro
(hoy se rotula `Payoff in: Libro III` como texto, sin modelarlo). El nuevo
`Realized` log es el ladrillo que hace esto viable: la historia realizada del seed
viaja con `seeds.md` (nunca comprimido).

- [ ] Extender `Seed` con `trans_book_payoff: list[dict]` (`{book, chapter, note}`)
      + parser.
- [ ] `envelope_for_chapter` consulta también seeds de libros previos de la serie
      con echo/payoff programado para el libro actual.
- [ ] `mark_seed.py` acepta `--book` opcional.
- [ ] Decidir cómo el writer del Libro III hereda los seeds activos del Libro I
      sin recargar el archivo entero (probablemente: filtrar status ≠ `paid_off`).

### Biblia obligatoria en `book-setup`

`references/bible-template.md` y la skill `critique-bible` (audit) ya existen.
Falta solo el gating:
- [ ] `book-setup/SKILL.md` exige `output/<series>/bible.md` antes de bootstrap;
      si falta, ofrece copiar el template y para hasta que el usuario lo rellene.

## Media prioridad

### Audit de consistencia POV / geografía

El outline ya lleva `**POV:**` por capítulo. Falta el check:
- [ ] `audit_plan.py` comprueba que el POV de cada `## Chapter N` concuerda con
      `setup.md §POV distribution`.
- [ ] Geografía: si un lugar es escenario de un capítulo, su nombre debería
      aparecer en `Where/when`; afinar qué cuenta como "mencionado en el plan"
      para que un lugar solo-en-canon no salga como "absent from plan".

### Bugs menores del audit

- [ ] "Magic sections all present" debe distinguir placeholder vacío de contenido
      real (como el fix de source/mechanic).
- [ ] "chapters without any seed activity" es ruidoso (es normal); decidir umbral
      o quitarlo.

## Baja prioridad

### Voice drift detection

Heurístico + revisión manual para detectar cuándo la voz de un POV se vuelve
inconsistente entre capítulos. Útil en la segunda mitad del libro, tras varios
`close-act`.

### Trans-book seed inheritance — UX

Al empezar el Libro II, cómo el writer "siente" qué seeds del Libro I siguen
vivos: `build_context.py` del Libro II lee el `book-summary.md` + `seeds.md` del
Libro I, filtra los `planted`/`echoed-N` no `paid_off`, y los inyecta como
contexto. (Depende de "Seeds trans-libro".)
