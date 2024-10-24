# DahuaEventsDMT

DahuaEventsDMT es una integración personalizada para Home Assistant utilizando AppDaemon. Esta integración captura eventos de detección de video inteligente (IVS) de las cámaras Dahua, como **CrossLineDetection** y **CrossRegionDetection**, y activa sensores binarios en Home Assistant para facilitar su monitoreo y control.

## Características

- Captura de eventos **CrossLineDetection** y **CrossRegionDetection** de cámaras Dahua.
- Activación automática de sensores binarios en Home Assistant.
- Configuración flexible para múltiples cámaras y tipos de eventos.
- Fácil instalación y personalización mediante AppDaemon.

## Requisitos

- [Home Assistant](https://www.home-assistant.io/)
- [AppDaemon](https://appdaemon.readthedocs.io/en/latest/)
- Cámaras Dahua compatibles con IVS.

## Instalación

### 1. Clonar el repositorio

Clona este repositorio en tu servidor Home Assistant:

```bash
git clone https://github.com/jaaneo/DahuaEventsDMT.git
