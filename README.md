# Forlex Optimizer

**Optimizador completo y 100 % reversible para Windows 10/11 (64 bits).**
393 tweaks en 16 categorías, con respaldo exacto del registro antes de cada cambio y un botón para
deshacerlo todo.

[![Versión 1.0.0](https://img.shields.io/badge/versi%C3%B3n-1.0.0-2f6fed)](../../releases/latest)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-3da639)](LICENSE)
[![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-0078d4)](#requisitos)
[![Sin telemetría](https://img.shields.io/badge/sin%20telemetr%C3%ADa-100%25%20local-2ea043)](#privacidad)

**Sitio oficial: [https://zforlexx.github.io/forlex/](https://zforlexx.github.io/forlex/) — Discord: [discord.gg/vr2rjqFPyG](https://discord.gg/vr2rjqFPyG)**

Forlex Optimizer es una aplicación nativa de escritorio escrita en **C# + WPF (.NET Framework 4.8)** y
distribuida como ejecutable portable: sin instalador, sin servicios en segundo plano y sin conexiones a
servidores propios. Está pensada para jugadores y usuarios avanzados que quieren ajustar Windows con
criterio, ver exactamente qué cambia cada ajuste y poder volver atrás en cualquier momento.

## Descargar

| Archivo | Tamaño | Descripción |
| --- | ---: | --- |
| **[ForlexOptimizer.exe](downloads/ForlexOptimizer.exe)** | 2.32 MB | Recomendado. Ejecutable único: descárgalo, ejecútalo y listo (requiere permisos de administrador). |
| [ForlexOptimizer-1.0.0-portable.zip](downloads/ForlexOptimizer-1.0.0-portable.zip) | 1.48 MB | Paquete portable completo: lanzador `ForlexOptimizer.cmd`, ejecutable, `install.ps1` / `uninstall.ps1`, documentación y licencias. |

- Las versiones publicadas están en **[Releases](../../releases/latest)**; los mismos dos archivos
  quedan en la carpeta [`downloads/`](downloads/) de este repositorio como **espejo** (los binarios se
  sirven desde GitHub, nunca desde una PC).
- Integridad: hashes SHA-256 en [`downloads/SHA256SUMS.txt`](downloads/SHA256SUMS.txt).

### Verificar la integridad (recomendado)

SHA-256 de la versión 1.0.0:

```text
17AAB74C46F2BF0AEA87FDAE6A96D32868C18D2011CD38BE7A85F107EF9B859C  ForlexOptimizer.exe
FBEC04B0C58F7A9B93F9E19A7944C5DA89DFD09FDC83D435396D7A15D3978772  ForlexOptimizer-1.0.0-portable.zip
```

En Windows (PowerShell), desde la carpeta de descarga:

```powershell
Get-FileHash .\ForlexOptimizer.exe -Algorithm SHA256
# El valor de "Hash" debe coincidir exactamente con el de arriba
```

En macOS o Linux, con el archivo `SHA256SUMS.txt` al lado de los binarios:

```bash
sha256sum -c SHA256SUMS.txt
```

## Características

- **393 tweaks en 16 categorías**: Rendimiento/FPS, GPU, Red, CPU/RAM, Energía, Windows, Personalización,
  Segundo plano, Privacidad, Almacenamiento, Periféricos, BIOS y drivers, Priorizar juegos, Drivers de
  mouse, Accesos directos y Optimizar apps. Cada tweak indica su nivel: **Seguro**, **Precaución** o
  **Riesgoso**.
- **Aplicar y revertir con el mismo botón**: antes de tocar el registro se guarda el valor exacto que
  había; «Deshacer» lo restaura tal cual, aunque el tweak ya no exista en el catálogo.
- **Punto de restauración**: opción de crear un punto de restauración de Windows antes de aplicar cambios.
- **Optimizar todo**: perfiles Competitivo, Streaming y Notebook en un clic (los tweaks riesgosos nunca se
  aplican automáticamente).
- **Optimizar gráfica**: detección de NVIDIA / AMD / Intel, con respaldo y restauración de los ajustes.
- **Modo Juego automático**: detecta la biblioteca de Steam, Epic o Battle.net, aplica el perfil al abrir el juego,
  revierte al cerrarlo y guarda el historial de sesiones.
- **Planes de energía**: perfiles propios (Forlex Rendimiento, Notebook Gamer, Silencioso) y control de los
  planes de Windows.
- **Chequeo de PC**: puntaje de salud, cuello de botella, driver de GPU y problemas accionables.
- **Forlex Games**: aim trainer con 7 modos, mira overlay, widget flotante, test de escritura, conversor de
  sensibilidad y filtro de pantalla.
- **Personalización completa**: 5 temas, acento personalizable, fondos, densidad, asistente sin conexión,
  perfil con nivel y logros, y exportar/importar la configuración.
- **Extras**: 31 arreglos de un clic, limpieza con SFC/DISM, desinstalador + gestor de inicio, 12 programas
  recomendados y pruebas de hardware (Hz del mouse, CPS, teclado, mando/drift, USB, monitor, reflejos,
  audio, disco, ForlexBench, ping).

## Requisitos

- **Windows 10 u 11 de 64 bits** (probado en equipo de escritorio).
- **Permisos de administrador** (UAC): la app modifica servicios y el registro de la máquina.
- **.NET Framework 4.8** (incluido en Windows 10 1903 o posterior y en Windows 11).
- No requiere instalación: el ejecutable es portable y guarda sus datos en
  `%LOCALAPPDATA%\ForlexOptimizer`.

## Aviso de SmartScreen

El ejecutable **no está firmado con un certificado comercial** (la firma que incluye es de desarrollo
local), así que Windows puede mostrar el aviso «Windows protegió su PC» / SmartScreen la primera vez que lo
abras. Es habitual en aplicaciones open source recién publicadas.

Para ejecutarlo:

1. Pulsa **Más información**.
2. Pulsa **Ejecutar de todas formas**.

Antes de hacerlo, puedes comprobar el hash SHA-256 de tu descarga y consultar el análisis en VirusTotal
(secciones siguientes). Si tu equipo tiene **Smart App Control / WDAC** activo (por ejemplo, equipos
corporativos), usa el lanzador incluido en el paquete `.zip` (`ForlexOptimizer.cmd`), que carga la app en
memoria y evita el bloqueo del ejecutable directo.

> [!IMPORTANT]
> Descarga Forlex Optimizer únicamente desde este repositorio o desde el sitio oficial. No redistribuyas
> versiones modificadas ni ejecutes copias de origen desconocido.

## Verificación en VirusTotal

Puedes consultar el análisis del ejecutable de la versión 1.0.0 (SHA-256
`17AAB74C46F2BF0AEA87FDAE6A96D32868C18D2011CD38BE7A85F107EF9B859C`) en VirusTotal:

- <https://www.virustotal.com/gui/file/17AAB74C46F2BF0AEA87FDAE6A96D32868C18D2011CD38BE7A85F107EF9B859C>

Si el informe aún no está disponible (porque el archivo se acaba de publicar), puedes subirlo tú mismo a
VirusTotal y comprobar que el SHA-256 que muestra coincide con el de arriba.

## Privacidad

- **Sin telemetría**, sin cuentas y sin servidores propios: la aplicación no envía datos a ningún lado.
- Todo ocurre en tu equipo:
  - Ajustes: `%LOCALAPPDATA%\ForlexOptimizer\settings.json`
  - Tweaks aplicados: `%LOCALAPPDATA%\ForlexOptimizer\state.json`
  - Backups: `%LOCALAPPDATA%\ForlexOptimizer\backups\*.json`
  - Registros: `%LOCALAPPDATA%\ForlexOptimizer\logs\forlex-AAAA-MM-DD.log`
- El asistente integrado funciona sin conexión.

## Seguridad y reversibilidad

- Todo cambio en el registro se respalda **valor por valor** antes de aplicarse; el backup queda en
  `%LOCALAPPDATA%\ForlexOptimizer\backups` y se restaura al revertir.
- Los tweaks por lote (`.reg`) también se respaldan.
- Puedes crear un **punto de restauración** de Windows antes de aplicar cambios.
- Los tweaks **Riesgosos** nunca se aplican automáticamente en «Optimizar todo».

## Estructura del repositorio

```text
forlex/
├─ index.html          Página del proyecto (GitHub Pages, raíz del sitio)
├─ assets/
│  ├─ css/site.css     Estilos (tema oscuro, animaciones, responsive)
│  ├─ js/site.js       Interacciones (galería, lightbox, sonido, contadores)
│  ├─ fonts/           Inter + JetBrains Mono auto-hospedadas (woff2)
│  ├─ img/             Capturas reales del programa en WebP (+ thumbs/)
│  ├─ favicon/         Iconos del sitio
│  ├─ og.jpg           Imagen para redes sociales (1200×630)
│  └─ site.webmanifest
├─ downloads/          Espejo de los binarios publicados (+ SHA256SUMS.txt)
├─ tools/              Scripts de generación y verificación de assets
├─ robots.txt · sitemap.xml
├─ LICENSE             Licencia MIT
└─ .nojekyll           Desactiva el procesado de Jekyll en GitHub Pages
```

## Publicar una nueva versión

El sitio se publica automáticamente desde la rama `main` con GitHub Pages. Los binarios se suben como
assets de un **GitHub Release** con la etiqueta de versión (`v1.0.0`, `v1.1.0`, …); abajo quedan también
como espejo en `downloads/`. Las notas de cada versión se leen en
[Releases](https://github.com/zforlexx/forlex/releases).

## Comunidad y soporte

- **Discord oficial:** <https://discord.gg/vr2rjqFPyG>
  - `#soporte` para dudas y problemas del optimizador.
  - `#trabajos` y `#clientes` para encargos de Minecraft y desarrollo a medida (trabajos de **pago ($)**).
  - `#anuncios` para novedades de versiones.
- Para reportar un fallo del optimizador, indica tu versión de Windows, el tweak implicado y, si puedes,
  adjunta el log de `%LOCALAPPDATA%\ForlexOptimizer\logs\`.

## Licencia y créditos

- Proyecto bajo licencia **MIT**: consulta [`LICENSE`](LICENSE).
- El catálogo de datos y parte del conocimiento de tweaks se derivaron de **CeitoTweaks** (licencia MIT),
  de ceitoooo; la implementación (motor, interfaz y servicios) es original.
- Los iconos son **Lucide** (licencia ISC).
- Los avisos completos de terceros están en `docs/THIRD_PARTY_NOTICES.md` dentro del paquete portable.
- Microsoft, NVIDIA, AMD e Intel son marcas de sus respectivos dueños; este proyecto no está afiliado a
  ellos.

---

Hecho con cariño para la comunidad de jugadores hispanohablantes.
