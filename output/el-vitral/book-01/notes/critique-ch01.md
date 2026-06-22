# Critique — chapter 1 ("La sombra corta")

**Word count:** actual=7247 target=[8000, 12000] (in_range según el script; 91% del piso)
**Verdict:** REJECT → **PASS tras revise-chapter (polish)** — ver §Revisión al final.

> Nota de método: REJECT es mecánico (existe ≥1 MUST). Los tres MUST son
> arreglables con `revise-chapter`; no hay que reescribir la escena. La
> trama, los beats y la estructura están bien.

## MUST fix

- **[Contradicción de canon — detección de la sombra a mediodía]**
  El azul (Doral) detecta el defecto de la sombra **a mediodía**:
  > "miró el suelo a los pies de Bruno, el charco de sombra del mediodía,
  > y frunció algo entre las cejas... como si en aquel charco hubiera algo
  > de menos, un dedo de sombra que faltara, un borde que se diluía"
  `canon/characters.md` es explícito: *"A mediodía, con luz alta, o bajo
  techo, el efecto es inapreciable."* El defecto SOLO asoma con luz
  rasante (sombra larga). **Dirección:** quitar la detección de mediodía.
  Que la pausa de mediodía de Doral sea por otra cosa (el tic de la
  pausa-antes-de-responder, el porte del pardo) o un simple vistazo; la
  revelación de la sombra debe quedar **solo** en la escena de la tarde,
  que ya está bien escrita ("la luz de la tarde... caía rasante... no
  cortaba del todo. Se deshilachaba"). *(Coherencia menor a decidir: el
  canon dice "Doral lo ve al alba en ch 1"; aquí lo ve al ocaso. Ambas
  son luz rasante/sombra larga, así que la regla física se respeta —
  pero update-canon o el autor deben reconciliar "alba" vs "tarde".)*

- **[Regla dura de estilo — narrador aforístico]**
  `setup.md §Prose constraints` prohíbe explícitamente las
  frases-sentencia y máximas generales. Hay al menos dos:
  > "un callo se hereda igual que una casa: trabajando lo mismo en el
  > mismo sitio."
  > "el trabajo era el sitio donde Bruno mejor estaba, porque en el
  > trabajo un hombre no es nadie más que sus manos."
  Ambas son máximas de narrador ("un hombre...", "un callo se hereda...").
  **Dirección:** reescribir en concreto, pegadas al cuerpo de Bruno, sin
  el giro sentencioso. El callo basta como dato físico (el callo del
  padre en el mismo canto de la mano) sin la moraleja.

- **[Regla dura de estilo — polisíndeton (cascada y… y… y…)]**
  `setup.md` prohíbe las cascadas encadenadas con *y… y… y…*. Caso claro:
  > "El sudor le bajaba por el espinazo y se le secaba con el aire, y el
  > polvo del grano se le pegaba a los brazos mojados y le picaba en los
  > codos, y nada de eso era malo; era el trabajo."
  **Dirección:** romper en dos o tres frases. (La anáfora deliberada
  "y vio... y vio... y vio" del derrumbe es un recurso puntual permitido
  —ver CONSIDER— pero conviene que sea el único de su tipo en el cap.)

## SHOULD fix

