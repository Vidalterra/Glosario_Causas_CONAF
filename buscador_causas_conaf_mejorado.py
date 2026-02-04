import streamlit as st
import pandas as pd
import re
import base64
import os
from html import escape

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Clasificador de Causas – CONAF",
    page_icon="🌲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES Y DATOS
# ═══════════════════════════════════════════════════════════════════════════════

# Columnas del CSV
COL_CODIGO_ESP = "Código especifico"
COL_CODIGO_GEN = "Código general"
COL_CAUSA_GEN = "Causa general"
COL_GRUPO = "Grupo de causa"
COL_CAUSA = "Causa"

# Glosarios
GLOSARIO_GRUPOS = {
    "Grupo 1 - Accidentales": "Agrupan aquellos incendios generados por un suceso eventual, inesperado e impredecible, generado al emplear fuentes de calor.",
    "Grupo 2 - Intencionales": "Acciones antrópicas deliberadas que derivan en un incendio forestal al aplicar una fuente de calor a la vegetación con el fin de lograr un efecto determinado.",
    "Grupo 3 - Naturales": "Incendios forestales generados sin la intervención antrópica, donde actúan las condiciones propias del medio natural.",
    "Grupo 4 - Negligentes": "Incendios forestales generados por falta de cuidado, malas prácticas, omisión o desconocimiento de la normativa vigente.",
    "Grupo 5 - Indeterminadas": "Son aquellos incendios forestales que tienen causa indeterminada, es decir que se investigan, pero no es posible establecer la causa origen o bien no fue posible investigar.",
}

GLOSARIO_CAUSAS_GENERALES = {
    "1.1": ("Faenas forestales", "Actividades asociadas a la producción forestal a micro o macro escala. Considera trabajos de eliminación de desechos vegetales, manejo de plantaciones y uso de maquinaria y herramientas. Se consideran dentro de esta categoría incendios en terrenos de aptitud preferentemente forestal y los predios particulares con especies forestales nativas o exóticas."),
    "1.2": ("Faenas agrícolas y pecuarias", "Actividades asociadas a la producción agrícola y pecuaria a micro o macro escala. Considera eliminación de desechos vegetales, manejo de cultivos y uso de maquinaria y herramientas. Se incluyen los incendios en terrenos de aptitud agrícola."),
    "1.3": ("Actividades al aire libre", "Actividades asociadas al empleo de fuentes de calor en actividades de entretención al aire libre en áreas habilitadas como camping, caminatas, actividades de pesca, caza u otras."),
    "1.4": ("Vías férreas", "Actividades o eventos asociadas al desplazamiento, funcionamiento o mantención del sistema ferroviario."),
    "1.5": ("Actividades de control y extinción de incendios forestales", "Clasificación que incluye accidentes de aeronaves en combate de incendio forestal, reconocimiento de zonas y el uso de herramientas en actividades de extinción."),
    "1.6": ("Parcelaciones, edificaciones residenciales, industriales u otras", "Las parcelaciones son subdivisiones del terreno rural, destinadas para el desarrollo inmobiliario, cultivos u otros fines. Las edificaciones residenciales corresponden a viviendas, habitadas por personas o familias. Las edificaciones industriales son los que albergan actividad económica y/o productiva."),
    "1.7": ("Originados por desplazamiento de personas, vehículos o aeronaves", "Incendio forestal generado por desplazamiento de personas a través de diversos medios de transportes, terrestre o aéreo."),
    "1.8": ("Otras quemas", "Otras quemas distintas a lo dispuesto en el DS 276, así como también, la quema avisada para limpieza de canales, cercas u otros."),
    "1.9": ("Líneas eléctricas", "Situaciones asociadas a los tendidos eléctricos de baja, media o alta tensión. Incluye todo tipo de estructura asociada tales como postación, transformador, otros. Esta causa general hace referencia a que es total y exclusiva responsabilidad de las empresas eléctricas el correcto funcionamiento, instalación y mantenimiento de la vegetación circundante."),
    "1.10": ("Otras causas", "Actividades o acciones particulares que no están asociados a las causas generales anteriores o que no se encuentran dentro del sistema de clasificación de causas."),
    "2.1": ("Incendios Intencionales", "Incendios forestales provocados de manera premeditada y directa con diversas motivaciones: conflictos personales, venganza, ataques incendiarios, conflictos territoriales, obtención de beneficios económicos, observación de operaciones de combate, encubrimiento de delitos, extracción de productos del bosque, o cambio irregular de uso del suelo."),
    "3.1": ("Incendios naturales", "Incendios forestales generados por fenómenos naturales como caída de rayo, actividad volcánica u otras causas naturales sin intervención humana."),
    "4.1": ("Faenas forestales", "Incendios forestales generados por negligencia en actividades forestales: quemas no avisadas o mal ejecutadas, incendio de maquinaria por falta de mantención, contacto con conductor eléctrico, partículas incandescentes, rebrotes de quemas, empleo inadecuado de fuentes de calor en campamentos forestales."),
    "4.2": ("Faenas agrícolas y pecuarias", "Incendios forestales generados por negligencia en actividades agrícolas y pecuarias: quemas no avisadas o mal ejecutadas, incendio de maquinaria por falta de mantención, contacto con conductor eléctrico, partículas incandescentes, rebrotes de quemas, empleo inadecuado de fuentes de calor en faenas agropecuarias."),
    "4.3": ("Actividades al aire libre", "Incendios forestales generados por el empleo de fuentes de calor por personas que realizan actividades recreativas en sectores no habilitados para el uso del fuego, tales como excursiones, camping, caza, pesca u otras."),
    "4.4": ("Vías férreas", "Causas negligentes asociadas al sistema ferroviario, incluyendo partículas incandescentes por falta de mantención de fajas de seguridad, uso de fuentes de calor en mantención y contacto o corte de conductor eléctrico de línea férrea."),
    "4.5": ("Actividades de control y extinción de incendios forestales", "Causas negligentes en operaciones de control y extinción, como rebrote de incendio declarado extinto por trabajo deficiente, o generado por uso de equipos durante operaciones de control."),
    "4.6": ("Parcelaciones, edificaciones residenciales, industriales u otras", "Causas negligentes asociadas a parcelaciones y edificaciones en zonas rurales o de interfaz, incluyendo uso de equipos de construcción, conexiones eléctricas irregulares, infraestructura de energía, chimeneas y desecho de cenizas."),
    "4.7": ("Originados por desplazamiento de personas, vehículos o aeronaves", "Causas negligentes por desplazamiento, como empleo de fuentes de calor en actividades religiosas o de peregrinación, y señalización en rutas o faenas de mantención."),
    "4.8": ("Otras quemas", "Causas negligentes por quemas no avisadas para limpieza, quema de basura residencial, desechos industriales, eliminación de fauna y uso de fuentes de calor en vertederos o basurales."),
    "4.9": ("Tendido eléctrico", "Causas negligentes asociadas al tendido eléctrico, como combustión por contacto con la vegetación, corte de conductor por caída de rama o fatiga de estructura, sobrecalentamiento de transformadores y otros elementos del sistema eléctrico."),
    "4.10": ("Otras causas", "Causas negligentes que no encaben en las anteriores: maniobras militares, faenas mineras, explosiones, fumar, menores de edad con fuente de calor, fuegos artificiales, elaboración de ladrillos, combustión espontánea y personas en situación de calle."),
    "4.11": ("Producción y/o extracción de productos y/o derivados del bosque", "Causas negligentes en actividades de producción forestal no industriales, como elaboración de carbón vegetal, extracción de hongos y frutos, confección de leña y actividades de apicultura."),
    "5.1": ("Incendios de causa indeterminada", "Incendios forestales donde, tras la investigación, no es posible establecer la causa origen, bien sea por área de inicio alterada, hipótesis sin validación o imposibilidad de llegar al área de inicio por dificultades geográficas."),
}

