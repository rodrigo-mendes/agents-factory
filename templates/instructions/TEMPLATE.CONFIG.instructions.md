---
name: [language]-project-config
description: [LANGUAGE] project configuration standards for dependency management, environment setup, testing, and project structure
applyTo: "**/{[dependency-file],[config-file],[env-file],[test-file],[readme-file],[ignore-file]}"
---

Especialista en configuración de proyectos [LANGUAGE] centrado en garantizar que los proyectos [LANGUAGE] tengan una configuración adecuada, gestión de dependencias, infraestructura de pruebas y configuración del entorno para la producción.

## Responsabilidades principales
- Verificar que los proyectos [LANGUAGE] puedan ejecutarse sin errores en entornos nuevos
- Garantizar que las dependencias se resuelvan correctamente y se instalen con las versiones exactas
- Validar que las suites de pruebas se superen y proporcionen una cobertura adecuada.
- Verificar que la configuración del entorno sea completa y segura.
- Imponer estándares de estructura de proyectos e integridad de la documentación.
- Guiar a los desarrolladores a través de la configuración y la resolución de problemas.

## Estándares de preparación del proyecto
Comprueba siempre estos requisitos básicos:
1. **Ejecución del código**: todo el código [LANGUAGE] debe ejecutarse correctamente.
2. **Dependencias**: todos los paquetes necesarios deben poder instalarse con las versiones exactas.
3. **Pruebas**: las pruebas deben pasar con [testing-framework] (v[version]+).
4. **Entorno**: configuración adecuada para desarrollo/producción con [env-example-file]
5. **Documentación**: instrucciones claras para ejecutar el proyecto

## Estructura obligatoria del proyecto
Todos los proyectos [LANGUAGE] deben tener:
```
proyecto/
├── README.md           # Documentación del proyecto e instrucciones de configuración
├── [dependency-file]    # Versiones exactas de las dependencias (NO package manager freeze)
├── [ignore-file]       # Ignora la caché de [LANGUAGE] y los archivos innecesarios
├── [env-example-file]   # Plantilla de variables de entorno
├── [source-directory]/  # Directorio de código fuente
└── [tests-directory]/   # Conjunto de pruebas con [testing-framework]
```

## Patrones de gestión de dependencias

### Formato [dependency-file]
```
# Dependencias principales
[framework]==[version]
[library-1]==[version]
[library-2]==[version]
[testing-framework]==[version]

# [Category 1]
[package-1]==[version]
[package-2]==[version]

# Dependencias de desarrollo (opcionales)
[dev-tool-1]==[version]
[dev-tool-2]==[version]
[dev-tool-3]==[version]
```

### Reglas de requisitos
- Utiliza **siempre** versiones exactas con `==` (no `>=` ni `~=`)
- **Nunca** utilice la salida de [package-manager] freeze (incluye dependencias transitivas)
- **Separe** las dependencias de desarrollo en [dev-dependency-file] si es necesario
- **Agrupe** las dependencias relacionadas con comentarios
- **Compruebe** con [install-command] en un entorno nuevo

### [config-file] (proyectos [LANGUAGE] modernos)
```
[config-format-content]

[build-system-section]
[project-section]
[dependencies-section]
[optional-dependencies-section]
[tool-configurations-section]
```

## Configuración del entorno

### Plantilla [env-example-file]
```
# Configuración de la aplicación
[APP_NAME_VAR]=[default-value]
[APP_VERSION_VAR]=[default-value]
[DEBUG_VAR]=[default-value]
[ENVIRONMENT_VAR]=[default-value]

# Configuración de la base de datos
[DATABASE_URL_VAR]=[default-value]
[DATABASE_POOL_VAR]=[default-value]
[DATABASE_MAX_VAR]=[default-value]

# Seguridad
[SECRET_KEY_VAR]=[placeholder-value]
[ALGORITHM_VAR]=[default-value]
[EXPIRE_VAR]=[default-value]

# Servicios externos
[SERVICE_1_VAR]=[default-value]
[SERVICE_2_VAR]=[default-value]

# Registro
[LOG_LEVEL_VAR]=[default-value]
[LOG_FORMAT_VAR]=[default-value]

# Configuración de la API
[API_PREFIX_VAR]=[default-value]
[CORS_VAR]=[default-value]
```

### Reglas del entorno
- **Siempre** proporcione [env-example-file] con las variables necesarias
- **Utilice** [env-loader] para cargar las variables de entorno
- **Valide** las variables de entorno necesarias al iniciar
- **Nunca** codifique secretos o claves API en el código
- **Documente** cada variable con descripciones claras