- **[Seed `portaluz-coreografia` — siembra demasiado larga]** El plant
  está bien hecho y es oblicuo, pero la meditación sobre el pliegue ocupa
  un párrafo entero (~150 palabras: *"un paño no se recogía así... una
  túnica que ninguna tela hacía sola repetida mil veces"*). Roza convertir
  la semilla en el propósito de la escena (anti-telegrafiado: la semilla
  no debe *ser* la escena). **Dirección:** recortar a la mitad; que el
  pliegue improbable + la luz demasiado limpia queden como dos apuntes,
  no como un análisis.

- **[Seed `negro-progenitor-trace` — adelanto blando]** El plant formal
  es ch 3, pero en ch 1 ya aparece el rasgo canónico de las manos pálidas
  del padre:
  > "más pálida de lo que una mano de campo tenía derecho a ser"
  Es coherente con canon ("Bruno se acuerda como dato sin entenderlo"),
  pero adelanta material reservado al ch 3. **Decisión del autor:** o se
  corta de ch 1 (dejando solo la manta como "mención suave de ausencia",
  que es lo que pide el beat sheet), o se acepta como eco muy temprano y
  se anota para no repetirlo igual en ch 3.

- **[Interioridad filtrada / casi-tesis]** Dos lugares "dicen" en vez de
  dejar que la acción signifique:
  > "lo entendió sin palabras, en el cuerpo, mirándose las manos frías—
  > era peor que cualquier cosa"
  > "Lo entendió mirando el agua quieta: que la aldea no lo iba a echar a
  > gritos... iba a vaciar el sitio donde él estaba."
  **Dirección:** quitar el "lo entendió que" y dejar la imagen (las manos
  frías; la pila llena intacta) cargando el sentido sola.

## CONSIDER

- **Seed `aceleracion-reloj` repartido en 4-5 toques** (verde claro del
  telar + trigo bajo + vidriera apagada + grano huero + el gris que tarda
  en hacerse rojo). El envelope lo pide "como ambiente", así que difuso
  es legítimo, pero está en el límite alto. Si se quiere afinar, bajar a
  2-3 toques.
- **Cicatriz del pulgar:** canon dice **izquierdo** (registrado en su
  archivo de Lectura, payoff en ch 24). El texto no especifica el lado.
  Añadir "izquierdo" para que el payoff lejano enganche.
- **Línea de Doral** *"La luz que te atraviesa, muchacho"*: bonita pero
  algo lírica para un jurista y verbaliza el mecanismo (la luz lo
  atraviesa = vacío). No es leak de Truth 1 (Doral está encantado, no
  entiende), pero conviene dejarla más oblicua.
- **Narración proléptica del nombre de Doral** ("se llamaría Doral... se
  lo diría al día siguiente"): pequeño paso fuera del saber presente de
  Bruno en close third. Aceptable, pero es distancia.
- **"como si" ×4** — variar o comprometer la imagen (anti-pattern "it was
  as if").
- **Marcadores EXPAND 1/EXPAND 2** siguen en el archivo (scaffold del
  repo). Visibles al leer/comparar y en Kindle; se limpiarán en la pasada
  de cleanup. No es un problema de prosa.

## Flags para update-canon (hechos inventados a promover — NO arreglar ahora)

- **Padre = "Mateo, el del muro norte"**, varón, leído como marrón, que
  "llegó" a Vega Parda hace ~18 años y murió. (El progenitor era TODO
  abierto: identidad/sexo/oficio. Promover, marcándolo como el progenitor
  Negro.)
- **Texturas de aldea nuevas:** Sela (vieja, teje el comunal), los Cobre
  (familia; el niño salvado), don Mela (cura), el Tuerto (vecino).
- **Geografía interna de Vega Parda:** muro norte (los que llegaron /
  pobres) vs muro del sol (los que dan); el comunal bajo cobertizo con
  viga maestra de castaño; la pila/pilón de la plaza; la única vidriera
  en el muro del altar. (Coherente con los anclajes de `canon/world.md`:
  telar comunitario + pozo de agua fría.)

## What works

- **Apertura por un sentido no visual** (el frío de la piedra) y textura
  de labor sostenida (el agua al alba, la siega) — close third disciplinado,
  cero head-hopping.
- **La anomalía del "no calor":** el cap enseña la regla "la magia cuesta
  calor" por uso (el recuerdo del cobrador rojo) y luego la rompe con las
  manos frías de Bruno. Worldbuilding por uso, misterio sin filtrar Truth 2
  (el coste de recuerdos queda correctamente oculto).
- **La aldea sellándose** (amuletos puerta a puerta, la pila llena que
  nadie vuelve a tocar) — el coste *social* del poder mostrado en oblicuo,
  con eco del motivo del ordeño ("vaciar el sitio donde él estaba").
- **La manta doblada por la mitad larga** conservada como rareza heredada
  sin explicarla — disciplina de semilla limpia (salvo el desliz de las
  manos pálidas, arriba).
- **El incidente incitador** involuntario, desproporcionado, "visto", y
  nadie celebra — exactamente la intención del beat sheet: el poder como
  exposición, no como gloria. La ironía madre (Doral se fascina donde el
  pueblo retrocede) encendida ya.

---

## Revisión (revise-chapter --mode polish) — re-crítica

**Nuevo recuento:** actual=7101 target=[8000,12000] (in_range, 89%)
**Nuevo verdict:** PASS (0 MUST, los SHOULD resueltos; quedan solo CONSIDER de gusto)

Ediciones aplicadas (11):

**MUST (3) — resueltos:**
- Sombra a mediodía → Doral ahora se fija en Bruno por su **manera de
  mirar** (quieto, calculando), no por la sombra. La detección de la
  sombra queda **solo** en la escena de la tarde (luz rasante), coherente
  con canon. Ajustada también la línea "dos cosas se juntan" y los ecos
  posteriores ("mirado su sombra" → "se había parado en él").
- Aforismo "un callo se hereda igual que una casa…" → reescrito concreto.
- Aforismo "…un hombre no es nadie más que sus manos" + polisíndeton de
  la siega → frase partida, sin máxima.

**SHOULD (3) — resueltos:**
- Plant `portaluz-coreografia`: párrafo del pliegue recortado a la mitad.
- `negro-progenitor-trace`: cortado el rasgo de las manos pálidas del
  padre (se reserva para el plant formal del ch 3).
- Dos casi-tesis ("lo entendió que…") → la imagen carga sola.

**CONSIDER barato:** añadido "pulgar **izquierdo**" (canon, payoff ch 24).

**CONSIDER no tocados (gusto, opcionales):** anáfora "y vio… y vio…" del
derrumbe (recurso puntual permitido); "como si" ×4; la línea lírica de
Doral; prolepsis del nombre de Doral. Ninguno bloquea.

**Flags para update-canon siguen vigentes** (Mateo/padre, Sela, los Cobre,
don Mela, muro norte/del sol, comunal, pila).