GLOSARIO_CAUSAS_ESPECIFICAS = {
    # GRUPO 1 - ACCIDENTALES
    "1.1.1": "Quema controlada avisada que se escapa al control y se propaga fuera del área circunscrita para su ejecución, aun cumpliendo con todo lo descrito en el aviso o plan de quema.",
    "1.1.2": "Partículas incandescentes o chispas originadas entre la fricción de maquinaria o herramientas forestales con rocas, cercos u otro material metálico en faenas forestales de explotación de bosques, fajas o casillas mecanizadas o subsolado.",
    "1.1.3": "Accidente o acción en faenas forestales no clasificada anteriormente. Se debe detallar en el informe de investigación la descripción de la causa que no fue clasificada, esto para futuras actualizaciones del sistema de clasificación de causas de incendios forestales.",
    "1.2.1": "Quema controlada avisada que se escapa al control y se propaga fuera del área circunscrita para su ejecución, aun cumpliendo con todo lo descrito en el aviso o plan de quema. Se considera también el manejo de praderas dentro de esta causa.",
    "1.2.2": "Partículas incandescentes o chispas originadas entre la fricción de maquinaria o herramientas agrícolas con rocas, cercos u otro material empleadas en faenas agrícolas o pecuarias.",
    "1.2.3": "Accidente o acción en faenas agropecuarias no clasificada anteriormente. Se debe detallar en el informe de investigación la descripción de la causa que no fue clasificada, esto para futuras actualizaciones del sistema de clasificación de causas de incendios forestales.",
    "1.3.1": "Actividades recreativas en sectores habilitados para el empleo de fuentes de calor con fines de calefacción, cocinar, iluminación, u otros usos. Entre las actividades recreativas se encuentran: excursionistas, paseantes, trekking, senderismo, actividades de caza, actividades de pesca, camping, otras.",
    "1.4.1": "Accidente ferroviario que genera el incendio del tren (u otro vehículo) y éste por transmisión de calor o emisión de partículas incandescentes origina un incendio forestal.",
    "1.4.2": "Partículas incandescentes generadas por el roce de las ruedas metálicas con los rieles del tren o vehículo ferroviario, que producen un incendio forestal, aun manteniendo una faja de seguridad libre de vegetación.",
    "1.5.1": "Caída de cualquier tipo de aeronave, completa o parcialmente, tripulada o no, que esté realizando operaciones de control, coordinación, supervisión o reconocimiento del incendio forestal que, producto del impacto con la superficie, provoca un incendio que se propaga a través de la vegetación circundante.",
    "1.6.1": "Fuego de una estructura en llamas que, al estar cercano a vegetación, y que presenta continuidad horizontal y/o vertical, se transmite a ella y origina un incendio forestal.",
    "1.7.1": "Accidente vehicular que involucra colisiones o choques, genera el incendio del propio vehículo, el cual se propaga a través de la vegetación. Se considera también el contacto de algún elemento del vehículo que se encuentra a altas temperaturas con la vegetación, genera material incandescente y afecta a la vegetación circundante.",
    "1.7.2": "Caída de cualquier tipo de aeronave, completa o parcialmente, tripulada o no, que esté realizando cualquier labor DISTINTA o sin ninguna relación con incendios forestales, donde el impacto provoca un incendio que se propaga a la vegetación circundante.",
    "1.7.3": "Partículas incandescentes emitidas a través del escape del vehículo o por el roce entre un artefacto del vehículo con algún elemento de la vía, que encienden la vegetación cercana. Se incluyen en esta categoría los incendios provocados por vehículos de limpieza y/o mantención de caminos (asfaltados o de tierra).",
    "1.8.1": "Uso del fuego autorizado, como quema controlada para eliminar vegetación en caminos, canales, cercos o cunetas. Se considera esta causa distinta a faenas forestales y agrícola debido a que personas particulares utilizan este tipo de quema para limpiar predios particulares, los que no tienen ninguna faena asociada.",
    "1.9.1": "Arco y material incandescente que cae sobre la vegetación, como producto del contacto de fauna con el tendido eléctrico.",
    "1.9.2": "Se entiende por material desprendido al material vegetal o no vegetal que fue separado de su lugar de origen y desplazado por la acción del viento y que entra en contacto con el tendido eléctrico, generando un arco eléctrico y/o material incandescente, que cae hacia la vegetación y origina un incendio forestal.",
    "1.9.3": "Accidente eléctrico no clasificado anteriormente. Se debe detallar en el informe de investigación la descripción de la causa que no fue clasificada, esto para futuras actualizaciones del sistema de clasificación de causas de incendios forestales.",
    "1.10.1": "Cualquier causa accidental que no se enmarque en las nueve causas generales antes descritas. Se debe detallar en el informe de investigación la descripción de la causa que no fue clasificada, esto para futuras actualizaciones del sistema de clasificación de causas de incendios forestales.",
    # GRUPO 2 - INTENCIONALES
    "2.1.1": "Incendios forestales intencionales que no están incorporados en el sistema de clasificación o donde no se logre determinar la motivación. Se debe detallar en el informe de investigación por qué se ha escogido esta causa, aludiendo a que se cuenta con pruebas o indicios de intencionalidad del incendio forestal.",
    "2.1.2": "Acción originada en un conflicto territorial, familiar, pasional o de otro tipo entre personas, donde una de ellas enciende la vegetación del entorno como venganza o para lograr un fin determinado.",
    "2.1.3": "Uso premeditado de fuentes de calor para incendiar y destruir con un fin determinado, dirigido hacia bienes muebles (vehículos, maquinaria, otros) como inmuebles (terrenos, infraestructura, otros). Se utilizan fuentes de calor como arma de destrucción, dando origen a un incendio forestal.",
    "2.1.4": "Empleo del fuego como herramienta para provocar un incendio forestal por conflicto territorial o patrimonial, con el fin de modificar los límites o deslindes de una propiedad.",
    "2.1.5": "Uso de fuentes de calor para incendiar terrenos con el objetivo de despejar la vegetación que rodea los productos de interés, como por ejemplo árboles y sus huellas de extracción (madereo), para el retiro y/o sustracción de los productos, tales como: varas, metros ruma, robo de madera o leña, otros. Indicar siempre cual fue el beneficio económico establecido.",
    "2.1.6": "Intención premeditada de provocar un incendio forestal para observar las operaciones terrestres y aéreas de combate y extinción por parte de CONAF, bomberos o empresas forestales.",
    "2.1.7": "Incendio provocado en forma deliberada para encubrir delitos o faltas, como por ejemplo eliminación de plantaciones de Cannabis sp. (marihuana), u otros.",
    "2.1.8": "Uso de fuentes de calor para incendiar un terreno y eliminar la vegetación con el fin de habilitar caminos para el paso de personas para extraer productos del bosque. Así como también, para favorecer el crecimiento de hongos (ejemplo, Morchella sp.) u otros frutos.",
    "2.1.9": "Uso ilegal de fuentes de calor para eliminar la vegetación de un terreno público o privado, que se requiere limpiar para un posterior loteo, venta o construcción de viviendas u otras instalaciones, cambio de uso del suelo, entre otros. Al determinar esta causa es necesario que en el mediano o largo plazo se realice un análisis en el sitio del suceso para establecer la veracidad del cambio de uso.",
    # GRUPO 3 - NATURALES
    "3.1.1": "Incendio forestal generado por el impacto directo de un rayo en un árbol o en un área con vegetación, donde el calor extremo generado por la descarga eléctrica encendió la vegetación y se propagó a través de ella.",
    "3.1.2": "Incendio forestal generado por la expulsión de lava, cenizas o piroclastos que transmiten calor a la vegetación circundante, produciendo la ignición de materiales combustibles.",
    "3.1.3": "Considera las causas naturales no incluidas en el sistema de clasificación. Se debe detallar en el informe de investigación la descripción de la causa que no fue clasificada, esto para futuras actualizaciones.",
    # GRUPO 4 - NEGLIGENTES
    "4.1.1": "Incendio forestal generado por el empleo del fuego para eliminar desechos forestales en contravención a lo establecido en el D.S 276 o sin avisar a CONAF.",
    "4.1.2": "Incendio forestal generado por falta de mantención y que se propaga por la vegetación produciendo un incendio forestal. Se entiende por maquinaria forestal, a todas aquellas máquinas, motrices u operadoras, que se utilizan en este tipo de faenas.",
    "4.1.3": "Incendio forestal que se produce por el contacto o corte del conductor eléctrico, ocasionado por la caída de rama, de un árbol o por una maquinaria forestal, producido en una faena de explotación forestal en predios forestales y/o particulares tales como volteo de árbol, poda, producto de maquinaria, otros.",
    "4.1.4": "Incendio forestal generado por herramientas alteradas o con desperfectos (motosierra u otros), mala utilización o su uso en condiciones de riesgo de incendio forestal tales como horarios de altas temperaturas o alertas preventivas. Además, incluye el desplazamiento de vehículos en faena forestal que puedan emitir partículas incandescentes desde el tubo de escape u otro tipo de desperfecto.",
    "4.1.5": "Incendio forestal generado por el rebrote de una quema no avisada, en terrenos forestales o de aptitud preferentemente forestal.",
    "4.1.6": "Se entenderá por 'quema mal ejecutada' aquella quema avisada que no cumple con lo estipulado en el plan de quema y/o aviso de quema presentado ante CONAF. Entre ellas se considera no contar con el número de personas, quema realizada fuera de la superficie mencionada, no disponer de medidas de prevención como extintores, agua a disposición u otros, horarios distintos a lo informado, entre otras. Se incluye además la causa 'rebrote de quema avisada mal ejecutada', puesto que no se realizó una liquidación de la quema de forma efectiva.",
    "4.1.7": "Incendio forestal que se produce al emplear fuentes de calor en una faena de explotación forestal en predios forestales y/o particulares con la finalidad de calefacción, alimentación, entre otros.",
    "4.1.8": "Considera las causas negligentes en faenas forestales no incluidas en el sistema de clasificación. Se debe detallar en el informe de investigación la descripción de la causa que no fue clasificada, esto para futuras actualizaciones del sistema de clasificación de causas de incendios forestales.",
    "4.2.1": "Incendio forestal generado por el empleo del fuego para eliminar desechos agrícolas en contravención a lo establecido en el D.S 276 o sin avisar a CONAF.",
    "4.2.2": "Incendio de maquinaria en faena agrícola generado por falta de mantención, que se propaga por la vegetación generando un incendio forestal. Se entiende por maquinaria agrícola, a todas aquellas máquinas, motrices u operadoras, que se utilizan para usos agrícolas. A esta categoría pertenecen los tractores, cosechadoras, equipos forrajeros, labranza, desmalezadoras, pulverizadoras.",
    "4.2.3": "Incendio forestal que se produce por el contacto o corte del conductor eléctrico por la caída de rama, de un árbol o una maquinaria agrícola, generado en faenas agrícolas y pecuarias.",
    "4.2.4": "Incendio forestal generado por herramientas alteradas o con desperfectos, mala utilización o su uso en condiciones de riesgo de incendio forestales tales como horarios de altas temperaturas o alertas preventivas en faenas agrícolas. Además, incluye el desplazamiento de vehículos en faena forestal que puedan emitir partículas incandescentes desde el tubo de escape u otro tipo de desperfecto.",
    "4.2.5": "Incendio forestal generado por el rebrote de una quema no avisada, en terrenos agrícolas.",
    "4.2.6": "Se entenderá por 'mal ejecutada' aquella quema avisada en la que no se cumple con lo estipulado en el plan de quema y/o aviso de quema presentado ante CONAF. Entre ellas se considera: no contar con el número de personas, quema realizada fuera de la superficie mencionada, no tener medidas de prevención como extintores y/o agua a disposición, entre otras. Se incluye además la causa 'rebrote de quema avisada mal ejecutada', puesto que no se realizó una liquidación de la quema de forma efectiva.",
    "4.2.7": "Incendio forestal que se produce por la acción de emplear fuentes de calor dentro del predio en faena agrícola o pecuaria, con la finalidad de calefacción, alimentación, iluminación, entre otros.",
    "4.2.8": "Considera las causas negligentes en faenas agrícolas y pecuarias no incluidas en el sistema de clasificación. Se debe detallar en el informe de investigación la descripción de la causa que no fue clasificada, esto para futuras actualizaciones del sistema de clasificación de causas de incendios forestales.",
    "4.3.1": "Considera incendios forestales generados por el empleo de fuentes de calor por personas que realizan actividades recreativas en sectores no habilitados para el uso del fuego. Entre las actividades recreativas se encuentran: excursiones, caminatas, paseos, trekking, senderismo, actividades de caza, actividades de pesca, camping, otras. Se incluye, además, el empleo de fuego en actividades de caza, con objetivos distintos a la alimentación, calefacción o iluminación, tales como: la quema de madrigueras para la salida de conejos, liebres u otros animales, partículas incandescentes generado por la acción de disparar, entre otros.",
    "4.4.1": "Incendio forestal generado por partículas incandescentes desprendidas por el roce de las ruedas metálicas con los rieles del tren o vehículo ferroviario, que producen un incendio forestal, cuando la vía férrea no tiene una faja de seguridad.",
    "4.4.2": "Incendio forestal generado por el empleo de fuentes de calor en faenas de mantención o reparación de la vía férrea por parte de los operarios.",
    "4.4.3": "Contacto o corte del conductor eléctrico del tendido de la vía férrea que genera partículas incandescentes, que en contacto con el suelo puede producir la ignición de la vegetación colindante, produciendo un incendio forestal.",
    "4.5.1": "Se refiere a un incendio forestal que fue declarado extinto, el cual se reactiva, cruza la línea de control, y reinicia su propagación. Lo anterior debido a un trabajo deficiente previo. Si se abre una nueva ficha de incendio, esta debe ser la causa, en cambio si la ficha es la del incendio anterior, se debe mantener la causa de origen.",
    "4.5.2": "Incendio forestal que fue generado por el uso de equipos o herramientas durante las operaciones de control de un incendio forestal.",
    "4.6.1": "Incendio forestal originado por actividades humanas ligadas a la construcción, limpieza de terreno o montaje de estructuras en áreas de parcelaciones, edificaciones residenciales, industriales u otras. Entre las maquinarias o herramientas se encuentran los equipos de soldadura, herramientas de corte, partículas incandescentes generada por equipos eléctricos, entre otras. Se incluye los incendios eléctricos ocasionados por motobombas/ bombas extractoras de agua.",
    "4.6.2": "Las conexiones eléctricas irregulares involucran conexiones deficientes, cables defectuosos, sobrecargas, cortocircuitos, entre otros fallos eléctricos, lo que genera calor excesivo, partículas incandescentes o arcos eléctricos que pueden afectar a la vegetación circundante y generar un incendio forestal.",
    "4.6.3": "La infraestructura destinada a la producción de energía considera la instalación y operación de éstas. El mal funcionamiento, mantenimiento y operación inadecuada puede generar sobrecalentamiento de los sistemas y/o generar partículas incandescentes, generando la ignición de material vegetal circundante, lo que produce un incendio forestal.",
    "4.6.4": "Expulsión de material en combustión desde chimeneas, cocina a leña u otro artefacto, y que es desplazado por el viento hacia zonas de vegetación o cualquier material inflamable, originando un incendio forestal. Se considera dentro de estas categorías la expulsión de material en combustión por hornos, hornillos, cocinillas u otras fuentes de calor utilizadas con fines de alimentación.",
    "4.6.5": "Incendio forestal ocasionado por la falta de precaución al realizar actividades al aire libre, relacionadas a las parcelaciones, entre ellas, celebración por la adquisición del sitio, inauguración o festejo por el término de obras gruesas de construcción, entre otras.",
    "4.6.6": "Los desechos de cenizas provenientes de chimenea, calefacción, cocina a leña, tinajas, u otros artefactos, son depositadas en áreas adyacentes a la vegetación, acopios de basura u otro material inflamable, originando un incendio forestal.",
    "4.7.1": "Se refiere al empleo de fuentes de calor en actividades religiosas como peregrinación o veneración de animitas, el que se puede desarrollar en una capilla, ermita, santuario, templete u otros, que da origen a un incendio forestal. También se deben considerar las animitas a orilla de rutas o caminos.",
    "4.7.2": "Se señaliza con fuego en caso de: extravío en la montaña o paraje, señalización de detención obligada en caminos locales, por accidente grave más adelante, por corte de camino, por caída de puente. También es utilizado por los arrieros en el periodo estival, que suben con sus animales a las veranadas de la cordillera, señalizando la ruta de desplazamiento y reportan su ubicación usando el fuego para comunicarse entre ellos. Faenas de mantención considerando: limpieza en caminos o sectores públicos o privados, cuando los trabajadores hacen campamentos durante la noche y usan fuentes de calor para iluminar/calefacción/alimentación/otros.",
    "4.8.1": "Incendio forestal generado por el empleo del fuego con fines de limpieza en canales, cunetas, cercos o caminos (en predios particulares o rústicos), en contravención a lo establecido en el artículo anterior y/o sin avisar a CONAF. Considera la quema de vegetación para la habilitación de caminos o senderos, la quema de pastizales u otros similares con fines de limpieza en terreno o la quema de especies vegetales perjudiciales, viva o muerta.",
    "4.8.2": "Incendio forestal generado por el empleo de fuentes de calor en actividades de quema de basura residencial, basura proveniente de construcciones, quema de microbasurales o desechos vegetales tales como aserrín, biomasa, hojas u otros. Se excluye desechos forestales y/o agrícolas, los que deben ser categorizados según su causa general (4.1 o 4.2, respectivamente). No considera instalaciones autorizadas de vertederos y/o basurales ni desechos industriales.",
    "4.8.3": "Empleo de fuentes de calor para eliminar desechos industriales como cartones, cartulinas, bandejas de cartón, envases, baterías, envoltorio de fardos, entre otros.",
    "4.8.4": "Incendio forestal producto del empleo de fuentes de calor para la eliminación de fauna no deseada, viva o muerta, entre los que se consideran roedores, reptiles, avispas, otros.",
    "4.8.5": "Empleo de fuentes de calor en vertederos o basurales.",
    "4.9.1": "La vegetación que se encuentra bajo, sobre o al costado del tendido eléctrico entra en contacto con él, generando partículas incandescentes que caen sobre la vegetación circundante, generando un incendio forestal. Se considera la caída de ramas o árboles sobre el tendido eléctrico sin provocar el corte de cable, pero que su contacto genera la producción de partículas incandescentes.",
    "4.9.2": "Incendio forestal que se genera por el corte del conductor eléctrico producto de la caída de rama o de un árbol.",
    "4.9.3": "Incendio forestal que se genera por el corte del conductor eléctrico por fatiga del mismo material (sin intervención de otro componente) o por la caída de algún elemento del tendido eléctrico como la postación, generándose partículas incandescentes que, al tener contacto con vegetación circundante, se prende y se propaga.",
    "4.9.4": "El sobrecalentamiento de estructuras asociados al sistema eléctrico puede generar material incandescente o explosión de los equipos, el cual entra en contacto con el material vegetal circundante y generar un incendio forestal. Se incluyen en esta categoría los cortocircuitos de cualquier elemento del sistema eléctrico, la sobrecarga del sistema, explosiones de las estructuras, derretimiento de algún componente, desperfectos eléctricos, entre otros.",
    "4.9.5": "Considera las causas negligentes asociadas al tendido eléctrico que no se encuentran en el sistema de clasificación. Se debe detallar en el informe la descripción de la causa que no fue clasificada, esto para futuras actualizaciones.",
    "4.10.1": "Incendios forestales generados durante maniobras militares, tales como actividades en campo de entrenamiento, campos de tiro, explosiones de artefactos, u otras actividades. Las maniobras policiales hacen referencia cuando deben efectuar acciones para disuadir enfrentamientos, tales como el uso de bombas lacrimógenas u otros. Para futura actualización de causas, se consideran dentro de esta categoría las manifestaciones y todo lo relacionado a ella, que origina un incendio forestal.",
    "4.10.2": "Faenas mineras manuales o mecanizadas que debido a su operación generan un incendio forestal.",
    "4.10.3": "Explosión de oleoducto, polvorín, depósito de combustible u otro no clasificado, que genera un incendio forestal.",
    "4.10.4": "Incendio forestal asociado a la acción de fumar, tales como cigarrillo, pitillo, colilla, fósforo, pipa, batería o cargadores de cigarrillos eléctricos u otros asociados, que inicia el incendio forestal. Para ello es necesario encontrar el medio de ignición y fijarlo fotográficamente.",
    "4.10.5": "Incendio forestal que se origina cuando menores de edad comienzan a experimentar o jugar con fósforos, encendedores u otras fuentes de calor.",
    "4.10.6": "Incendio forestal generado por la utilización de fuegos artificiales, artículos pirotécnicos, globos aerostáticos (globos de los deseos) y otros artefactos de similar naturaleza en actividades de celebración como año nuevo, eventos artísticos, u otros, lo que, una vez efectuado el lanzamiento, entran en contacto con áreas de vegetación.",
    "4.10.7": "Actividad asociada a la elaboración y/o cocción de ladrillos que, por falta de medidas preventivas, origina un incendio forestal.",
    "4.10.8": "Incendio forestal que se produce debido a la ignición espontánea en combustibles que se encuentran almacenados y/o acopiados, tales como fardos de pastos, acopios de aserrín o chips de madera, entre otros. Se considera negligente puesto que no se realizó el tratamiento respectivo.",
    "4.10.9": "Incendio forestal que se produce, de la ignición por combustión espontánea en vertederos, los cuales no cuentan con tratamientos y tampoco efectúan reciclaje de la basura que se deposita en sus instalaciones.",
    "4.10.10": "Empleo de fuentes de calor para eliminar recubrimiento de conductores eléctricos, donde las partículas incandescentes entran en contacto con la vegetación adyacente, originando un incendio forestal.",
    "4.10.11": "Empleo de fuentes de calor por personas en situación de calle, con fines de calefacción, alimentación, iluminación u otros.",
    "4.10.12": "Considera las causas negligentes que no se encuentran detalladas en el sistema de clasificación de causas. Se debe detallar en el informe la descripción de la causa que no fue clasificada, esto para futuras actualizaciones.",
    "4.11.1": "Incendio forestal generado por faenas de elaboración de carbón vegetal, proceso que puede utilizar hornos metálicos, de barro u otros. En la producción artesanal utiliza pilas de leña en una fosa de tierra, percha, rumba y mono, la madera se suele tapar con tierra, en donde se generan partículas incandescentes y que se propaga por la vegetación adyacente.",
    "4.11.2": "Empleo de fuentes de calor en faenas de extracción de productos del bosque, con fines de alimentación, calefacción, iluminación u otros fines. Distinto a lo expresado en la causa 2.1.5",
    "4.11.3": "Actividad asociada al proceso de limpieza, post producción de leña no industrial (distinto a la causa 2.1.4). Así como también, al empleo de fuentes de calor con fines de alimentación, calefacción, iluminación u otros usos.",
    "4.11.4": "Empleo de fuentes de calor en actividades de apicultura, con fines de alimentación, calefacción, iluminación u otros fines. Considera también el uso de ahumadores u otros.",
    # GRUPO 5 - INDETERMINADAS
    "5.1.1": "Categoría atingente cuando después de realizar el método de evidencias físicas y la prueba de personal, no es posible establecer la causa, esto puede darse por: área de inicio alterada, hipótesis sin validación, hipótesis múltiples u otros motivos.",
    "5.1.2": "Categoría atingente cuando el incendio no posee las características como para realizar una investigación, porque no se pudo llegar al área de inicio debido a dificultades geográficas o paso inhabilitado. Las UAD no deben utilizar esta causa en los informes.",
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES CACHEADAS Y HELPER
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_data():
    """Carga y procesa los datos del CSV con caché para optimizar performance."""
    try:
        df = pd.read_csv("causas_csv.csv", sep=";", encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].str.strip()
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar causas_csv.csv: {str(e)}")
        st.stop()

@st.cache_data
def get_unique_grupos(df):
    return sorted(df[COL_GRUPO].unique().tolist())

def get_grupo_class(grupo: str) -> str:
    grupo_map = {"1": "g1", "2": "g2", "3": "g3", "4": "g4"}
    return grupo_map.get(grupo[0] if grupo else "", "g5")

def sanitize_text(text: str) -> str:
    return escape(str(text))

def extract_codigo_general(codigo_esp: str) -> str:
    parts = str(codigo_esp).split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else codigo_esp

def filter_dataframe(df: pd.DataFrame, grupo_filter: str, search_query: str) -> pd.DataFrame:
    df_filtered = df.copy()
    if grupo_filter != "Todos":
        df_filtered = df_filtered[df_filtered[COL_GRUPO] == grupo_filter]
    if search_query.strip():
        tokens = search_query.strip().lower().split()
        search_index = df_filtered.astype(str).apply(lambda row: ' '.join(row.values).lower(), axis=1)
        mask = search_index.str.contains(tokens[0], na=False, regex=False)
        for token in tokens[1:]:
            mask &= search_index.str.contains(token, na=False, regex=False)
        df_filtered = df_filtered[mask]
    return df_filtered

def get_img_as_base64(file_path):
    """
    Lee un archivo de imagen (SVG/PNG) y retorna una cadena base64 lista para HTML.
    Esto permite usar imágenes locales en st.markdown sin problemas de rutas en deploy.
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

# ═══════════════════════════════════════════════════════════════════════════════
# CSS (DISEÑO FIEL MEJORADO)
# ═══════════════════════════════════════════════════════════════════════════════

def load_css():
    st.markdown("""
    <style>
    html, body, .stApp { font-family: 'Segoe UI', system-ui, sans-serif; }
    
    /* HEADER: Centrado perfecto usando Flexbox '1-2-1' */
    .app-header {
        background: linear-gradient(135deg, #F1F8F4 0%, #E3F1EA 100%);
        color: #fff; 
        padding: 1.2rem 2rem;
        border-radius: 0 0 16px 16px; 
        margin: -1rem -2rem 1.8rem;
        box-shadow: 0 4px 20px rgba(27,67,50,.35);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 20px;
    }
    
    .header-left {
        flex: 1; /* Ocupa 1 parte del espacio */
        display: flex;
        justify-content: flex-start;
    }
    
    .header-center {
        flex: 2; /* Ocupa el doble, centrado */
        text-align: center;
    }
    .header-center h1 { margin:0; font-size:1.75rem; font-weight:700; letter-spacing:-.3px; color: #1B4332 !important; }
    .header-center p { margin:.3rem 0 0; font-size:.88rem; opacity:.9; color: #2D6A4F; }

    .header-right {
        flex: 1; /* Ocupa 1 parte del espacio */
        display: flex;
        justify-content: flex-end;
    }

    .header-logo-img {
        height: 60px; /* Altura fija para uniformidad */
        width: auto;
        display: block;
    }
    
    @media (max-width: 768px) {
        .app-header { flex-direction: column; text-align: center; }
        .header-left, .header-center, .header-right { flex: auto; width: 100%; justify-content: center; }
        .header-center { margin: 15px 0; }
    }
    
    /* Badges */
    .badge-grupo {
        display:inline-block; border-radius:6px;
        padding:3px 10px; font-weight:600; font-size:.75rem; white-space:nowrap;
    }
    .badge-grupo.g1 { background:#fff3cd; color:#856404; border:1px solid #ffc107; }
    .badge-grupo.g2 { background:#f8d7da; color:#721c24; border:1px solid #f5c6cb; }
    .badge-grupo.g3 { background:#d1ecf1; color:#0c5460; border:1px solid #bee5eb; }
    .badge-grupo.g4 { background:#e2d9f3; color:#4a235a; border:1px solid #c9b1ff; }
    .badge-grupo.g5 { background:#e9ecef; color:#495057; border:1px solid #ced4da; }

    /* Interior Expander Unificado */
    .card-interior {
        background: #fdfdfd;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        overflow: hidden;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    
    .detalle-box {
        padding: 1.5rem;
        background: #ffffff;
        border-bottom: 1px solid #f1f3f5;
        color: #212529;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .detalle-title {
        color: #1B4332;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.8rem;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }

    .glosario-box {
        background: #f8fcf9;
        padding: 1.2rem 1.5rem;
        display: flex;
        gap: 20px;
        flex-wrap: wrap;
    }
    
    .glos-item { flex: 1; min-width: 250px; }
    .glos-label { font-size: 0.75rem; color: #2D6A4F; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }
    .glos-content { font-size: 0.85rem; color: #495057; line-height: 1.5; }

    /* Estilos Streamlit */
    div[data-testid="expander"] {
        border: none !important; box-shadow: none !important;
        background: transparent !important; margin-bottom: 8px !important;
    }
    div[data-testid="expander"] summary {
        padding: 12px 16px !important;
        background: #fff !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }
    div[data-testid="expander"] summary:hover {
        border-color: #2D6A4F !important;
        background: #f8fcf9 !important;
    }
    div[data-testid="expander"] > div:last-child > div > div {
        padding: 0 !important; margin: 0 !important;
    }
    
    /* Footer */
    .app-footer {
        text-align:center; padding: 2rem 0 1rem;
        font-size:.76rem; color:#adb5bd;
        border-top:1px solid #eee; margin-top:3rem;
    }
    .footer-img {
        max-width: 150px;
        height: auto;
        opacity: 0.8;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    load_css()
    df = load_data()
    
    if "grupo_pill" not in st.session_state:
        st.session_state.grupo_pill = "Todos"
    
    # --- HEADER CON LOGOS ---
    slogan_b64 = get_img_as_base64("slogan.svg")
    logo_b64 = get_img_as_base64("logo.svg")
    
    # Se generan las etiquetas img solo si la imagen cargó correctamente
    img_slogan = f'<img src="data:image/svg+xml;base64,{slogan_b64}" class="header-logo-img">' if slogan_b64 else ""
    img_logo = f'<img src="data:image/svg+xml;base64,{logo_b64}" class="header-logo-img">' if logo_b64 else ""

    st.markdown(f"""
    <div class="app-header">
        <div class="header-left">
            {img_logo}
        </div>
        <div class="header-center">
            <h1>🌲 Sistema de Clasificación de Incendios</h1>
            <p>Sistema de búsqueda y glosario oficial · CONAF</p>
        </div>
        <div class="header-right">
            {img_slogan}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- BUSCADOR ---
    query_input = st.text_input(
        label="Buscar",
        placeholder="🔍  Escribe una causa, código o palabra clave...",
        label_visibility="hidden",
        key="buscar_input",
    )
    
    # --- FILTROS ---
    grupos_opciones = ["Todos"] + get_unique_grupos(df)
    try:
        sel = st.pills("Filtrar por Grupo", options=grupos_opciones, selection_mode="single", default=st.session_state.grupo_pill, label_visibility="hidden")
        if sel is not None and sel != st.session_state.grupo_pill:
            st.session_state.grupo_pill = sel
            st.rerun()
    except AttributeError:
        cols = st.columns(len(grupos_opciones))
        for i, g in enumerate(grupos_opciones):
            if cols[i].button(g, key=f"btn_{g}", type="primary" if st.session_state.grupo_pill == g else "secondary"):
                st.session_state.grupo_pill = g
                st.rerun()
    
    # --- RESULTADOS ---
    df_filtered = filter_dataframe(df, st.session_state.grupo_pill, query_input)
    n_results = len(df_filtered)
    
    st.markdown(f'<div style="margin-bottom:10px; color:#666; font-size:0.9rem;">Resultados encontrados: <b>{n_results}</b></div>', unsafe_allow_html=True)
    
    if n_results == 0:
        st.info("No se encontraron resultados para tu búsqueda.")
    else:
        for _, row in df_filtered.iterrows():
            codigo_esp = str(row[COL_CODIGO_ESP])
            codigo_gen = extract_codigo_general(codigo_esp)
            grupo = str(row[COL_GRUPO])
            #causa_gen_txt = str(row[COL_CAUSA_GEN]) # Variable no usada en el display final simplificado
            causa_esp_txt = str(row[COL_CAUSA])
            g_class = get_grupo_class(grupo)
            
            # Limpieza de redundancia
            clean_desc = causa_esp_txt
            if clean_desc.startswith(str(codigo_esp)):
                clean_desc = re.sub(f"^{re.escape(codigo_esp)}[ .:-]*", "", clean_desc)
            
            expander_label = f"{codigo_esp} - {clean_desc.strip()}"
            
            with st.expander(label=expander_label, expanded=False):
                
                # Preparar variables para el HTML
                definicion_detalle = GLOSARIO_CAUSAS_ESPECIFICAS.get(codigo_esp, "Descripción detallada no disponible para este código.")
                grupo_def = GLOSARIO_GRUPOS.get(grupo, "")
                cg_titulo, cg_def = GLOSARIO_CAUSAS_GENERALES.get(codigo_gen, ("", ""))
                
                # HTML CARD INTERIOR - IMPORTANTE: unsafe_allow_html=True al final
                html_content = f"""
                <div class="card-interior">
                    <div class="detalle-box">
                        <div class="detalle-title">📋 Definición Técnica ({codigo_esp})</div>
                        {escape(definicion_detalle)}
                    </div>
                    <div class="glosario-box">
                        <div class="glos-item">
                            <div class="glos-label">Grupo de Causa</div>
                            <div class="glos-content">
                                <span class="badge-grupo {g_class}">{escape(grupo)}</span><br>
                                <span style="font-size:0.8rem; margin-top:4px; display:block;">{escape(grupo_def)}</span>
                            </div>
                        </div>
                        <div class="glos-item">
                            <div class="glos-label">Causa General ({codigo_gen})</div>
                            <div class="glos-content">
                                <strong>{escape(cg_titulo)}</strong><br>
                                {escape(cg_def)}
                            </div>
                        </div>
                    </div>
                </div>
                """
                
                # Renderizar
                st.markdown(html_content, unsafe_allow_html=True)

    # --- FOOTER ---
    footer_svg_b64 = get_img_as_base64("inferior.svg")
    img_footer = f'<img src="data:image/svg+xml;base64,{footer_svg_b64}" class="footer-img">' if footer_svg_b64 else ""
    
    st.markdown(f"""
    <div class="app-footer">
        <p>Sistema de Clasificación de Causas de Incendios Forestales · Chile 2026 · Glosario v1.5</p>
        <p>CONAF · Autor: Alumno en Práctica Francisco Vidal</p>
        {img_footer}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