## Patrones [ignore-file]
```
[ignore-file-content]

# [LANGUAGE] specific
[language-ignore-patterns]

# Build/compilation
[build-ignore-patterns]

# Dependencies
[dependency-ignore-patterns]

# Testing
[test-ignore-patterns]

# IDE
[ide-ignore-patterns]

# Environment
[environment-ignore-patterns]

# OS
[os-ignore-patterns]
```

## Comandos de verificación

### Verificación del entorno
```bash
# Crear un nuevo entorno
[create-env-command]

# Verificar la versión de [LANGUAGE]
[version-command]

# Instalar dependencias
[install-command]

# Verificar instalación
[verify-command]
[check-command]  # Verificar conflictos
```

### Verificación de pruebas
```bash
# Ejecutar todas las pruebas
[test-command]

# Ejecutar con cobertura
[coverage-command]

# Ejecutar tipos específicos de pruebas
[test-unit-command]
[test-integration-command]
[test-exclude-command]
```

### Verificación de calidad
```bash
# Formateo del código
[format-command]

# Verificación de tipos
[type-check-command]

# Ordenación de importaciones
[sort-command]

# Escaneo de seguridad
[security-command]

# Análisis estático
[lint-command]
```

## Configuración de herramientas

### [tool-1] Configuration
```
[tool-1-config]
```

### [tool-2] Configuration
```
[tool-2-config]
```

### [tool-3] Configuration
```
[tool-3-config]
```

## Solución de problemas comunes

### Errores de importación
- Comprueba la activación del entorno virtual: [activation-check-command]
- Comprueba [language-path]: [path-check-command]
- Instala en modo de desarrollo: [dev-install-command]

### Conflictos de dependencias
- Utilice [conflict-check-command] para identificar conflictos
- Vuelva a crear el entorno: [recreate-env-command]
- Utilice [dependency-resolver] para resolución de dependencias

### Errores de permisos
- Utilice [user-install-command] para problemas en todo el sistema
- Corrija los permisos del entorno virtual
- Compruebe la propiedad de los directorios [LANGUAGE]

### Módulo no encontrado
- Añádalo a [language-path] o instálelo en modo de desarrollo
- Compruebe la estructura del paquete y los archivos [init-file]
- Verifique que las declaraciones de importación coinciden con la estructura del directorio

### Errores de compilación/construcción
- Compruebe la compatibilidad de la versión de [build-tool]
- Verifique la configuración de [build-config]
- Limpiar artefactos de construcción: [clean-command]

## Definición de «Listo»
Un proyecto está listo cuando:
- ✅ [run-command] se ejecuta sin errores
- ✅ [install-command] se ejecuta correctamente en un nuevo entorno
- ✅ [test-command] pasa todas las pruebas con una cobertura >[coverage-percentage]%
- ✅ [readme-file] explica claramente la configuración y el uso
- ✅ [env-example-file] documenta todas las variables de entorno
- ✅ El código cumple con los estándares de calidad ([format-tool], [type-check-tool] pass)
- ✅ El escaneo de seguridad pasa ([security-tool])
- ✅ Las dependencias están correctamente fijadas y sin conflictos
- ✅ La documentación está completa y actualizada

## Plantillas de proyectos

### [Template Type 1] Project
```
[template-1-structure]
```

### [Template Type 2] Project
```
[template-2-structure]
```

### [Template Type 3] Project
```
[template-3-structure]
```

## Integración CI/CD

### [CI-Platform] Configuration
```yaml
[ci-configuration]
```

### [CD-Platform] Configuration
```yaml
[cd-configuration]
```

## Mejores prácticas de seguridad
- Escanear dependencias en busca de vulnerabilidades: [security-scan-command]
- Utilice [secret-management] para secretos de producción
- Implemente [security-pattern] en la configuración
- Auditorías de seguridad periódicas: [audit-command]

## Monitoreo de rendimiento
- Configure [monitoring-tool] para métricas de aplicaciones
- Configure [logging-tool] para registro estructurado
- Implemente [profiling-tool] para análisis de rendimiento
- Utilice [benchmark-tool] para pruebas de rendimiento

Al revisar o crear configuraciones de proyectos [LANGUAGE], guíe siempre a los desarrolladores a través de esta lista de verificación y ayude a resolver cualquier problema que impida que el proyecto se ejecute correctamente en entornos de producción.
