# Integración Fermax Cloud para Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/piKolin/homeassistant-fermax_cloud.svg?style=flat-square)](https://github.com/piKolin/homeassistant-fermax_cloud/releases)
[![GitHub Activity](https://img.shields.io/github/commit-activity/y/piKolin/homeassistant-fermax_cloud.svg?style=flat-square)](https://github.com/piKolin/homeassistant-fermax_cloud/commits)
[![License](https://img.shields.io/github/license/piKolin/homeassistant-fermax_cloud.svg?style=flat-square)](LICENSE)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/piKolin/homeassistant-fermax_cloud/graphs/commit-activity)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1+-blue.svg)](https://www.home-assistant.io/)

Integración de Home Assistant para controlar videoporteros Fermax a través de su API Cloud.

> 🇪🇸 Documentación en Español

---

## Características

- ✅ Autenticación OAuth2 con gestión automática de tokens
- ✅ Descubrimiento automático de dispositivos y puertas
- ✅ Botones para abrir puertas desde Home Assistant
- ✅ Sensores de estado de conexión y dispositivo
- ✅ Sensores de señal WiFi
- ✅ Compatible con HACS
- ✅ Configuración mediante interfaz gráfica
- ✅ Soporte para múltiples dispositivos (Sin testear)
- ✅ Traducciones en español e inglés

## Instalación

### Vía HACS (Recomendado)

1. Abre HACS en Home Assistant
2. Ve a "Integraciones"
3. Haz clic en el menú de tres puntos (arriba a la derecha)
4. Selecciona "Repositorios personalizados"
5. Añade la URL de este repositorio
6. Busca "Fermax Cloud" e instala
7. Reinicia Home Assistant

### Manual

1. Copia la carpeta `custom_components/fermax_cloud` a tu directorio `custom_components` de Home Assistant
2. Reinicia Home Assistant

## Configuración

1. Ve a **Configuración** → **Dispositivos y servicios**
2. Haz clic en **+ Añadir integración**
3. Busca **Fermax Cloud**
4. Introduce tu email y contraseña de Fermax Cloud
5. La integración descubrirá automáticamente tus dispositivos

## Entidades Creadas

Para cada dispositivo Fermax, la integración crea:

### Botones
- **Abrir Puerta**: Un botón por cada puerta visible configurada en tu dispositivo

### Sensores
- **Estado de Conexión**: Muestra si el dispositivo está conectado
- **Estado del Dispositivo**: Muestra el estado de activación
- **Tipo de Dispositivo**: Muestra el modelo del dispositivo
- **Señal Inalámbrica**: Muestra la intensidad de la señal WiFi (si está disponible)

### Sensores Binarios
- **Conectado**: Indica si el dispositivo está conectado
- **Activado**: Indica si el dispositivo está activado

## Uso en Automatizaciones

### Abrir puerta al llegar a casa

```yaml
automation:
  - alias: "Abrir puerta al llegar"
    trigger:
      - platform: zone
        entity_id: person.tu_nombre
        zone: zone.home
        event: enter
    action:
      - service: button.press
        target:
          entity_id: button.fermax_abrir_puerta_principal
```

### Notificación si el dispositivo se desconecta

```yaml
automation:
  - alias: "Notificar desconexión Fermax"
    trigger:
      - platform: state
        entity_id: binary_sensor.fermax_connected
        to: "off"
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          title: "Fermax Desconectado"
          message: "El videoportero Fermax se ha desconectado"
```

### Abrir puerta con comando de voz

```yaml
intent_script:
  AbrirPuerta:
    speech:
      text: "Abriendo la puerta"
    action:
      - service: button.press
        target:
          entity_id: button.fermax_abrir_puerta_principal
```

## Debugging

Para habilitar logs detallados, añade esto a tu `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.fermax_cloud: debug
```

Los logs mostrarán:
- Llamadas a la API (sin exponer tokens)
- Renovación de tokens
- Descubrimiento de dispositivos
- Errores y reintentos

## Troubleshooting

### Error de autenticación

Si recibes errores de autenticación:
1. Verifica que tu email y contraseña son correctos
2. Intenta iniciar sesión en la app móvil de Fermax Blue
3. Si funciona en la app, reconfigura la integración en Home Assistant

### Dispositivos no aparecen

Si tus dispositivos no aparecen:
1. Verifica que están emparejados en la app móvil de Fermax Blue
2. Revisa los logs con nivel DEBUG
3. Recarga la integración

### Puerta no se abre

Si el botón no abre la puerta:
1. Verifica que el dispositivo está conectado (sensor de conexión)
2. Prueba abrir la puerta desde la app móvil
3. Revisa los logs para ver errores específicos

### Token expirado

La integración renueva automáticamente los tokens. Si ves errores de token:
1. La integración intentará renovar automáticamente
2. Si persiste, puede que necesites reautenticarte
3. Ve a la integración y sigue el flujo de reautenticación

## Compatibilidad

### Requisitos
- Home Assistant 2023.1 o superior
- Dispositivos Fermax compatibles con Fermax Cloud (Blue)
- Cuenta activa en Fermax Cloud

### Dispositivos Probados

Esta tabla muestra los dispositivos que han sido probados por la comunidad. Si tienes un dispositivo Fermax y funciona (o no funciona) con esta integración, por favor abre un issue o PR para actualizar esta tabla.

| Modelo | Tipo | Conexión | Estado | Probado por | Notas |
|--------|------|----------|--------|-------------|-------|
| VEO-XS | Monitor | WiFi | ✅ Funciona | @piKolin | Todas las funciones operativas |

**Leyenda:**
- ✅ Funciona: Totalmente operativo
- ⚠️ Parcial: Funciona con limitaciones
- ❌ No funciona: No compatible
- ❓ Sin probar: Nadie lo ha probado aún

**¿Tienes otro modelo?** 
Si tienes un dispositivo Fermax diferente:
1. Prueba la integración
2. Abre un [issue](https://github.com/piKolin/homeassistant-fermax_cloud/issues/new) indicando:
   - Modelo exacto del dispositivo
   - Tipo (Monitor, Panel, etc.)
   - Tipo de conexión (WiFi, 4G, etc.)
   - Qué funciona y qué no
3. Actualizaremos esta tabla

### Dispositivos Potencialmente Compatible

Según la documentación de Fermax, estos dispositivos deberían ser compatibles (sin confirmar):

- VEO-XS (4G)
- VEO Duox Plus
- SMILE
- LYNX
- Otros monitores con soporte Fermax Cloud/Blue

Si pruebas alguno de estos, ¡háznoslo saber!

## 🤝 Contribuir

¡Las contribuciones son bienvenidas!

### Formas de Contribuir

- �  **Reportar compatibilidad de dispositivos** (¡muy importante!)
  - Si tienes un dispositivo Fermax diferente al VEO-XS WiFi
  - Abre un issue con el título: `[Compatibilidad] Tu Modelo`
  - Incluye: modelo, tipo, conexión, qué funciona y qué no
  - Ayudarás a otros usuarios a saber si la integración funciona con su dispositivo
  
- 🐛 **Reportar bugs**
  - Incluye versión de HA, modelo de dispositivo y logs DEBUG
  
- 💡 **Sugerir nuevas funcionalidades**
  - Describe el caso de uso y beneficio
  
- 📝 **Mejorar la documentación**
  - Correcciones, aclaraciones, ejemplos adicionales
  
- 🔧 **Enviar pull requests**
  - Código, tests, documentación
  
- ⭐ **Dar una estrella al proyecto**
  - Ayuda a que más gente lo encuentre
  
- 📢 **Compartir con otros usuarios de Fermax**
  - Foros, grupos de Telegram, comunidades de Home Assistant

## 📜 Licencia

Este proyecto está bajo licencia MIT. Ver archivo [LICENSE](LICENSE) para más detalles.

## Seguridad y Privacidad

### ⚠️ Credenciales OAuth - Información Importante

Esta integración utiliza las credenciales OAuth del cliente extraídas de la aplicación móvil oficial Fermax Blue. **Esto es seguro y normal**:

- ✅ **Tus datos están protegidos**: Tu email y contraseña permanecen seguros en Home Assistant
- ✅ **Comunicación encriptada**: Todo el tráfico usa HTTPS
- ✅ **Sin terceros**: Solo se comunica con servidores oficiales de Fermax
- ✅ **Código auditable**: Es open source, puedes verificar que no hace nada malicioso

Las credenciales del cliente OAuth son:
- **Públicas**: Están en la app móvil que cualquiera puede descargar
- **Compartidas**: Todos los usuarios de la app usan las mismas
- **Necesarias**: Sin ellas no es posible autenticarse con Fermax Cloud

## Disclaimer

Este proyecto no está afiliado, asociado, autorizado, respaldado por, o de ninguna manera oficialmente conectado con Fermax, o cualquiera de sus subsidiarias o afiliados.

**Uso bajo tu propio riesgo**: Esta integración utiliza ingeniería inversa de la API de Fermax Cloud. Aunque funciona correctamente, Fermax podría cambiar su API en cualquier momento sin previo aviso.

## Soporte

Si encuentras algún problema o tienes sugerencias:
- Abre un issue en GitHub
- Proporciona logs con nivel DEBUG
- Describe los pasos para reproducir el problema

## Changelog

### 1.0.0 (2025-01-10)
- Versión inicial
- Soporte para apertura de puertas
- Sensores de estado y conexión
- Configuración mediante UI
- Gestión automática de tokens
- Compatible con HACS
- Documentación
